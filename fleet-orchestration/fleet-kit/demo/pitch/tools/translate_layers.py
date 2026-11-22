"""Turns the French layer names of a swann_demo.py page into English, in place.

    python3 tools/translate_layers.py demo-pages/view_ours.html

swann_demo.py writes "Gagnés vs glouton", "Bloqués", ... into the page's data. The live demo copy was translated with
this, after `python3 demo/swann_demo.py scenario.json plan.json -o out` (out/view.html = view_ours.html).
"""
import json
import sys

PAIRS = {
    "Notre plan face au glouton": "Ours vs kit greedy",
    "Gagnés vs glouton": "Won vs greedy",
    "Perdus vs glouton": "Lost vs greedy",
    "À gagner": "Still winnable",
    "Concurrence ressources": "Resource conflict",
    "Bloqués (R7 ou hors de portée)": "Blocked (R7 or out of reach)",
    "Routes du glouton": "Greedy routes",
}
LABELS = {' bloqu\\u00e9"': ' blocked"', ' en concurrence"': ' resource conflict"', ' \\u00e0 gagner"': ' winnable"'}


def main():
    path = sys.argv[1]
    s = open(path, encoding="utf-8").read()
    n = 0
    for fr, en in PAIRS.items():  # plain text and the JSON-escaped form both appear in the page
        for a, b in ((fr, en), (json.dumps(fr)[1:-1], json.dumps(en)[1:-1])):
            n += s.count(a)
            s = s.replace(a, b)
    for a, b in LABELS.items():
        n += s.count(a)
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)
    print(f"{n} replacements in {path}")


if __name__ == "__main__":
    main()
