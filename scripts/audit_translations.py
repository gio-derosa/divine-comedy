"""Heuristic content audit of translations in data/work (run after check_translations.py).

The checker proves numbering is right; this looks for translations that sit on
the wrong line (shifted by one) or are otherwise suspicious:
  - name/number mismatch: a capitalized name or number in the source line is
    missing from its translation but present in a neighbour's translation
  - identical translation on two consecutive lines
  - length ratio far outside the norm for that slice
"""
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(slice_name, canto_file):
    src = json.load(open(os.path.join(ROOT, "data", "slices", slice_name, canto_file), encoding="utf-8"))
    path = os.path.join(ROOT, "data", "work", slice_name, canto_file.replace(".json", ".txt"))
    with open(path, encoding="utf-8-sig") as f:
        tr = {int(n): t.strip() for n, t in (l.split("|") for l in f.read().splitlines() if l.strip())}
    return [(r["line_number"], r["text"], tr[r["line_number"]]) for r in src]


def fold(s):
    return re.sub(r"[̀-ͯ]", "", __import__("unicodedata").normalize("NFD", s)).lower()


def names(text):
    """Capitalized words not at the start of the line (likely proper nouns)."""
    words = re.findall(r"[A-Za-zÀ-ÿ’']+", text)
    return {fold(w) for w in words[1:] if w[0].isupper() and len(w) > 3}


def audit(slice_name):
    flags = []
    d = os.path.join(ROOT, "data", "slices", slice_name)
    rows = []
    for canto_file in sorted(os.listdir(d)):
        canto = int(canto_file[6:8])
        rows.extend((canto,) + r for r in load(slice_name, canto_file))
    ratios = [len(t) / max(len(s), 1) for _, _, s, t in rows]
    mu, sd = statistics.mean(ratios), statistics.pstdev(ratios)
    for i, (canto, n, s, t) in enumerate(rows):
        tf = fold(t)
        prev_t = rows[i - 1][3] if i and rows[i - 1][0] == canto else ""
        next_t = rows[i + 1][3] if i + 1 < len(rows) and rows[i + 1][0] == canto else ""
        for name in names(s):
            stem = name[:5]
            if stem not in tf and (stem in fold(prev_t) or stem in fold(next_t)):
                flags.append((canto, n, "name '%s' found on neighbouring line" % name, s, t))
        if prev_t and t == prev_t:
            flags.append((canto, n, "same translation as previous line", s, t))
        r = len(t) / max(len(s), 1)
        if abs(r - mu) > 4 * sd:
            flags.append((canto, n, "length ratio %.2f (mean %.2f)" % (r, mu), s, t))
    return flags


def main():
    names_ = sys.argv[1:] or sorted(os.listdir(os.path.join(ROOT, "data", "slices")))
    for name in names_:
        flags = audit(name)
        print("== %s: %d flags" % (name, len(flags)))
        for canto, n, why, s, t in flags:
            print("  %2d.%-3d %s\n      src: %s\n      tr:  %s" % (canto, n, why, s, t))


if __name__ == "__main__":
    main()
