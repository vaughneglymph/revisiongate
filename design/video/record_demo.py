"""Record the one-minute RevisionGate demo video.

What it records: the real app at http://127.0.0.1:8000 running the three-click
path on synthetic packet 01, in one continuous take with a live model call.
Captions sit in a strip under the app; nothing in the app itself is altered.

Run from the repo root:  python3 design/video/record_demo.py
Needs: the backend running on port 8000, and Playwright with Chromium.
Output: design/video/revisiongate-demo.webm (silent, captioned), beat screenshots,
and the packet the recorded run downloaded.
"""
import shutil
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000/"
OUT = Path(__file__).resolve().parent
W, H, STRIP = 1280, 720, 92
BEAT = 9.6  # seconds per beat; six beats plus load time stays near one minute

CAPTIONS = [
    ("The user", "An estimator at a small Michigan CNC shop opens the next RFQ."),
    ("The problem", "The RFQ asks for revision C in 6061-T6. The drawing says revision B in 7075-T6. No finish is stated."),
    ("Click 1 · Analyze packet", "Gemini on Vertex AI extracts each document's requirements. Fixed checks flag two conflicts and one missing requirement."),
    ("Click 2 · Review evidence", "Every finding opens beside its exact source lines. The estimator checks the meaning and edits the questions."),
    ("Click 3 · Approve clarification packet", "The questions download. The quote stays blocked until the customer answers."),
    ("The impact", "Pilot target: blocker review in five minutes instead of twenty. A target, not a measured result."),
]

OVERLAY = """
(strip => {
  document.documentElement.style.setProperty('--rg-height', `calc(100vh - ${strip}px)`);
  const bar = document.createElement('div');
  bar.style.cssText = `position:fixed;left:0;right:0;bottom:0;height:${strip}px;z-index:99999;background:#0c1726;color:#fff;display:flex;align-items:center;gap:22px;padding:0 28px;font-family:"Inter Variable",Inter,system-ui,sans-serif;border-top:3px solid #4fd1c5;box-sizing:border-box`;
  bar.innerHTML = '<div id="demo-beat" style="flex:none;width:176px;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#4fd1c5;line-height:1.4"></div>'
    + '<div id="demo-text" style="flex:1;font-size:21px;font-weight:600;line-height:1.3;letter-spacing:-.01em"></div>'
    + '<div style="flex:none;font-size:11px;font-weight:600;color:#b4c3d4;text-align:right;line-height:1.5">Synthetic packet<br>Live model call, one take</div>';
  document.body.appendChild(bar);
  const dot = document.createElement('div');
  dot.style.cssText = 'position:fixed;z-index:100000;width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;background:rgba(29,95,214,.25);border:2px solid #1d5fd6;pointer-events:none;left:-60px;top:-60px;transition:transform .12s';
  document.body.appendChild(dot);
  addEventListener('mousemove', e => { dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => { dot.style.transform = 'scale(.55)'; }, true);
  addEventListener('mouseup', () => { dot.style.transform = 'scale(1)'; }, true);
  window.__caption = (beat, text) => {
    document.getElementById('demo-beat').textContent = beat;
    document.getElementById('demo-text').textContent = text;
  };
})
"""


