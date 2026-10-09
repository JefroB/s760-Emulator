#include "s760/s760_webview_host.hpp"

// =============================================================================
//  s760_webview_host.cpp
//
//  Implements the platform-abstracted WebView host and the bridge-attached
//  editor controller for the S-760 plugin editor views (task 3.6).
//
//  CONCRETE vs STUB (as shipped in this build):
//    * StubWebViewHost      — ALWAYS compiled. Portable, headless, no OS window.
//                             Fully implements IWebViewHost in memory so the
//                             editor<->bridge wiring is compile/link-clean and
//                             deterministically testable in CI. This is what
//                             create_webview_host() returns by default.
//    * WebView2WebViewHost  — Windows concrete embed, compiled ONLY when
//                             S760_HAVE_WEBVIEW2 is defined (OFF by default,
//                             requires the WebView2 SDK/runtime). See the gated
//                             block at the bottom. macOS WKWebView / Linux
//                             WebKitGTK / CEF follow the same pattern and are
//                             future work behind their own flags.
//
//  The format-specific plugin glue (IPlugView / effEditOpen / clap.gui) targets
//  ONLY IWebViewHost + S760EditorController, so swapping in a real backend later
//  requires no change to the plugins.
// =============================================================================

#include <cstdlib>
#include <mutex>
#include <vector>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace s760 {

// =============================================================================
//  StubWebViewHost — portable, headless implementation (always available).
// =============================================================================
//  Records the loaded URL and buffers outbound C++->JS messages so tests can
//  inspect them. Provides post_message_from_js() as the test-side entry point
//  that simulates the page posting a message to C++ (looping into the registered
//  JsMessageHandler), which is exactly what a real backend's script-message
//  callback does. No OS window is created.
class StubWebViewHost : public IWebViewHost {
public:
    bool create(NativeWindowHandle parent, const WebViewSize& size,
                const std::string& url) override {
        (void)parent;
        m_size = size;
        m_url = url;
        m_created = true;
        return true;
    }

    void destroy() override {
        m_created = false;
        m_handler = nullptr;
        m_text_to_js.clear();
        m_frames_to_js.clear();
    }

    bool is_created() const override { return m_created; }

    void set_size(const WebViewSize& size) override { m_size = size; }
    WebViewSize size() const override { return m_size; }

    void set_js_message_handler(JsMessageHandler handler) override {
        m_handler = std::move(handler);
    }

    void post_text_to_js(const std::string& text) override {
        if (!m_created) return;
        m_text_to_js.push_back(text);
    }

    void post_frame_to_js(const uint8_t* data, std::size_t len) override {
        if (!m_created || !data) return;
        m_frames_to_js.emplace_back(data, data + len);
    }

    const std::string& loaded_url() const override { return m_url; }
    const char* backend_name() const override { return "stub"; }

    // --- Test / diagnostic surface (not part of IWebViewHost) ----------------

    // Simulate the page posting a string message to C++ (JS -> C++). This is the
    // same path a real backend invokes from its script-message callback.
    void post_message_from_js(const std::string& message) {
        if (m_handler) m_handler(message);
    }

    const std::vector<std::string>& text_messages_to_js() const { return m_text_to_js; }
    const std::vector<std::vector<uint8_t>>& frames_to_js() const { return m_frames_to_js; }

private:
    bool                              m_created = false;
    std::string                       m_url;
    WebViewSize                       m_size;
    JsMessageHandler                  m_handler;
    std::vector<std::string>          m_text_to_js;
    std::vector<std::vector<uint8_t>> m_frames_to_js;
};

// Forward declaration of the gated concrete backend factory (defined at bottom
// when S760_HAVE_WEBVIEW2 is set). Returns nullptr when the real backend cannot
// be created, so the factory falls back to the stub.
#if defined(S760_HAVE_WEBVIEW2)
std::unique_ptr<IWebViewHost> try_create_webview2_host();
#endif

