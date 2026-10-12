#include "s760/s760_webview_host.hpp"
#define NOMINMAX
#include <windows.h>
#include <wrl.h>
#include <WebView2.h>
#include <shlwapi.h>
#include <filesystem>
#include <vector>

namespace s760 {
using Microsoft::WRL::ComPtr;
using Microsoft::WRL::Callback;
namespace {
std::wstring wide(const std::string& s) {
    int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.data(),int(s.size()),nullptr,0);
    std::wstring r(n,L'\0');
    if(n) MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.data(),int(s.size()),r.data(),n);
    return r;
}
std::string narrow(const wchar_t* s) {
    if(!s) return {};
    int n=WideCharToMultiByte(CP_UTF8,0,s,-1,nullptr,0,nullptr,nullptr);
    std::string r(n,'\0');
    if(n) {WideCharToMultiByte(CP_UTF8,0,s,-1,r.data(),n,nullptr,nullptr);r.pop_back();}
    return r;
}
std::wstring document_url(std::wstring url) {
    const auto hash=url.find(L'#');
    if(hash!=std::wstring::npos) url.resize(hash);
    return url;
}
struct Page {
    bool alive=true, ready=false;
    HWND parent=nullptr;
    WebViewSize size;
    std::wstring url;
    IWebViewHost::JsMessageHandler handler;
    ComPtr<ICoreWebView2Controller> controller;
    ComPtr<ICoreWebView2> view;
    void bounds() {
        if(controller) {RECT r{0,0,LONG(size.width),LONG(size.height)};controller->put_Bounds(r);}
    }
    void close() {
        alive=false;ready=false;handler=nullptr;
        if(controller) controller->Close();
        view.Reset();controller.Reset();
    }
};
}

