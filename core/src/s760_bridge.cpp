#include "s760/s760_bridge.hpp"

// =============================================================================
//  s760_bridge.cpp — in-process C++ UI bridge + optional loopback WS server.
//
//  WebSocket implementation / LICENSE NOTE:
//    The RFC6455 server below is a MINIMAL, SELF-CONTAINED implementation
//    written for this project. It depends only on the platform socket API
//    (Winsock2 on Windows, BSD sockets elsewhere) and the C++ standard library.
//    No third-party WebSocket library is vendored, so there is no additional
//    license obligation — the code is covered by this project's own license.
//    The handshake needs SHA-1 + Base64 (RFC6455 §4.2.2); both are implemented
//    inline here (public-domain-style, from the published algorithms) so no
//    crypto dependency is pulled in either.
//
//    The in-process API path (on_input / pump / callbacks) uses NONE of this
//    socket code and is the primary plugin transport.
// =============================================================================

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <functional>
#include <sstream>
#include <string>
#include <thread>
#include <atomic>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
using socket_t = SOCKET;
static constexpr socket_t INVALID_SOCK = INVALID_SOCKET;
#define CLOSESOCK closesocket
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
using socket_t = int;
static constexpr socket_t INVALID_SOCK = -1;
#define CLOSESOCK ::close
#endif

namespace s760 {
namespace {

// =============================================================================
//  Minimal JSON reader (just enough for S760ClientMessage).
//
//  Supports objects, strings (with the common escapes), numbers, booleans and
//  null, nested one level (the `payload` object). Not a general-purpose parser;
//  it exists so the in-process path has ZERO external dependencies. It is
//  tolerant of insignificant whitespace and ignores unknown keys (per protocol:
//  "Unknown fields are ignored").
// =============================================================================
class JsonReader {
public:
    explicit JsonReader(const std::string& s) : m_s(s), m_i(0) {}

    bool parse_object(std::function<bool(const std::string& key, JsonReader& val)> on_member) {
        skip_ws();
        if (!consume('{')) return false;
        skip_ws();
        if (peek() == '}') { ++m_i; return true; }
        for (;;) {
            skip_ws();
            std::string key;
            if (!read_string(key)) return false;
            skip_ws();
            if (!consume(':')) return false;
            skip_ws();
            if (!on_member(key, *this)) {
                if (!skip_value()) return false; // member handler declined; skip
            }
            skip_ws();
            char c = peek();
            if (c == ',') { ++m_i; continue; }
            if (c == '}') { ++m_i; return true; }
            return false;
        }
    }

    // Readers for a value at the current position.
    bool read_string(std::string& out) {
        skip_ws();
        if (!consume('"')) return false;
        out.clear();
        while (m_i < m_s.size()) {
            char c = m_s[m_i++];
            if (c == '"') return true;
            if (c == '\\') {
                if (m_i >= m_s.size()) return false;
                char e = m_s[m_i++];
                switch (e) {
                    case '"': out.push_back('"'); break;
                    case '\\': out.push_back('\\'); break;
                    case '/': out.push_back('/'); break;
                    case 'n': out.push_back('\n'); break;
                    case 't': out.push_back('\t'); break;
                    case 'r': out.push_back('\r'); break;
                    case 'b': out.push_back('\b'); break;
                    case 'f': out.push_back('\f'); break;
                    case 'u': {
                        if (m_i + 4 > m_s.size()) return false;
                        // Decode BMP code point; emit UTF-8. Sufficient for ids.
                        unsigned cp = 0;
                        for (int k = 0; k < 4; ++k) {
                            char h = m_s[m_i++];
                            cp <<= 4;
                            if (h >= '0' && h <= '9') cp |= (h - '0');
                            else if (h >= 'a' && h <= 'f') cp |= (h - 'a' + 10);
                            else if (h >= 'A' && h <= 'F') cp |= (h - 'A' + 10);
                            else return false;
                        }
                        append_utf8(out, cp);
                        break;
                    }
                    default: return false;
                }
            } else {
                out.push_back(c);
            }
        }
        return false; // unterminated
    }

    bool read_number(double& out) {
        skip_ws();
        std::size_t start = m_i;
        if (peek() == '-' || peek() == '+') ++m_i;
        bool any = false;
        while (m_i < m_s.size()) {
            char c = m_s[m_i];
            if ((c >= '0' && c <= '9') || c == '.' || c == 'e' || c == 'E' ||
                c == '+' || c == '-') { ++m_i; any = true; }
            else break;
        }
        if (!any) return false;
        try {
            out = std::stod(m_s.substr(start, m_i - start));
        } catch (...) { return false; }
        return true;
    }