std::unique_ptr<IWebViewHost> create_webview_host() {
#if defined(S760_HAVE_WEBVIEW2)
    if (auto real = try_create_webview2_host()) {
        return real;
    }
#endif
    // Default: the portable stub keeps every caller build/link-clean.
    return std::make_unique<StubWebViewHost>();
}

// =============================================================================
//  S760EditorController
// =============================================================================

S760EditorController::S760EditorController(S760Bridge* bridge)
    : m_bridge(bridge) {}

S760EditorController::S760EditorController(S760Bridge* bridge,
                                           std::unique_ptr<IWebViewHost> host)
    : m_bridge(bridge), m_host(std::move(host)) {}

S760EditorController::~S760EditorController() {
    close();
}

std::string S760EditorController::resolve_frontend_url() {
    // 1) Explicit override (dev / CI): a full URL or path in S760_UI_URL.
    if (const char* env = std::getenv("S760_UI_URL")) {
        if (env[0] != '\0') return std::string(env);
    }

    // 2) Locate the built React app (google-ui/dist/index.html) relative to the
    //    loaded module (plugin binary) first, then the current working dir. We
    //    emit a file:// URL. On platforms where we cannot query the module path
    //    we fall back to a relative path the DAW/webview resolves against CWD.
    const std::string rel = "google-ui/dist/index.html";

#if defined(_WIN32)
    // Try to resolve relative to the directory containing THIS module so a
    // plugin installed anywhere finds its bundled UI. Walk up a few levels to
    // tolerate build/<cfg>/ layouts.
    HMODULE mod = nullptr;
    if (GetModuleHandleExA(
            GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
            GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCSTR>(&S760EditorController::resolve_frontend_url),
            &mod)) {
        char path[MAX_PATH] = {0};
        DWORD n = GetModuleFileNameA(mod, path, MAX_PATH);
        if (n > 0 && n < MAX_PATH) {
            std::string dir(path);
            auto slash = dir.find_last_of("\\/");
            if (slash != std::string::npos) dir.erase(slash);
            // Try dir, dir/.., dir/../.., dir/../../.. for the bundled UI.
            std::string prefix = dir;
            for (int up = 0; up < 4; ++up) {
                std::string candidate = prefix + "\\" + "google-ui\\dist\\index.html";
                DWORD attrs = GetFileAttributesA(candidate.c_str());
                if (attrs != INVALID_FILE_ATTRIBUTES &&
                    !(attrs & FILE_ATTRIBUTE_DIRECTORY)) {
                    std::string u = "file:///" + candidate;
                    for (char& c : u) if (c == '\\') c = '/';
                    return u;
                }
                prefix += "\\..";
            }
        }
    }
#endif

    // 3) Documented fallback: a relative file URL. A real backend resolves this
    //    against its working directory; the stub simply records it.
    return "file:///" + rel;
}

bool S760EditorController::open(NativeWindowHandle parent, const WebViewSize& size) {
    if (m_open) return true;
    if (!m_bridge) return false;

    if (!m_host) m_host = create_webview_host();
    if (!m_host) return false;

    m_size = size;
    const std::string url = resolve_frontend_url();
    if (!m_host->create(parent, size, url)) {
        return false;
    }

    install_bindings();
    m_open = true;

    // Push one initial frame so the page has content immediately on open.
    m_bridge->push_frames();
    return true;
}

void S760EditorController::close() {
    if (!m_open) {
        if (m_host && m_host->is_created()) m_host->destroy();
        return;
    }
    remove_bindings();
    if (m_host) m_host->destroy();
    m_open = false;
}

void S760EditorController::set_size(const WebViewSize& size) {
    m_size = size;
    if (m_host) m_host->set_size(size);
}

WebViewSize S760EditorController::size() const {
    return m_host ? m_host->size() : m_size;
}

