"""
capture_ui_screenshot.py — Capture pixel-perfect high-DPI screenshot of Google UI for README
"""
import subprocess
import time
import os
import sys
from playwright.sync_api import sync_playwright

def main():
    google_ui_dir = os.path.abspath("google-ui")
    target_path = os.path.abspath("Main.png")
    
    # 1. Start Vite preview server
    server_proc = subprocess.Popen(
        ["npx.cmd", "vite", "preview", "--port", "3145", "--host", "127.0.0.1"],
        cwd=google_ui_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(2)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # 1540x950 with 2x device scale factor for ultra-sharp crisp screenshot
            context = browser.new_context(
                viewport={"width": 1540, "height": 950},
                device_scale_factor=2.0
            )
            page = context.new_page()
            page.goto("http://127.0.0.1:3145", wait_until="networkidle")
            
            # Wait for canvas elements to render
            page.wait_for_timeout(1000)
            
            # Select the main studio container (CRT Monitor + 1U Rack)
            main_el = page.query_selector("main")
            
            if main_el:
                img_data = main_el.screenshot()
            else:
                img_data = page.screenshot()
                
            with open(target_path, "wb") as f:
                f.write(img_data)
                
            print(f"[SUCCESS] Captured screenshot to {target_path} ({len(img_data)} bytes)")
            browser.close()
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=2)
        except Exception:
            server_proc.kill()

if __name__ == "__main__":
    main()
