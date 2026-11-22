"""Renders the deck's slide sources into one local HTML page, and optionally a PNG, to check layouts offline.

    python3 tools/preview_deck.py                 # writes out/deck_preview.html
    python3 tools/preview_deck.py --png           # also out/deck_preview.png (needs Google Chrome)

Run from demo/pitch/. Slides are 1920x1080, stacked in deck.json order; uploaded images (/_blob/<id>) are mapped to
the local files in stills/ through deck/assets.json. Fonts come from Google Fonts, so text wraps as in the live deck
only when online. Standard library only.
"""
import argparse
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_CSS = """* { margin: 0 } body { font: 32px/1.2 sans-serif }
body > section { width: 1920px !important; height: 1080px !important; overflow: hidden !important;
  box-sizing: border-box !important; position: relative; isolation: isolate }
aside { display: none !important }
table { width: 100%; border-collapse: separate; border-spacing: 0 }
th, td { padding: .35em .6em; text-align: left }"""


def build(out_html):
    deck = json.load(open(os.path.join(HERE, "deck", "deck.json"), encoding="utf-8"))
    assets = json.load(open(os.path.join(HERE, "deck", "assets.json"), encoding="utf-8"))
    body = ""
    for sid in deck["order"]:
        s = open(os.path.join(HERE, "deck", "slides", sid + ".html"), encoding="utf-8").read()
        for blob in re.findall(r"/_blob/([0-9a-f]{32})", s):
            assert blob in assets, f"{sid}: image {blob} has no local file in deck/assets.json"
            s = s.replace("/_blob/" + blob, "file://" + os.path.join(HERE, "stills", assets[blob]))
        body += s
    links = "".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in deck["faces"].values() if "href" in f)
    css = "file://" + os.path.join(HERE, "deck", "deck.css")
    page = (f"<!doctype html><html><head><meta charset=utf-8>{links}<style>{BASE_CSS}</style>"
            f"<link rel=stylesheet href='{css}'></head><body>{body}</body></html>")
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    open(out_html, "w", encoding="utf-8").write(page)
    return len(deck["order"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--png", action="store_true", help="also screenshot every slide into one tall PNG (half size)")
    args = ap.parse_args()
    out_html = os.path.join(HERE, "out", "deck_preview.html")
    n = build(out_html)
    print(f"{n} slides -> {out_html}")
    if args.png:
        png = os.path.join(HERE, "out", "deck_preview.png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--user-data-dir=" + os.path.join(HERE, "out", "chrome"),  # never the user's own profile
                        f"--window-size=1920,{1080 * n}", "--force-device-scale-factor=0.5",
                        "--virtual-time-budget=6000", f"--screenshot={png}", "file://" + out_html],
                       check=True, capture_output=True)
        assert os.path.getsize(png) > 0, "Chrome wrote an empty screenshot"
        print(f"-> {png}")


if __name__ == "__main__":
    main()
