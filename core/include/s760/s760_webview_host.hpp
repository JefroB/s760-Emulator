#pragma once

// =============================================================================
//  s760_webview_host.hpp
//
//  Platform-abstracted WebView host + bridge-attached editor controller for the
//  S-760 plugin editor views (task 3.6, F7 — greenfield plugin GUI).
//
//  WHAT THIS PROVIDES
//  ------------------
//  The VST3/VST2/CLAP plugins are C++ shared libraries loaded into a DAW. Their
//  editor view is a native WebView that loads the built React canonical UI
//  (google-ui/dist/index.html) and talks to the plugin's in-process
//  `S760Bridge` (task 3.2) over the ONE message contract defined in
//  `s760_bridge_protocol.hpp`. There is no socket on this path: the WebView's
//  JS<->C++ script-message channel is wired 1:1 to the bridge:
//
//        JS  (window.postMessage / script handler)
//          -> IWebViewHost delivers the string to S760EditorController
//          -> S760Bridge::on_input(json)                        [JS  -> C++]
//
//        S760Bridge frame callback (binary)   -> IWebViewHost::post_frame_to_js
//        S760Bridge telemetry callback (JSON) -> IWebViewHost::post_text_to_js
//                                                                 [C++ -> JS]
//
//  CONCRETE vs STUB (documented precisely, per the task):
//    * `IWebViewHost` is the platform abstraction. All plugin-format glue
//      (IPlugView / effEditOpen / clap.gui) depends ONLY on this interface and
//      on `S760EditorController`, so the wiring and the message contract are
//      fully compiled, exercised and testable regardless of platform.
//    * A portable `StubWebViewHost` (in s760_webview_host.cpp) is ALWAYS built.
//      It implements the full interface in memory (records loaded URL, buffers
//      messages, and loops a `post_message_from_js()` test entry point into the
//      registered handler) WITHOUT opening a real OS window. This keeps the
//      core library and the plugin editor entry points compile-clean and
//      link-clean in a headless/CI build, and lets the editor<->bridge wiring be
//      unit-tested deterministically.
//    * A concrete Windows `WebView2WebViewHost` is provided behind the
//      `S760_HAVE_WEBVIEW2` compile flag (OFF by default). It is the real
//      embed; it is intentionally gated because it requires the WebView2 SDK /
//      runtime which is not guaranteed in this build environment. When the flag
//      is OFF, `create_webview_host()` returns the stub so nothing fails to
//      build or link. The macOS WKWebView / Linux WebKitGTK and CEF backends
//      follow the same pattern and are future work behind their own flags.
//
//  THREADING
//  ---------
//    All WebView operations (create/destroy/load/post) MUST happen on the UI
//    thread the DAW opens the editor on. `S760EditorController::tick()` is the
//    per-frame pump driven by a UI timer; it calls `S760Bridge::pump()` and the
//    produced frames/telemetry are posted to JS from that same thread.
//
//  Spec: .kiro/specs/ui-consolidation/  (Requirements R5.2 plugin-editor mode,
//        R5.4; design "Plugin editor view — WebView host (per F7, greenfield)").
// =============================================================================

#include "s760/s760_bridge.hpp"

#include <cstdint>
#include <functional>
#include <memory>
#include <string>

namespace s760 {

// -----------------------------------------------------------------------------
//  Native window handle (opaque, platform-specific).
// -----------------------------------------------------------------------------
//  The DAW hands the plugin a parent window to embed the editor into:
//    * VST3  IPlugView::attached(void* parent, const char* type)  -> HWND/NSView
//    * VST2  effEditOpen  ptr == parent window handle
//    * CLAP  clap_window.ptr (HWND / NSView* / X11 window id)
//  We carry it as a void* so the abstraction stays header-portable.
using NativeWindowHandle = void*;

// -----------------------------------------------------------------------------
//  WebView editor geometry. The React shell is authored at a fixed design size;
//  the default matches a comfortable 1U-sampler editor window. The DAW may
//  resize; the host forwards the new size to the webview.
// -----------------------------------------------------------------------------
struct WebViewSize {
    uint32_t width  = 1024;
    uint32_t height = 640;
};

// -----------------------------------------------------------------------------
//  IWebViewHost — the platform abstraction every backend implements.
// -----------------------------------------------------------------------------
//  Lifetime: created by create_webview_host(); the owner calls create() with a
//  parent handle when the editor opens and destroy() when it closes. A single
//  host instance may be create()/destroy()'d more than once over its lifetime.
class IWebViewHost {
public:
    // Called by the host when JS posts a string message to C++ (the JS->C++
    // half of the channel). The payload is the raw string the page sent.
    using JsMessageHandler = std::function<void(const std::string& message)>;