    // Skip any JSON value (used to ignore unknown keys / unneeded members).
    bool skip_value() {
        skip_ws();
        char c = peek();
        if (c == '"') { std::string tmp; return read_string(tmp); }
        if (c == '{') return skip_object();
        if (c == '[') return skip_array();
        if (c == 't' || c == 'f') return skip_literal_bool();
        if (c == 'n') return skip_literal("null");
        double d; return read_number(d);
    }

    char peek() const { return (m_i < m_s.size()) ? m_s[m_i] : '\0'; }

private:
    bool skip_object() {
        if (!consume('{')) return false;
        skip_ws();
        if (peek() == '}') { ++m_i; return true; }
        for (;;) {
            skip_ws();
            std::string k;
            if (!read_string(k)) return false;
            skip_ws();
            if (!consume(':')) return false;
            if (!skip_value()) return false;
            skip_ws();
            char c = peek();
            if (c == ',') { ++m_i; continue; }
            if (c == '}') { ++m_i; return true; }
            return false;
        }
    }
    bool skip_array() {
        if (!consume('[')) return false;
        skip_ws();
        if (peek() == ']') { ++m_i; return true; }
        for (;;) {
            if (!skip_value()) return false;
            skip_ws();
            char c = peek();
            if (c == ',') { ++m_i; continue; }
            if (c == ']') { ++m_i; return true; }
            return false;
        }
    }
    bool skip_literal_bool() {
        if (m_s.compare(m_i, 4, "true") == 0) { m_i += 4; return true; }
        if (m_s.compare(m_i, 5, "false") == 0) { m_i += 5; return true; }
        return false;
    }
    bool skip_literal(const char* lit) {
        std::size_t n = std::strlen(lit);
        if (m_s.compare(m_i, n, lit) == 0) { m_i += n; return true; }
        return false;
    }
    void skip_ws() {
        while (m_i < m_s.size()) {
            char c = m_s[m_i];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') ++m_i;
            else break;
        }
    }
    bool consume(char c) {
        if (m_i < m_s.size() && m_s[m_i] == c) { ++m_i; return true; }
        return false;
    }
    static void append_utf8(std::string& out, unsigned cp) {
        if (cp < 0x80) out.push_back(static_cast<char>(cp));
        else if (cp < 0x800) {
            out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else {
            out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        }
    }

    const std::string& m_s;
    std::size_t m_i;
};

// =============================================================================
//  SHA-1 + Base64 (for the RFC6455 handshake only).
// =============================================================================
void sha1(const uint8_t* data, std::size_t len, uint8_t out[20]) {
    uint32_t h[5] = {0x67452301u, 0xEFCDAB89u, 0x98BADCFEu, 0x10325476u, 0xC3D2E1F0u};
    uint64_t ml = static_cast<uint64_t>(len) * 8u;

    std::vector<uint8_t> msg(data, data + len);
    msg.push_back(0x80);
    while (msg.size() % 64 != 56) msg.push_back(0x00);
    for (int i = 7; i >= 0; --i) msg.push_back(static_cast<uint8_t>((ml >> (i * 8)) & 0xFF));

    auto rol = [](uint32_t v, int c) { return (v << c) | (v >> (32 - c)); };
    for (std::size_t chunk = 0; chunk < msg.size(); chunk += 64) {
        uint32_t w[80];
        for (int i = 0; i < 16; ++i) {
            w[i] = (uint32_t(msg[chunk + i * 4]) << 24) |
                   (uint32_t(msg[chunk + i * 4 + 1]) << 16) |
                   (uint32_t(msg[chunk + i * 4 + 2]) << 8) |
                   (uint32_t(msg[chunk + i * 4 + 3]));
        }
        for (int i = 16; i < 80; ++i)
            w[i] = rol(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);

        uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4];
        for (int i = 0; i < 80; ++i) {
            uint32_t f, k;
            if (i < 20) { f = (b & c) | ((~b) & d); k = 0x5A827999u; }
            else if (i < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1u; }
            else if (i < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDCu; }
            else { f = b ^ c ^ d; k = 0xCA62C1D6u; }
            uint32_t tmp = rol(a, 5) + f + e + k + w[i];
            e = d; d = c; c = rol(b, 30); b = a; a = tmp;
        }
        h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e;
    }
    for (int i = 0; i < 5; ++i) {
        out[i * 4]     = static_cast<uint8_t>((h[i] >> 24) & 0xFF);
        out[i * 4 + 1] = static_cast<uint8_t>((h[i] >> 16) & 0xFF);
        out[i * 4 + 2] = static_cast<uint8_t>((h[i] >> 8) & 0xFF);
        out[i * 4 + 3] = static_cast<uint8_t>(h[i] & 0xFF);
    }
}

std::string base64(const uint8_t* data, std::size_t len) {
    static const char* tbl =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    out.reserve(((len + 2) / 3) * 4);
    std::size_t i = 0;
    while (i + 3 <= len) {
        uint32_t n = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2];
        out.push_back(tbl[(n >> 18) & 0x3F]);
        out.push_back(tbl[(n >> 12) & 0x3F]);
        out.push_back(tbl[(n >> 6) & 0x3F]);
        out.push_back(tbl[n & 0x3F]);
        i += 3;
    }
    if (len - i == 1) {
        uint32_t n = (data[i] << 16);
        out.push_back(tbl[(n >> 18) & 0x3F]);
        out.push_back(tbl[(n >> 12) & 0x3F]);
        out.push_back('=');
        out.push_back('=');
    } else if (len - i == 2) {
        uint32_t n = (data[i] << 16) | (data[i + 1] << 8);
        out.push_back(tbl[(n >> 18) & 0x3F]);
        out.push_back(tbl[(n >> 12) & 0x3F]);
        out.push_back(tbl[(n >> 6) & 0x3F]);
        out.push_back('=');
    }
    return out;
}

} // anonymous namespace

