"""Draws the sizing curve (expected score against communication range) from linkloss/results/*.csv as an SVG.

Usage, from fleet-kit/: python3 -m linkloss.plot [--slow 0.1] [--msgs 3] [--dir linkloss/results]
"""
import argparse
import csv
import os

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLORS = {(0, 0.0): "#c0392b", (0, 0.3): "#e6a39b", (2, 0.0): "#1f6fb2", (2, 0.3): "#9cc3e6"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slow", type=float, default=0.1)
    ap.add_argument("--msgs", type=int, default=3)
    ap.add_argument("--dir", default=os.path.join(KIT, "linkloss", "results"))
    args = ap.parse_args()
    with open(os.path.join(args.dir, "sizing.csv")) as f:
        rows = [r for r in csv.DictReader(f) if float(r["slow"]) == args.slow and int(r["max_msgs"]) == args.msgs]
    with open(os.path.join(args.dir, "robustness.csv")) as f:
        cont = {int(r["margin"]): float(r["expected_score"]) for r in csv.DictReader(f)
                if float(r["slow"]) == args.slow and r["policy"] == "continue"}
    ranges = sorted({float(r["range_m"]) for r in rows})
    ys = [float(r["expected_score"]) for r in rows] + list(cont.values())
    lo, hi = min(ys) - 10, max(ys) + 10
    w, h, ml, mr, mt, mb = 700, 380, 64, 210, 36, 56
    px = lambda i: ml + (w - ml - mr) * i / (len(ranges) - 1)
    py = lambda v: mt + (h - mt - mb) * (1 - (v - lo) / (hi - lo))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="sans-serif" font-size="12">' % (w, h),
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="%d" y="20" font-size="14" font-weight="bold">Score attendu sous dérive (ralentissement max %.0f %%, %d messages max)</text>'
           % (ml, args.slow * 100, args.msgs)]
    for i, rg in enumerate(ranges):
        out.append('<text x="%.1f" y="%d" text-anchor="middle">%g m</text>' % (px(i), h - mb + 18, rg))
    out.append('<text x="%d" y="%d" text-anchor="middle">portée de diffusion</text>' % ((ml + w - mr) // 2, h - 12))
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#ddd"/>' % (ml, w - mr, py(v), py(v)))
        out.append('<text x="%d" y="%.1f" text-anchor="end">%.0f</text>' % (ml - 6, py(v) + 4, v))
    for margin in (0, 2):
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s" stroke-dasharray="4 3"/>'
                   % (ml, w - mr, py(cont[margin]), py(cont[margin]), COLORS[(margin, 0.0)]))
    ly = mt + 6
    for (margin, loss), col in COLORS.items():
        pts = [(px(i), py(float(r["expected_score"]))) for i, rg in enumerate(ranges) for r in rows
               if int(r["margin"]) == margin and float(r["loss"]) == loss and float(r["range_m"]) == rg]
        out.append('<polyline fill="none" stroke="%s" stroke-width="2.5" points="%s"/>' % (col, " ".join("%.1f,%.1f" % p for p in pts)))
        out.append('<rect x="%d" y="%d" width="14" height="4" fill="%s"/><text x="%d" y="%d">marge %d, pertes %.0f %%</text>'
                   % (w - mr + 10, ly, col, w - mr + 30, ly + 6, margin, loss * 100))
        ly += 20
    out.append('<text x="%d" y="%d" fill="#555">pointillés : sans radio (continue)</text>' % (w - mr + 10, ly + 8))
    out.append("</svg>")
    target = os.path.join(args.dir, "sizing.svg")
    with open(target, "w") as f:
        f.write("\n".join(out))
    print("written", target)


if __name__ == "__main__":
    main()
