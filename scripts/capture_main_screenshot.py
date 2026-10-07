import subprocess
import time
import http.server
import socketserver
import threading
import os
import sys
from playwright.sync_api import sync_playwright

DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "google-ui", "dist"))
OUTPUT_PNG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Main.png"))
PORT = 8999

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

def main():
    print(f"Serving {DIST_DIR} on port {PORT}...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    print("Launching headless browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2
        )
        page = context.new_page()
        page.goto(f"http://localhost:{PORT}")
        
        # Wait for canvas to render
        page.wait_for_selector("canvas", timeout=10000)
        time.sleep(2) # Allow fonts and canvas effects to paint

        # Locate the main emulator studio container or take full page screenshot
        app_container = page.locator("body > div#root")
        if app_container.count() > 0:
            print("Capturing studio layout screenshot...")
            app_container.first.screenshot(path=OUTPUT_PNG)
        else:
            page.screenshot(path=OUTPUT_PNG, full_page=True)
        
        browser.close()

    print(f"Screenshot saved successfully to {OUTPUT_PNG}")

if __name__ == "__main__":
    main()