namespace bridge_detail {

// =============================================================================
//  WsServer — minimal single-client RFC6455 loopback server.
//
//  Design: binds to loopback (127.0.0.1) only. Accepts one client at a time
//  (sufficient for a single UI editor view / browser tab per bridge instance).
//  Runs an accept+receive loop on a background thread; inbound TEXT frames are
//  handed to the on_text callback (-> S760Bridge::on_input). Outbound TEXT
//  (telemetry) and BINARY (display frames) are sent from whatever thread calls
//  send_text / send_binary (the pump thread), guarded by a send mutex.
// =============================================================================
class WsServer {
public:
    using TextHandler = std::function<void(const std::string&)>;

    WsServer() {
#if defined(_WIN32)
        WSADATA wsa;
        m_wsa_ok = (WSAStartup(MAKEWORD(2, 2), &wsa) == 0);
#endif
    }

    ~WsServer() {
        stop();
#if defined(_WIN32)
        if (m_wsa_ok) WSACleanup();
#endif
    }

    bool start(uint16_t port, TextHandler on_text) {
        if (m_running.load()) return false;
#if defined(_WIN32)
        if (!m_wsa_ok) return false;
#endif
        m_on_text = std::move(on_text);

        m_listen = ::socket(AF_INET, SOCK_STREAM, 0);
        if (m_listen == INVALID_SOCK) return false;

        int yes = 1;
        ::setsockopt(m_listen, SOL_SOCKET, SO_REUSEADDR,
                     reinterpret_cast<const char*>(&yes), sizeof(yes));

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK); // loopback only
        addr.sin_port = htons(port);

        if (::bind(m_listen, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0) {
            CLOSESOCK(m_listen); m_listen = INVALID_SOCK; return false;
        }
        if (::listen(m_listen, 1) != 0) {
            CLOSESOCK(m_listen); m_listen = INVALID_SOCK; return false;
        }

        // Read back the actual bound port (for ephemeral port == 0).
        sockaddr_in bound{};
#if defined(_WIN32)
        int blen = sizeof(bound);
#else
        socklen_t blen = sizeof(bound);
#endif
        if (::getsockname(m_listen, reinterpret_cast<sockaddr*>(&bound), &blen) == 0) {
            m_port = ntohs(bound.sin_port);
        } else {
            m_port = port;
        }

        m_running.store(true);
        m_thread = std::thread([this] { run(); });
        return true;
    }

    void stop() {
        if (!m_running.exchange(false)) return;
        if (m_listen != INVALID_SOCK) { CLOSESOCK(m_listen); m_listen = INVALID_SOCK; }
        {
            std::lock_guard<std::mutex> lk(m_send_mutex);
            if (m_client != INVALID_SOCK) { CLOSESOCK(m_client); m_client = INVALID_SOCK; }
        }
        if (m_thread.joinable()) m_thread.join();
    }

    bool running() const { return m_running.load(); }
    uint16_t port() const { return m_port; }