    virtual ~IWebViewHost() = default;

    // Create the native webview as a child of `parent`, sized to `size`, and
    // load `url` (an absolute file:// URL to google-ui/dist/index.html or an
    // http(s) dev URL). Returns true on success. Must be called on the UI
    // thread. On an unsupported/headless backend the stub returns true and
    // records the url without opening a window.
    virtual bool create(NativeWindowHandle parent, const WebViewSize& size,
                         const std::string& url) = 0;

    // Tear down the native webview (idempotent).
    virtual void destroy() = 0;

    // True between a successful create() and destroy().
    virtual bool is_created() const = 0;

    // Resize the webview content area.
    virtual void set_size(const WebViewSize& size) = 0;

    // The current size (last create()/set_size()).
    virtual WebViewSize size() const = 0;

    // Register the JS->C++ message handler. Replaces any previous handler.
    virtual void set_js_message_handler(JsMessageHandler handler) = 0;

    // C++ -> JS: deliver a UTF-8 text message (telemetry JSON / control) to the
    // page. The page receives it via its script-message callback.
    virtual void post_text_to_js(const std::string& text) = 0;

    // C++ -> JS: deliver a binary display frame (already framed per the
    // protocol) to the page as an ArrayBuffer-equivalent payload.
    virtual void post_frame_to_js(const uint8_t* data, std::size_t len) = 0;

    // The loaded URL (for diagnostics/tests).
    virtual const std::string& loaded_url() const = 0;

    // Human-readable backend name ("stub", "webview2", ...). For diagnostics.
    virtual const char* backend_name() const = 0;
};

// Factory: returns the best available backend for this build/platform. When no
// concrete native backend is compiled in (the default), returns the portable
// StubWebViewHost so all callers build and link. Never returns nullptr.
std::unique_ptr<IWebViewHost> create_webview_host();

// -----------------------------------------------------------------------------
//  S760EditorController
// -----------------------------------------------------------------------------
//  Owns an IWebViewHost and binds it to a (borrowed) S760Bridge. This is the
//  single piece of logic every plugin format reuses; the format-specific glue
//  (IPlugView / effEditOpen / clap.gui) only forwards open/close/size/tick to
//  this controller. It wires the channel 1:1:
//
//    * JS -> C++ : webview JS messages are forwarded verbatim to
//                  S760Bridge::on_input() (a S760ClientMessage JSON string).
//    * C++ -> JS : the bridge's frame callback is posted via
//                  IWebViewHost::post_frame_to_js(), and the telemetry callback
//                  via IWebViewHost::post_text_to_js().
//
//  The controller does NOT own the bridge or the host's S760LibretroHost; the
//  plugin owns those and must outlive the controller's open editor.
// -----------------------------------------------------------------------------
class S760EditorController {
public:
    // `bridge` is borrowed and must outlive this controller. The webview host is
    // created lazily on open() via create_webview_host() unless one is injected
    // (the injecting ctor is used by tests to supply a StubWebViewHost).
    explicit S760EditorController(S760Bridge* bridge);
    S760EditorController(S760Bridge* bridge, std::unique_ptr<IWebViewHost> host);
    ~S760EditorController();

    S760EditorController(const S760EditorController&) = delete;
    S760EditorController& operator=(const S760EditorController&) = delete;

    // Open the editor into `parent` at `size`. Resolves the React app URL
    // (resolve_frontend_url()), creates the webview, installs the JS->C++ and
    // C++->JS bindings on the bridge, and pushes one initial frame. Returns true
    // on success. Safe no-op (returns true) if already open.
    bool open(NativeWindowHandle parent, const WebViewSize& size);

    // Close the editor: detaches the bridge callbacks and destroys the webview.
    // Idempotent.
    void close();

    bool is_open() const { return m_open; }

    // Forward a DAW resize to the webview.
    void set_size(const WebViewSize& size);
    WebViewSize size() const;

    // Per-frame pump: advance the bridge one tick (produces + posts the three
    // surfaces + telemetry to JS). Call from the UI timer while open.
    void tick();

    // The resolved file:// URL (or dev URL) of the built React app. Resolution
    // order: S760_UI_URL env override -> google-ui/dist/index.html located
    // relative to the loaded module / CWD -> a documented fallback. Exposed for
    // tests/diagnostics.
    static std::string resolve_frontend_url();

    // Accessors for tests / format glue.
    IWebViewHost* webview() { return m_host.get(); }
    S760Bridge*   bridge()  { return m_bridge; }

private:
    void install_bindings();
    void remove_bindings();

    S760Bridge*                  m_bridge = nullptr;
    std::unique_ptr<IWebViewHost> m_host;
    bool                         m_open = false;
    WebViewSize                  m_size;
};

} // namespace s760
