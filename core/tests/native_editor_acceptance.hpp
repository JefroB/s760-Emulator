// Windows WebView2 + built React + native plugin engine acceptance. The audio
// test thread never pumps UI messages; the editor owns a separate STA thread.
#define NOMINMAX
#include <windows.h>
#include <atomic>
#include "s760/s760_webview_host.hpp"

class NativeEditorAcceptance {
public:
    std::atomic<unsigned> phase{0}, verified{0};
    std::atomic<bool> stop{false}, failed{false};
    std::thread ui;
    NativeEditorAcceptance(s760::S760Bridge& bridge,const std::filesystem::path& root,
                           const std::filesystem::path& state) {
        const auto folder=state/"editor-ui";
        std::filesystem::create_directories(folder);
        std::filesystem::copy(root/"google-ui/dist",folder,
            std::filesystem::copy_options::recursive|std::filesystem::copy_options::overwrite_existing);
        std::ofstream page(folder/"index.html",std::ios::app);
        page<<R"(<script>
          let checked=false;
          chrome.webview.addEventListener('message',e=>{
            if(checked || e.data?.type!=='S760_FRAME') return;
            const bytes=atob(e.data.base64);
            if(bytes.length!==1228806 || bytes.charCodeAt(0)!==0) return;
            requestAnimationFrame(()=>{
              const canvases=[...document.querySelectorAll('canvas')].filter(c=>c.width===640&&c.height===480);
              const canvas=canvases.at(-1);if(!canvas) return;
              const rgba=canvas.getContext('2d').getImageData(0,0,640,480).data;
              let lit=0;
              for(let i=0;i<rgba.length;i+=4004) {
                for(let c=0;c<4;c++) if(rgba[i+c]!==bytes.charCodeAt(i+c+6)) return;
                if(rgba[i]||rgba[i+1]||rgba[i+2])lit++;
              }
              if(lit>20) {checked=true;chrome.webview.postMessage('S760_TEST_PIXELS');}
            });
          });
        </script>)";
        page.close();
        const auto url="file:///"+(folder/"index.html").generic_string();
        _putenv_s("S760_UI_URL",url.c_str());
        ui=std::thread([this,&bridge] {
            HWND window=CreateWindowExW(0,L"STATIC",L"Native editor acceptance",WS_OVERLAPPEDWINDOW,
                0,0,1440,1100,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);
            s760::S760EditorController editor(&bridge);
            unsigned observed=99;
            while(!stop) {
                const auto desired=phase.load();
                if(desired!=observed) {
                    editor.close();observed=desired;
                    if(desired!=1) {
                        if(!window || !editor.open(window,{1440,1100})) {failed=true;break;}
                        editor.webview()->set_js_message_handler([this,&bridge,desired](const std::string& message){
                            if(message=="S760_TEST_PIXELS") verified.fetch_or(desired==0?1:2);
                            else bridge.on_input(message);
                        });
                    }
                }
                MSG msg;
                while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)) {TranslateMessage(&msg);DispatchMessageW(&msg);}
                std::this_thread::sleep_for(std::chrono::milliseconds(2));
            }
            editor.close();if(window) DestroyWindow(window);
        });
    }
    ~NativeEditorAcceptance(){finish();}
    void finish(){stop=true;if(ui.joinable()) ui.join();_putenv_s("S760_UI_URL","");}
};
