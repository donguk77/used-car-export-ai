"""scripts/capture_autobell.py — Autobell Global 라이브 멀티 캡처.

핵심: autobellglobal.com 의 메인 페이지가 single-page 라 /usedcar, /about
같은 직접 URL 은 404 / 점검 페이지로 떨어진다. 그래서 메인 페이지를
스크롤 위치별로 잘라서 섹션마다 1장씩 viewport 캡처 + 메뉴 클릭으로
실제 inventory 페이지 진입 시도.

생성 파일 (demo_captures/):
  - competitor_autobell.png               (메인 hero, viewport)
  - competitor_autobell_full.png          (메인 풀페이지 — 모든 섹션 1장)
  - competitor_autobell_section2.png      (Special used cars)
  - competitor_autobell_section3.png      (About Autobell + Most popular)
  - competitor_autobell_section4.png      (Reviews + Learn More)
  - competitor_autobell_inventory.png     (Used Car 메뉴 클릭 진입)
"""
from __future__ import annotations
from pathlib import Path

from playwright.sync_api import sync_playwright

CAPS = Path(__file__).resolve().parent.parent / "demo_captures"
CAPS.mkdir(exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
MAIN = "https://www.autobellglobal.com/"


def dismiss_modals(page) -> None:
    for sel in [
        'button[aria-label*="close" i]',
        'button:has-text("Don\'t show")',
        'button:has-text("Close")',
        'button:has-text("CLOSE")',
        'button:has-text("닫기")',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=400):
                loc.click(timeout=2000)
                page.wait_for_timeout(500)
                break
        except Exception:
            continue
    for _ in range(2):
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)


def load_full(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)
    dismiss_modals(page)
    # lazy-load 트리거: 끝까지 스크롤 후 top 복귀
    try:
        page.evaluate(
            "() => new Promise(r => {"
            " let y=0; const step=()=>{ window.scrollBy(0,800); y+=800;"
            " if (y < document.body.scrollHeight) setTimeout(step,180);"
            " else { setTimeout(r,800); } }; step(); })"
        )
    except Exception:
        pass
    page.wait_for_timeout(1500)


def shot(page, name: str, full_page: bool = False) -> None:
    out = CAPS / name
    page.screenshot(path=str(out), full_page=full_page, type="png", timeout=60000)
    kb = out.stat().st_size // 1024
    print(f"    OK {name} ({kb} KB)")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=UA,
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        page = ctx.new_page()

        # ── 1) 메인 페이지 풀 로딩 후 섹션별 viewport 캡처 ───────
        print(f"[*] LOAD {MAIN}")
        load_full(page, MAIN)

        # scroll 0 — hero
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        shot(page, "competitor_autobell.png")

        # 풀페이지 (모든 섹션) — 참고용
        shot(page, "competitor_autobell_full.png", full_page=True)

        # 페이지 총 높이 측정 → 4구간으로 나눠 캡처
        try:
            total_h = page.evaluate("document.body.scrollHeight")
        except Exception:
            total_h = 4000
        vp_h = 900
        # 균등 분할: hero(0), 1/3, 2/3, footer-1
        for idx, ratio in enumerate([0.25, 0.50, 0.78], start=2):
            y = max(0, int(total_h * ratio) - vp_h // 2)
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(900)
            shot(page, f"competitor_autobell_section{idx}.png")

        # ── 2) Used Car 메뉴 클릭으로 실제 inventory 진입 시도 ──
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        clicked = False
        for sel in [
            'a:has-text("Used Car")',
            'a:has-text("USED CAR")',
            'a:has-text("Used Car Inventory")',
            'a[href*="usedcar" i]',
            'a[href*="inventory" i]',
        ]:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=600):
                    print(f"[*] CLICK Used Car via: {sel}")
                    loc.click(timeout=3000)
                    page.wait_for_timeout(5000)
                    dismiss_modals(page)
                    shot(page, "competitor_autobell_inventory.png")
                    clicked = True
                    break
            except Exception as e:
                continue
        if not clicked:
            print("[!] Used Car 메뉴 클릭 진입 실패 — inventory 캡처 skip")

        browser.close()


if __name__ == "__main__":
    main()