// All methods and COM callbacks run on the editor's STA/UI thread. Callbacks
// hold only weak state, so closing during asynchronous creation is safe.
class WebView2WebViewHost final : public IWebViewHost {
public:
    ~WebView2WebViewHost() override {destroy();}
    bool create(NativeWindowHandle parent,const WebViewSize& size,const std::string& url) override {
        destroy();
        if(!IsWindow(static_cast<HWND>(parent)) || !size.width || !size.height ||
            size.width>16384 || size.height>16384 || wide(url).empty()) return false;
        const auto hr=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
        if(FAILED(hr)) return false;
        com_=true;url_=url;size_=size;
        page_=std::make_shared<Page>();
        page_->parent=static_cast<HWND>(parent);page_->size=size;page_->url=wide(url);
        std::weak_ptr<Page> weak=page_;
        wchar_t temp[MAX_PATH];
        if(!GetTempPathW(MAX_PATH,temp)) {destroy();return false;}
        const auto profile=std::filesystem::path(temp)/L"S760-WebView2";
        auto result=CreateCoreWebView2EnvironmentWithOptions(nullptr,profile.c_str(),nullptr,
            Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
            [weak](HRESULT status,ICoreWebView2Environment* env)->HRESULT {
                auto p=weak.lock();if(!p || !p->alive) return S_OK;
                if(FAILED(status)||!env) {p->close();return S_OK;}
                const auto hr=env->CreateCoreWebView2Controller(p->parent,
                    Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                    [weak](HRESULT status,ICoreWebView2Controller* controller)->HRESULT {
                        auto p=weak.lock();
                        if(!p || !p->alive) {if(controller) controller->Close();return S_OK;}
                        if(FAILED(status)||!controller) {p->close();return S_OK;}
                        p->controller=controller;
                        if(FAILED(controller->get_CoreWebView2(&p->view))) {p->close();return S_OK;}
                        // Serve packaged ES modules from a local HTTPS origin. A raw
                        // file URL breaks root-relative assets and module CORS.
                        if(p->url.rfind(L"file:///",0)==0) {
                            wchar_t path[32768];DWORD count=32768;
                            ComPtr<ICoreWebView2_3> mapping;
                            if(FAILED(PathCreateFromUrlW(p->url.c_str(),path,&count,0)) ||
                                FAILED(p->view.As(&mapping))) {p->close();return S_OK;}
                            const std::filesystem::path file(path);
                            if(FAILED(mapping->SetVirtualHostNameToFolderMapping(L"s760.local",
                                file.parent_path().c_str(),COREWEBVIEW2_HOST_RESOURCE_ACCESS_KIND_DENY_CORS))) {
                                p->close();return S_OK;
                            }
                            p->url=L"https://s760.local/"+file.filename().wstring();
                        }
                        p->bounds();controller->put_IsVisible(TRUE);
                        EventRegistrationToken token;
                        p->view->add_NavigationStarting(Callback<ICoreWebView2NavigationStartingEventHandler>(
                            [weak](ICoreWebView2*,ICoreWebView2NavigationStartingEventArgs* args)->HRESULT {
                                auto p=weak.lock();LPWSTR uri=nullptr;args->get_Uri(&uri);
                                if(!p || !uri || document_url(uri)!=document_url(p->url)) args->put_Cancel(TRUE);
                                CoTaskMemFree(uri);return S_OK;
                            }).Get(),&token);
                        p->view->add_NewWindowRequested(Callback<ICoreWebView2NewWindowRequestedEventHandler>(
                            [](ICoreWebView2*,ICoreWebView2NewWindowRequestedEventArgs* args)->HRESULT {
                                args->put_Handled(TRUE);return S_OK;
                            }).Get(),&token);
                        p->view->add_WebMessageReceived(Callback<ICoreWebView2WebMessageReceivedEventHandler>(
                            [weak](ICoreWebView2*,ICoreWebView2WebMessageReceivedEventArgs* args)->HRESULT {
                                auto p=weak.lock();if(!p || !p->alive) return S_OK;
                                LPWSTR source=nullptr,message=nullptr;args->get_Source(&source);
                                if(source && document_url(source)==document_url(p->url) &&
                                    SUCCEEDED(args->TryGetWebMessageAsString(&message)) && message) {
                                    const auto text=narrow(message);
                                    if(text.size()<=65536 && p->handler) p->handler(text);
                                }
                                CoTaskMemFree(source);CoTaskMemFree(message);return S_OK;
                            }).Get(),&token);
                        p->view->add_NavigationCompleted(Callback<ICoreWebView2NavigationCompletedEventHandler>(
                            [weak](ICoreWebView2*,ICoreWebView2NavigationCompletedEventArgs* args)->HRESULT {
                                auto p=weak.lock();if(!p || !p->alive) return S_OK;
                                BOOL success=FALSE;args->get_IsSuccess(&success);p->ready=success;
                                return S_OK;
                            }).Get(),&token);
                        if(FAILED(p->view->Navigate(p->url.c_str()))) p->close();
                        return S_OK;
                    }).Get());
                if(FAILED(hr)) p->close();return S_OK;
            }).Get());
        if(FAILED(result)) {destroy();return false;}
        return true; // Request accepted; is_created() reports actual page readiness.
    }
    void destroy() override {
        if(page_) page_->close();page_.reset();
        if(com_) {CoUninitialize();com_=false;}
    }
    bool is_created() const override {return page_ && page_->alive && page_->ready;}
    void set_size(const WebViewSize& size) override {
        if(!size.width || !size.height || size.width>16384 || size.height>16384) return;
        size_=size;if(page_) {page_->size=size;page_->bounds();}
    }
    WebViewSize size() const override {return size_;}
    void set_js_message_handler(JsMessageHandler handler) override {if(page_) page_->handler=std::move(handler);}
    void post_text_to_js(const std::string& text) override {
        if(is_created() && text.size()<=65536) page_->view->PostWebMessageAsString(wide(text).c_str());
    }
    void post_frame_to_js(const uint8_t* data,std::size_t len) override {
        if(!is_created() || !data || len<6 || len>640*480*4+6) return;
        static const char alphabet[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        std::string out="{\"type\":\"S760_FRAME\",\"base64\":\"";
        out.reserve(40+(len+2)/3*4);
        for(std::size_t i=0;i<len;i+=3) {
            unsigned v=unsigned(data[i])<<16;
            if(i+1<len) v|=unsigned(data[i+1])<<8;if(i+2<len) v|=data[i+2];
            out+=alphabet[(v>>18)&63];out+=alphabet[(v>>12)&63];
            out+=i+1<len?alphabet[(v>>6)&63]:'=';out+=i+2<len?alphabet[v&63]:'=';
        }
        out+="\"}";page_->view->PostWebMessageAsJson(wide(out).c_str());
    }
    const std::string& loaded_url() const override {return url_;}
    const char* backend_name() const override {return "webview2";}
private:
    bool com_=false;
    std::shared_ptr<Page> page_;
    std::string url_;
    WebViewSize size_;
};
std::unique_ptr<IWebViewHost> try_create_webview2_host() {return std::make_unique<WebView2WebViewHost>();}
} // namespace s760