    void send_text(const std::string& s) {
        send_frame(0x1, reinterpret_cast<const uint8_t*>(s.data()), s.size());
    }
    void send_binary(const uint8_t* data, std::size_t len) {
        send_frame(0x2, data, len);
    }

private:
    void run() {
        while (m_running.load()) {
            socket_t c = ::accept(m_listen, nullptr, nullptr);
            if (c == INVALID_SOCK) {
                if (!m_running.load()) break;
                continue;
            }
            if (!handshake(c)) { CLOSESOCK(c); continue; }
            {
                std::lock_guard<std::mutex> lk(m_send_mutex);
                m_client = c;
            }
            serve_client(c);
            {
                std::lock_guard<std::mutex> lk(m_send_mutex);
                if (m_client == c) m_client = INVALID_SOCK;
            }
            CLOSESOCK(c);
        }
    }

    static bool recv_line(socket_t s, std::string& line) {
        line.clear();
        char ch;
        while (true) {
            int n = ::recv(s, &ch, 1, 0);
            if (n <= 0) return false;
            if (ch == '\n') return true;
            if (ch != '\r') line.push_back(ch);
        }
    }

    bool handshake(socket_t c) {
        std::string line, key;
        // Request line
        if (!recv_line(c, line)) return false;
        // Headers until blank line
        while (recv_line(c, line)) {
            if (line.empty()) break;
            auto colon = line.find(':');
            if (colon == std::string::npos) continue;
            std::string name = line.substr(0, colon);
            std::string val = line.substr(colon + 1);
            // trim leading spaces of val
            while (!val.empty() && (val.front() == ' ' || val.front() == '\t')) val.erase(val.begin());
            // case-insensitive compare of header name
            std::string lname = name;
            std::transform(lname.begin(), lname.end(), lname.begin(),
                           [](unsigned char ch) { return static_cast<char>(::tolower(ch)); });
            if (lname == "sec-websocket-key") key = val;
        }
        if (key.empty()) return false;

        std::string accept_src = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
        uint8_t digest[20];
        sha1(reinterpret_cast<const uint8_t*>(accept_src.data()), accept_src.size(), digest);
        std::string accept = base64(digest, 20);

        std::ostringstream resp;
        resp << "HTTP/1.1 101 Switching Protocols\r\n"
             << "Upgrade: websocket\r\n"
             << "Connection: Upgrade\r\n"
             << "Sec-WebSocket-Accept: " << accept << "\r\n\r\n";
        std::string r = resp.str();
        return send_all(c, reinterpret_cast<const uint8_t*>(r.data()), r.size());
    }

    static bool recv_all(socket_t s, uint8_t* buf, std::size_t len) {
        std::size_t got = 0;
        while (got < len) {
            int n = ::recv(s, reinterpret_cast<char*>(buf + got),
                           static_cast<int>(len - got), 0);
            if (n <= 0) return false;
            got += static_cast<std::size_t>(n);
        }
        return true;
    }

    void serve_client(socket_t c) {
        while (m_running.load()) {
            uint8_t hdr[2];
            if (!recv_all(c, hdr, 2)) return;
            bool fin = (hdr[0] & 0x80) != 0;
            uint8_t opcode = hdr[0] & 0x0F;
            bool masked = (hdr[1] & 0x80) != 0;
            uint64_t payload_len = hdr[1] & 0x7F;

            if (payload_len == 126) {
                uint8_t ext[2];
                if (!recv_all(c, ext, 2)) return;
                payload_len = (uint64_t(ext[0]) << 8) | ext[1];
            } else if (payload_len == 127) {
                uint8_t ext[8];
                if (!recv_all(c, ext, 8)) return;
                payload_len = 0;
                for (int i = 0; i < 8; ++i) payload_len = (payload_len << 8) | ext[i];
            }

            uint8_t mask[4] = {0, 0, 0, 0};
            if (masked && !recv_all(c, mask, 4)) return;

            // Guard against absurd frames (loopback UI control messages are tiny).
            if (payload_len > (16u * 1024u * 1024u)) return;

            std::vector<uint8_t> payload(static_cast<std::size_t>(payload_len));
            if (payload_len && !recv_all(c, payload.data(), payload.size())) return;
            if (masked) {
                for (std::size_t i = 0; i < payload.size(); ++i) payload[i] ^= mask[i & 3];
            }

            if (opcode == 0x8) return;            // close
            if (opcode == 0x9) {                   // ping -> pong
                send_frame(0xA, payload.data(), payload.size());
                continue;
            }
            if (opcode == 0xA) continue;          // pong
            if (!fin) continue;                   // (fragmentation not expected here)

            if (opcode == 0x1 && m_on_text) {     // text => control JSON
                m_on_text(std::string(payload.begin(), payload.end()));
            }
            // Binary inbound is not part of the client->server contract; ignore.
        }
    }