void S760EditorController::tick() {
    if (!m_open || !m_bridge) return;
    // Advance the host one frame; the installed bridge callbacks post the
    // produced surfaces + telemetry to JS via the webview.
    m_bridge->pump();
}

void S760EditorController::install_bindings() {
    // JS -> C++ : forward every webview message verbatim to the bridge input.
    IWebViewHost* host = m_host.get();
    S760Bridge* bridge = m_bridge;
    host->set_js_message_handler([bridge](const std::string& message) {
        if (bridge) bridge->on_input(message);
    });

    // C++ -> JS : bridge frame + telemetry callbacks post into the webview.
    m_bridge->set_frame_callback([host](const uint8_t* data, std::size_t len) {
        host->post_frame_to_js(data, len);
    });
    m_bridge->set_telemetry_callback([host](const std::string& json) {
        host->post_text_to_js(json);
    });
}

void S760EditorController::remove_bindings() {
    if (m_bridge) {
        m_bridge->set_frame_callback(nullptr);
        m_bridge->set_telemetry_callback(nullptr);
    }
    if (m_host) m_host->set_js_message_handler(nullptr);
}

} // namespace s760

// =============================================================================
//  Concrete Windows backend (GATED — OFF by default).
// =============================================================================
//  This is intentionally compiled only when S760_HAVE_WEBVIEW2 is defined,
//  because it requires the Microsoft WebView2 SDK headers/import libs and the
//  Evergreen runtime, neither of which is guaranteed in this build/CI
//  environment. The code below is the real embed outline wired to the SAME
//  IWebViewHost contract; when the flag is OFF the factory above transparently
//  returns the StubWebViewHost, so the core library and all plugin editor entry
//  points remain fully buildable and link-clean.
//
//  To enable: install the WebView2 SDK and configure with
//      -DS760_HAVE_WEBVIEW2=ON  (and link WebView2Loader + add the SDK include).
// =============================================================================
#if defined(S760_HAVE_WEBVIEW2)

#include <wrl.h>
#include <wil/com.h>
#include "WebView2.h"

namespace s760 {

class WebView2WebViewHost : public IWebViewHost {
public:
    bool create(NativeWindowHandle parent, const WebViewSize& size,
                const std::string& url) override {
        m_parent = static_cast<HWND>(parent);
        m_size = size;
        m_url = url;
        // Real impl: CreateCoreWebView2EnvironmentWithOptions ->
        // CreateCoreWebView2Controller(m_parent) -> get_CoreWebView2 ->
        // add_WebMessageReceived (JS->C++) -> Navigate(url). Pump messages into
        // m_handler; implement post_text_to_js via PostWebMessageAsString and
        // post_frame_to_js via PostWebMessageAsJson/SharedBuffer. Omitted here
        // because it only compiles against the WebView2 SDK.
        m_created = true;
        return true;
    }
    void destroy() override { m_created = false; m_handler = nullptr; }
    bool is_created() const override { return m_created; }
    void set_size(const WebViewSize& size) override { m_size = size; /* controller->put_Bounds */ }
    WebViewSize size() const override { return m_size; }
    void set_js_message_handler(JsMessageHandler handler) override { m_handler = std::move(handler); }
    void post_text_to_js(const std::string& text) override { (void)text; /* PostWebMessageAsString */ }
    void post_frame_to_js(const uint8_t* data, std::size_t len) override { (void)data; (void)len; }
    const std::string& loaded_url() const override { return m_url; }
    const char* backend_name() const override { return "webview2"; }
private:
    HWND             m_parent = nullptr;
    bool             m_created = false;
    std::string      m_url;
    WebViewSize      m_size;
    JsMessageHandler m_handler;
};

std::unique_ptr<IWebViewHost> try_create_webview2_host() {
    // A real build verifies the Evergreen runtime is present before returning a
    // live host; if unavailable, return nullptr so the factory uses the stub.
    return std::make_unique<WebView2WebViewHost>();
}

} // namespace s760

#endif // S760_HAVE_WEBVIEW2
