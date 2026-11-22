"""Re-renders the deck's screenshots from the demo pages at the scripted moments, with headless Chrome.

    python3 tools/make_stills.py                  # demo-pages/ -> stills/  (macOS: Chrome + sips)

Run from demo/pitch/. Each page is copied to out/stills_src/ with a small script that sets the moment (Layers tab,
link-loss replay at t = 645 s, Why cards C35 and C27), then screenshotted at 3200x1800 and cropped. The demo pages
themselves are not changed. If a page is rebuilt with a different plan, check the crops by eye: they assume this plan.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HELP = """function byText(sel, re){return [...document.querySelectorAll(sel)].find(e=>re.test((e.textContent||'').trim()));}
function key(k, shift){document.dispatchEvent(new KeyboardEvent('keydown',{key:k,shiftKey:!!shift,bubbles:true}));}"""
JOBS = {  # name: (page, script that sets the moment)
    "greedy": ("view_greedy.html", ""),
    "ours": ("view_ours.html", "setTimeout(()=>{byText('button,div,span',/^LAYERS$/i)?.click();},300);"),
    "linkloss": ("view_linkloss.html",
                 "setTimeout(()=>{byText('button,div,span',/^LINK$/i)?.click();},300);"
                 "setTimeout(()=>{document.querySelector('.issue[data-t=\"618\"]')?.click();},600);"
                 "setTimeout(()=>{key('ArrowRight',true);key('ArrowRight',true);key('ArrowRight',true);},900);"),
    "c35": ("view_ops.html", "setTimeout(()=>{byText('button,div,span',/^WHY$/i)?.click();},300);"
                             "setTimeout(()=>{document.querySelector('#ccard').parentElement"
                             ".querySelector('tr[data-c=\"C35\"]').click();},700);"),
    "c27": ("view_ops.html", "setTimeout(()=>{byText('button,div,span',/^WHY$/i)?.click();},300);"
                             "setTimeout(()=>{document.querySelector('#ccard').parentElement"
                             ".querySelector('tr[data-c=\"C27\"]').click();},700);"),
}
CROPS = {  # output: (source screenshot, height, width, offset y, offset x) in 3200x1800 pixels
    "c35_card": ("c35", 800, 700, 860, 2490),
    "c27_card": ("c27", 330, 700, 860, 2490),
    "hold_zoom": ("linkloss", 640, 760, 660, 720),
}


def main():
    src = os.path.join(HERE, "out", "stills_src")
    os.makedirs(src, exist_ok=True)
    stills = os.path.join(HERE, "stills")
    for name, (page, js) in JOBS.items():
        html = open(os.path.join(HERE, "demo-pages", page), encoding="utf-8").read()
        i = html.rfind("</body>")
        inj = f"<script>{HELP}{js}</script>"
        html = html[:i] + inj + html[i:] if i >= 0 else html + inj
        copy = os.path.join(src, name + ".html")
        open(copy, "w", encoding="utf-8").write(html)
        png = os.path.join(src, name + ".png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1600,900",
                        "--user-data-dir=" + os.path.join(HERE, "out", "chrome"),  # never the user's own profile
                        "--force-device-scale-factor=2", "--virtual-time-budget=4000", f"--screenshot={png}",
                        "file://" + copy], check=True, capture_output=True)
        assert os.path.getsize(png) > 0, f"{name}: empty screenshot"
    for name in ("greedy", "ours", "linkloss"):
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82", os.path.join(src, name + ".png"),
                        "--out", os.path.join(stills, name + ".jpg")], check=True, capture_output=True)
    for out, (name, h, w, y, x) in CROPS.items():
        tmp = os.path.join(src, out + ".png")
        subprocess.run(["sips", "-c", str(h), str(w), "--cropOffset", str(y), str(x), os.path.join(src, name + ".png"),
                        "--out", tmp], check=True, capture_output=True)
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88", tmp,
                        "--out", os.path.join(stills, out + ".jpg")], check=True, capture_output=True)
    print("stills/ rewritten: check them by eye, then upload them to the deck to replace the old images")


if __name__ == "__main__":
    main()