    static bool send_all(socket_t s, const uint8_t* data, std::size_t len) {
        std::size_t sent = 0;
        while (sent < len) {
            int n = ::send(s, reinterpret_cast<const char*>(data + sent),
                           static_cast<int>(len - sent), 0);
            if (n <= 0) return false;
            sent += static_cast<std::size_t>(n);
        }
        return true;
    }

    void send_frame(uint8_t opcode, const uint8_t* data, std::size_t len) {
        std::lock_guard<std::mutex> lk(m_send_mutex);
        if (m_client == INVALID_SOCK) return;

        std::vector<uint8_t> frame;
        frame.reserve(len + 10);
        frame.push_back(static_cast<uint8_t>(0x80 | opcode)); // FIN + opcode
        if (len < 126) {
            frame.push_back(static_cast<uint8_t>(len));
        } else if (len <= 0xFFFF) {
            frame.push_back(126);
            frame.push_back(static_cast<uint8_t>((len >> 8) & 0xFF));
            frame.push_back(static_cast<uint8_t>(len & 0xFF));
        } else {
            frame.push_back(127);
            for (int i = 7; i >= 0; --i)
                frame.push_back(static_cast<uint8_t>((static_cast<uint64_t>(len) >> (i * 8)) & 0xFF));
        }
        // Server->client frames are NOT masked (RFC6455 §5.1).
        frame.insert(frame.end(), data, data + len);
        if (!send_all(m_client, frame.data(), frame.size())) {
            CLOSESOCK(m_client);
            m_client = INVALID_SOCK;
        }
    }

#if defined(_WIN32)
    bool m_wsa_ok = false;
#endif
    socket_t m_listen = INVALID_SOCK;
    socket_t m_client = INVALID_SOCK;
    std::atomic<bool> m_running{false};
    std::thread m_thread;
    std::mutex m_send_mutex;
    TextHandler m_on_text;
    uint16_t m_port = 0;
};

} // namespace bridge_detail

// =============================================================================
//  S760Bridge
// =============================================================================

S760Bridge::S760Bridge(IS760Host* host) : m_host(host) {}

S760Bridge::~S760Bridge() {
    stop_ws_server();
}

// ----------------------------------------------------------------------------
//  Client message decoding (static, unit-testable)
// ----------------------------------------------------------------------------
bool S760Bridge::decode_client_message(const std::string& json,
                                       bridge::ClientMessage& out) {
    out = bridge::ClientMessage{};
    bool have_type = false;
    bool type_ok = true;

    JsonReader root(json);
    bool ok = root.parse_object([&](const std::string& key, JsonReader& val) -> bool {
        if (key == "type") {
            std::string t;
            if (!val.read_string(t)) { type_ok = false; return true; }
            if (!bridge::parse_client_message_type(t, out.type)) { type_ok = false; }
            have_type = true;
            return true;
        }
        if (key == "payload") {
            bridge::ClientPayload& p = out.payload;
            bool pok = val.parse_object([&](const std::string& pk, JsonReader& pv) -> bool {
                if (pk == "id")       { std::string s; if (pv.read_string(s)) { p.has_id = true; p.id = s; } return true; }
                if (pk == "diskPath") { std::string s; if (pv.read_string(s)) { p.has_diskPath = true; p.diskPath = s; } return true; }
                if (pk == "delta")    { double d; if (pv.read_number(d)) { p.has_delta = true; p.delta = d; } return true; }
                if (pk == "x")        { double d; if (pv.read_number(d)) { p.has_x = true; p.x = d; } return true; }
                if (pk == "y")        { double d; if (pv.read_number(d)) { p.has_y = true; p.y = d; } return true; }
                if (pk == "button")   { double d; if (pv.read_number(d)) { p.has_button = true; p.button = static_cast<int>(d); } return true; }
                if (pk == "note")     { double d; if (pv.read_number(d)) { p.has_note = true; p.note = static_cast<int>(d); } return true; }
                if (pk == "velocity") { double d; if (pv.read_number(d)) { p.has_velocity = true; p.velocity = static_cast<int>(d); } return true; }
                return false; // unknown payload key -> let reader skip it
            });
            return pok;
        }
        return false; // unknown top-level key -> let reader skip it
    });

    return ok && have_type && type_ok;
}

// ----------------------------------------------------------------------------
//  on_input
// ----------------------------------------------------------------------------
bool S760Bridge::on_input(const std::string& json) {
    bridge::ClientMessage msg;
    if (!decode_client_message(json, msg)) {
        return false; // malformed / unknown => ignored per design error handling
    }
    std::lock_guard<std::mutex> lock(m_mutex);
    apply_message(msg);
    return true;
}

