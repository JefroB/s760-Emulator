// Real WebView2 runtime acceptance; no simulated browser or DAW claims.
#include "s760/s760_webview_host.hpp"
#define NOMINMAX
#include <windows.h>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>

bool pump_until(const std::function<bool()>& done) {
    const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(20);
    while(std::chrono::steady_clock::now()<end) {
        MSG msg;
        while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)) {TranslateMessage(&msg);DispatchMessageW(&msg);}
        if(done()) return true;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    return false;
}
int main(int argc,char** argv) {
    if(argc!=2) {std::cerr<<"usage: s760_webview2_tests <existing scratch directory>\n";return 2;}
    auto file=std::filesystem::absolute(std::filesystem::path(argv[1])/"webview2-channel.html");
    std::ofstream html(file);
    html<<R"(<html><body>WebView2 channel test<script>
      chrome.webview.addEventListener('message',e=>{
        if(e.data==='ping') chrome.webview.postMessage('pong');
        if(e.data==='size') chrome.webview.postMessage('size:'+innerWidth+':'+innerHeight);
        if(e.data?.type==='S760_FRAME') {
          const b=atob(e.data.base64);
          if(b.length===7 && b.charCodeAt(6)===129) chrome.webview.postMessage('frame-ok');
          if(b.length===1228806) chrome.webview.postMessage('stream-frame');
        }
      });
    </script></body></html>)";
    html.close();
    std::string url="file:///"+file.generic_string();
    HWND window=CreateWindowExW(0,L"STATIC",L"S760 WebView acceptance",WS_OVERLAPPEDWINDOW,
        0,0,1024,768,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);
    if(!window) return 3;
    auto host=s760::create_webview_host();
    if(std::string(host->backend_name())!="webview2") return 4;
    if(host->create(nullptr,{640,480},url)) return 5;
    // Cancel pending initialization, then reopen the same host twice.
    if(!host->create(window,{640,480},url)) return 6;
    host->destroy();
    for(int pass=0;pass<2;++pass) {
        std::string received;
        if(!host->create(window,{640,480},url)) return 7;
        host->set_js_message_handler([&](const std::string& s){received=s;});
        if(!pump_until([&]{return host->is_created();})) {std::cerr<<"page never ready\n";return 8;}
        host->post_text_to_js("ping");
        if(!pump_until([&]{return received=="pong";})) return 9;
        const uint8_t frame[]{1,8,0,1,0,1,129};
        host->post_frame_to_js(frame,sizeof(frame));
        if(!pump_until([&]{return received=="frame-ok";})) return 10;
        host->set_size({800,600});
        if(!pump_until([&]{host->post_text_to_js("size");return received=="size:800:600";})) {
            std::cerr<<"resize: "<<received<<"\n";return 11;
        }
        host->destroy();host->destroy();
        if(host->is_created()) return 12;
    }
    // The editor must schedule frames itself. Generic IPlugView hosts have no
    // private tick entry point. This checks scheduling, not native audio parity.
    _putenv_s("S760_UI_URL",url.c_str());
    s760::S760Bridge bridge(nullptr);
    s760::S760EditorController editor(&bridge);
    for(int pass=0;pass<2;++pass) {
        int frames=0;
        if(!editor.open(window,{640,480})) return 13;
        editor.webview()->set_js_message_handler([&](const std::string& text){if(text=="stream-frame") ++frames;});
        if(!pump_until([&]{return frames>=3;})) {std::cerr<<"no automatic frames\n";return 14;}
        editor.close();
        const int closed_frames=frames;
        const auto until=std::chrono::steady_clock::now()+std::chrono::milliseconds(250);
        pump_until([&]{return std::chrono::steady_clock::now()>=until;});
        if(frames!=closed_frames) return 15;
    }
    _putenv_s("S760_UI_URL","");
    DestroyWindow(window);
    std::cout<<"PASS: real WebView2 text/frame roundtrip, resize, cancellation, reopen and automatic editor frames\n";
    return 0;
}
