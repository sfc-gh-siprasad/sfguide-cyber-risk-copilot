"""Capture app screenshots for the landing page and the Snow Packs catalog card.

Runs the app in sample-data mode (no Snowflake account) in headless Chromium at a
fixed 1600x1000 viewport, so images are identical on any machine and contain no
account details.

    pip install playwright && python -m playwright install chromium
    python docs/capture_screenshots.py

Writes docs/images/<name>.png (2000x1250) and docs/images/card/<n>.jpg (960x600).
"""

import io
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
CARD = OUT / "card"
PORT = 8599
URL = f"http://127.0.0.1:{PORT}"
VIEWPORT = {"width": 1600, "height": 1000}


def wait_for_server(timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(URL, timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Streamlit did not start")


def settle(page):
    page.wait_for_selector('[data-testid="stApp"]', timeout=60000)
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=60000)
    page.wait_for_timeout(1500)


def shoot(page, name):
    OUT.mkdir(parents=True, exist_ok=True)
    CARD.mkdir(parents=True, exist_ok=True)
    png = page.screenshot(type="png")
    (OUT / f"{name}.png").write_bytes(png)
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(png)).convert("RGB").resize((960, 600), Image.LANCZOS)
        img.save(CARD / f"{name}.jpg", "JPEG", quality=82, optimize=True)
    except ImportError:
        print("Pillow not installed; skipped card image for", name)


def ask(page, question):
    page.get_by_role("button", name=question).click()
    page.get_by_text("Sample AI response", exact=True).first.wait_for(timeout=30000)
    page.wait_for_timeout(1000)


def main():
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "streamlit_app.py"),
         "--server.port", str(PORT), "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env={**__import__("os").environ,
                                                                            "CYBER_COPILOT_MODE": "mock"})
    try:
        wait_for_server()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1.25, locale="en-US",
                                      timezone_id="UTC", color_scheme="light")
            page = ctx.new_page()

            page.goto(URL)
            settle(page)
            shoot(page, "overview")

            page.goto(f"{URL}/drill_down")
            settle(page)
            shoot(page, "services")

            page.goto(f"{URL}/copilot")
            settle(page)
            ask(page, "Which Tier 1 services have the most open critical findings?")
            page.get_by_test_id("stChatInput").locator("textarea").fill(
                "What does policy say about remediation deadlines for known exploited findings?")
            page.keyboard.press("Enter")
            page.get_by_text("Policy sources").wait_for(timeout=30000)
            page.wait_for_timeout(1500)
            shoot(page, "copilot")
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=20)
    print("Wrote", sorted(str(f.relative_to(ROOT)) for f in OUT.rglob("*") if f.is_file()))


if __name__ == "__main__":
    main()