void S760Bridge::apply_message(const bridge::ClientMessage& msg) {
    using T = bridge::ClientMessageType;
    if (!m_host) return;
    const bridge::ClientPayload& p = msg.payload;

    switch (msg.type) {
        case T::NOTE_ON: {
            if (p.has_note) {
                uint8_t note = static_cast<uint8_t>(std::max(0, std::min(127, p.note)));
                uint8_t vel  = static_cast<uint8_t>(std::max(1, std::min(127, p.has_velocity ? p.velocity : 100)));
                uint8_t m[3] = {0x90, note, vel};
                m_host->send_midi_message(m, 3);
            }
            break;
        }
        case T::NOTE_OFF: {
            if (p.has_note) {
                uint8_t note = static_cast<uint8_t>(std::max(0, std::min(127, p.note)));
                uint8_t vel  = static_cast<uint8_t>(std::max(0, std::min(127, p.has_velocity ? p.velocity : 0)));
                uint8_t m[3] = {0x80, note, vel};
                m_host->send_midi_message(m, 3);
            }
            break;
        }
        case T::MOUNT_DISK: {
            if (p.has_diskPath && !p.diskPath.empty()) {
                m_host->get_drive_manager().mount_floppy(p.diskPath);
            }
            break;
        }
        case T::BUTTON_PRESS:
        case T::BUTTON_RELEASE:
        case T::DIAL_DELTA:
        case T::MOUSE_MOVE:
        case T::MOUSE_CLICK:
            // Front-panel buttons, encoders and the pointer are consumed by the
            // emulated input map once the OS runs. The host's input surface
            // (handle_input_state) is polled by the core; wiring specific ids
            // into that map is deferred to the input-map task. Accepting and
            // decoding them here satisfies the protocol contract so the client
            // can send the full message set without error.
            break;
    }
}

// ----------------------------------------------------------------------------
//  Callbacks + emission
// ----------------------------------------------------------------------------
void S760Bridge::set_frame_callback(FrameCallback cb) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_frame_cb = std::move(cb);
}

void S760Bridge::set_telemetry_callback(TelemetryCallback cb) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_telemetry_cb = std::move(cb);
}

void S760Bridge::emit_frame(const std::vector<uint8_t>& framed) {
    if (m_frame_cb) m_frame_cb(framed.data(), framed.size());
    if (m_ws && m_ws->running()) m_ws->send_binary(framed.data(), framed.size());
}

void S760Bridge::emit_telemetry(const std::string& json) {
    if (m_telemetry_cb) m_telemetry_cb(json);
    if (m_ws && m_ws->running()) m_ws->send_text(json);
}

// ----------------------------------------------------------------------------
//  Frame production
// ----------------------------------------------------------------------------
std::vector<uint8_t> S760Bridge::build_frame(bridge::SurfaceId id,
                                             uint16_t width, uint16_t height,
                                             bridge::PixelFormat format,
                                             const uint8_t* payload,
                                             std::size_t payload_len) {
    std::vector<uint8_t> out;
    out.reserve(bridge::FRAME_HEADER_SIZE + payload_len);
    out.push_back(static_cast<uint8_t>(id));
    out.push_back(static_cast<uint8_t>(width & 0xFF));          // u16 LE
    out.push_back(static_cast<uint8_t>((width >> 8) & 0xFF));
    out.push_back(static_cast<uint8_t>(height & 0xFF));         // u16 LE
    out.push_back(static_cast<uint8_t>((height >> 8) & 0xFF));
    out.push_back(static_cast<uint8_t>(format));
    if (payload && payload_len) out.insert(out.end(), payload, payload + payload_len);
    return out;
}

std::vector<uint8_t> S760Bridge::blank_mono1(uint16_t width, uint16_t height) {
    return std::vector<uint8_t>(bridge::payload_size(bridge::PixelFormat::MONO1, width, height), 0u);
}