def main():
    tmp = Path(tempfile.mkdtemp(prefix="rg-demo-"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H}, device_scale_factor=2, color_scheme="light",
            record_video_dir=str(tmp), record_video_size={"width": 1920, "height": 1080}, accept_downloads=True,
        )
        page = context.new_page()
        page.on("download", lambda d: d.save_as(str(OUT / "demo-run-clarification.json")))
        page.goto(URL)
        page.wait_for_selector(".rg-line")           # packet list loaded, documents on screen
        page.evaluate(OVERLAY + f"({STRIP})")
        start = time.monotonic()
        clock = lambda: round(time.monotonic() - start, 1)

        def beat(index):
            target = start + index * BEAT
            while time.monotonic() < target:
                page.wait_for_timeout(100)
            page.evaluate("([b, t]) => window.__caption(b, t)", list(CAPTIONS[index]))
            print(f"beat {index + 1} at {clock()}s: {CAPTIONS[index][0]}", flush=True)

        def glide(locator, pause=600, dx=0.5, dy=0.5):
            box = locator.bounding_box()
            page.mouse.move(box["x"] + box["width"] * dx, box["y"] + box["height"] * dy, steps=22)
            page.wait_for_timeout(pause)

        def press(locator):
            glide(locator, 450)
            page.mouse.down(); page.wait_for_timeout(110); page.mouse.up()

        def shot(name):
            page.screenshot(path=str(OUT / f"beat-{name}.png"))

        ok = True
        try:
            # 1 The user
            beat(0)
            page.mouse.move(W / 2, H / 2)
            glide(page.locator(".rg-select select"), 1800)
            glide(page.locator(".rg-doc-head").first, 1500)
            shot("1-user")
            # 2 The problem
            beat(1)
            for ref in ("RFQ-L004", "RFQ-L005", "DRAWING-L003", "DRAWING-L004"):
                glide(page.locator(f'[id$="-line-{ref}"] .rg-line-body'), 1500, dx=0.3)
            shot("2-problem")
            # 3 Click 1
            beat(2)
            press(page.get_by_role("button", name="Analyze packet"))
            clicked = clock()
            page.wait_for_selector(".rg-finding", timeout=45000)
            print(f"analysis returned after {round(clock() - clicked, 1)}s", flush=True)
            glide(page.locator(".rg-versus").first, 1200)
            glide(page.locator(".rg-versus").nth(1), 1200)
            shot("3-analyze")
            # 4 Click 2
            beat(3)
            press(page.get_by_role("button", name="Review evidence"))
            page.wait_for_selector(".rg-passage")
            page.wait_for_timeout(900)
            page.evaluate("document.querySelector('.rg-review').scrollBy({ top: 250, behavior: 'smooth' })")
            page.wait_for_timeout(1300)
            glide(page.locator(".rg-passage").first, 900)
            box = page.locator(".rg-question textarea").first
            glide(box, 300, dx=0.6, dy=0.7)
            page.mouse.down(); page.mouse.up()
            box.evaluate("el => { el.focus(); el.setSelectionRange(el.value.length, el.value.length); }")
            page.keyboard.type(" Please reply before we estimate BRK-104.", delay=32)
            shot("4-review")
            # 5 Click 3
            beat(4)
            press(page.get_by_role("button", name="Approve clarification packet"))
            page.wait_for_selector(".rg-panel--ok", timeout=20000)
            page.wait_for_timeout(500)
            page.evaluate("document.querySelector('.rg-review').scrollTo({ top: 0, behavior: 'smooth' })")
            page.wait_for_timeout(1200)
            glide(page.locator(".rg-panel--ok h3"), 1800, dx=0.2)
            glide(page.locator(".rg-pill"), 1800)
            shot("5-approve")
            # 6 The impact
            beat(5)
            page.evaluate("document.querySelector('.rg-review').scrollTo({ top: 99999, behavior: 'smooth' })")
            page.wait_for_timeout(1300)
            press(page.locator(".rg-provenance:not(.rg-previous) summary"))
            page.wait_for_timeout(500)
            page.evaluate("document.querySelector('.rg-review').scrollTo({ top: 99999, behavior: 'smooth' })")
            page.wait_for_timeout(1200)
            shot("6-impact")
            while time.monotonic() < start + 6 * BEAT:
                page.wait_for_timeout(100)
            print(f"finished at {clock()}s; readiness label reads: {page.locator('.rg-pill').inner_text()}", flush=True)
        except Exception as exc:  # keep whatever was recorded so the failure can be seen
            ok = False
            shot("failure")
            print("RECORDING FAILED:", repr(exc), flush=True)
        finally:
            video = page.video
            context.close()
            browser.close()
            target = OUT / ("revisiongate-demo.webm" if ok else "revisiongate-demo-FAILED.webm")
            shutil.move(video.path(), target)
            shutil.rmtree(tmp, ignore_errors=True)
            print("wrote", target.name, target.stat().st_size, "bytes", flush=True)


if __name__ == "__main__":
    main()