// ----------------------------------------------------------------------------
//  emit_surface — centralized payload-length validation + suppression guard.
//
//  Validates the candidate payload against the protocol's exact payload-length
//  rule (bridge::payload_size). On a match, it builds the 6-byte-framed message
//  and emits it exactly as a direct build_frame()/emit_frame() pair would, so
//  correctly-sized surfaces are byte-for-byte identical to the previous code
//  path. On a mismatch, it SUPPRESSES emission (no malformed frame reaches the
//  client, which would discard it as a header/geometry/payload-length mismatch)
//  and records a descriptive finding instead (mame-live-backend Requirement
//  5.6, Property 8).
//
//  LOCKING: the caller MUST hold m_mutex. push_frames() (the only caller) takes
//  m_mutex for its whole body, so this records to m_findings directly WITHOUT
//  re-locking. Do not call emit_surface() without holding m_mutex.
// ----------------------------------------------------------------------------
void S760Bridge::emit_surface(bridge::SurfaceId id, uint16_t width, uint16_t height,
                              bridge::PixelFormat format,
                              const uint8_t* payload, std::size_t payload_len) {
    const std::size_t expected = bridge::payload_size(format, width, height);
    if (payload_len != expected) {
        // Suppress: do not emit a malformed frame. Record a reported finding
        // identifying the surface and the expected-vs-actual payload length.
        std::ostringstream msg;
        msg << "suppressed surface emission: surfaceId="
            << static_cast<unsigned>(static_cast<uint8_t>(id))
            << " geometry=" << width << "x" << height
            << " format=" << static_cast<unsigned>(static_cast<uint8_t>(format))
            << " expectedPayloadLen=" << expected
            << " actualPayloadLen=" << payload_len
            << " (payload length does not match payload_size)";
        m_findings.push_back(msg.str()); // m_mutex held by caller
        return;
    }
    emit_frame(build_frame(id, width, height, format, payload, payload_len));
}

std::vector<std::string> S760Bridge::findings() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_findings;
}

void S760Bridge::push_frames() {
    std::lock_guard<std::mutex> lock(m_mutex);

    // --- CRT (RGBA8888) ----------------------------------------------------
    // Source the live video frame from the host and normalize it to the fixed
    // CRT geometry advertised by the protocol. The host stores RGBA already
    // (0xAABBGGRR little-endian layout == R,G,B,A byte order on the wire).
    std::vector<uint8_t> crt_payload(
        bridge::payload_size(bridge::PixelFormat::RGBA8888,
                             bridge::CRT_WIDTH, bridge::CRT_HEIGHT), 0u);
    if (m_host) {
        VideoFrame vf = m_host->get_latest_video_frame();
        if (vf.width && vf.height && !vf.rgba_pixels.empty()) {
            // Copy row-by-row into the fixed CRT buffer, clipping to geometry.
            uint32_t copy_w = std::min<uint32_t>(vf.width, bridge::CRT_WIDTH);
            uint32_t copy_h = std::min<uint32_t>(vf.height, bridge::CRT_HEIGHT);
            for (uint32_t y = 0; y < copy_h; ++y) {
                const uint32_t* src = &vf.rgba_pixels[y * vf.width];
                uint8_t* dst = &crt_payload[(y * bridge::CRT_WIDTH) * 4];
                std::memcpy(dst, src, copy_w * 4u);
            }
        }
    }
    emit_surface(bridge::SurfaceId::CRT,
                 bridge::CRT_WIDTH, bridge::CRT_HEIGHT,
                 bridge::PixelFormat::RGBA8888,
                 crt_payload.data(), crt_payload.size());

    // --- LCD (SED1335 160x64, MONO1) ---------------------------------------
    // Ask the host for a genuine SED1335 raster via get_lcd_surface(). The MAME
    // backend derives the surface solely from m_sed_vram; the Core backend
    // returns false (it exposes no LCD raster), in which case the Bridge keeps
    // its authentic-blank behavior so that backend stays byte-for-byte identical
    // on the wire (mame-live-backend Requirements 3.3, 4.7).
    {
        std::vector<uint8_t> lcd = blank_mono1(bridge::LCD_WIDTH, bridge::LCD_HEIGHT);
        if (m_host) {
            m_host->get_lcd_surface(lcd.data(), lcd.size());
        }
        emit_surface(bridge::SurfaceId::LCD,
                     bridge::LCD_WIDTH, bridge::LCD_HEIGHT,
                     bridge::PixelFormat::MONO1,
                     lcd.data(), lcd.size());
    }

    // --- OLED (Gotek 128x32, MONO1) ----------------------------------------
    {
        std::vector<uint8_t> oled = blank_mono1(bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT);
        emit_surface(bridge::SurfaceId::OLED,
                     bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT,
                     bridge::PixelFormat::MONO1,
                     oled.data(), oled.size());
    }

    // --- Telemetry ---------------------------------------------------------
    bridge::ServerTelemetry t = current_telemetry_locked();
    emit_telemetry(encode_telemetry(t));
}

void S760Bridge::pump() {
    if (m_host) m_host->run_frame();
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        ++m_frame_counter;
    }
    push_frames();
}

// ----------------------------------------------------------------------------
//  Telemetry
// ----------------------------------------------------------------------------
bridge::ServerTelemetry S760Bridge::current_telemetry_locked() const {
    // Geometry fields default to the protocol constants (CRT 640x480,
    // LCD 160x64, OLED/Gotek 128x32) via ServerTelemetry's member initializers,
    // so they are reported fixed and unchanged here (mame-live-backend R5.3).
    bridge::ServerTelemetry t;

    // Monotonic-ish timestamp derived from the frame counter at ~60fps. A real
    // wall clock is not required by the contract (it only needs to be a
    // monotonic ms value from the server).
    t.timestamp = static_cast<double>(m_frame_counter) * (1000.0 / 60.0);
    // fps MUST stay within [0,240] (mame-live-backend R5.3). The backend runs a
    // 60Hz frame; clamp defensively so the field can never leave the range.
    t.fps = std::max(0.0, std::min(240.0, 60.0));
    // currentMode: report the derived mode where available, otherwise the EMPTY
    // string. m_current_mode defaults to "" and is only written from genuine
    // OS/display state, so no invented mode content is ever reported (R5.4).
    t.currentMode = m_current_mode;

    if (m_host) {
        // Output peaks: the recorder tracks input/live peaks; use them as the
        // available peak source until a dedicated output meter is exposed.
        const auto& rec = m_host->get_recorder();
        t.peakL = static_cast<double>(rec.get_peak_level_left());
        t.peakR = static_cast<double>(rec.get_peak_level_right());
    }
    // activeVoices: the host does not yet expose a voice count; leave 0 until a
    // voice-telemetry surface is added.
    t.activeVoices = 0;
    return t;
}

bridge::ServerTelemetry S760Bridge::current_telemetry() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return current_telemetry_locked();
}

std::string S760Bridge::encode_telemetry(const bridge::ServerTelemetry& t) {
    // Hand-rolled JSON to avoid pulling in a JSON library on the hot path. The
    // field set/order mirrors the TS S760ServerTelemetry exactly.
    auto num = [](double v) {
        std::ostringstream os;
        if (std::floor(v) == v && std::fabs(v) < 1e15) {
            os << static_cast<long long>(v);
        } else {
            os.precision(6);
            os << std::fixed << v;
        }
        return os.str();
    };
    auto jstr = [](const std::string& s) {
        std::string o = "\"";
        for (char c : s) {
            switch (c) {
                case '"':  o += "\\\""; break;
                case '\\': o += "\\\\"; break;
                case '\n': o += "\\n";  break;
                case '\r': o += "\\r";  break;
                case '\t': o += "\\t";  break;
                default:   o.push_back(c); break;
            }
        }
        o.push_back('"');
        return o;
    };

    std::ostringstream os;
    os << '{'
       << "\"timestamp\":"    << num(t.timestamp) << ','
       << "\"fps\":"          << num(t.fps) << ','
       << "\"crtWidth\":"     << t.crtWidth << ','
       << "\"crtHeight\":"    << t.crtHeight << ','
       << "\"lcdWidth\":"     << t.lcdWidth << ','
       << "\"lcdHeight\":"    << t.lcdHeight << ','
       << "\"gotekWidth\":"   << t.gotekWidth << ','
       << "\"gotekHeight\":"  << t.gotekHeight << ','
       << "\"peakL\":"        << num(t.peakL) << ','
       << "\"peakR\":"        << num(t.peakR) << ','
       << "\"activeVoices\":" << t.activeVoices << ','
       << "\"currentMode\":"  << jstr(t.currentMode)
       << '}';
    return os.str();
}

// ----------------------------------------------------------------------------
//  WebSocket server lifecycle
// ----------------------------------------------------------------------------
bool S760Bridge::start_ws_server(uint16_t port) {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_ws && m_ws->running()) return false;
    m_ws = std::make_unique<bridge_detail::WsServer>();
    // Forward inbound client TEXT frames into the same on_input() decode path.
    bool ok = m_ws->start(port, [this](const std::string& text) {
        this->on_input(text);
    });
    if (!ok) { m_ws.reset(); return false; }
    return true;
}

void S760Bridge::stop_ws_server() {
    std::unique_ptr<bridge_detail::WsServer> ws;
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        ws = std::move(m_ws);
    }
    // Destroy/stop outside the lock so the server thread can't deadlock against
    // an on_input() callback that also takes m_mutex.
    if (ws) ws->stop();
}

bool S760Bridge::ws_running() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_ws && m_ws->running();
}

uint16_t S760Bridge::ws_port() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return (m_ws && m_ws->running()) ? m_ws->port() : 0;
}

} // namespace s760
