"""Report line counts per cantica/canto for both source JSON files and flag oddities.

Every canto is written in terza rima, so its line count should be 3k+1.
Longfellow translated line for line, so per-canto counts should also agree
between the two files (we compare counts only; the texts are never aligned).
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {"Petrocchi (it)": "data/petrocchi.json", "Longfellow (en)": "data/longfellow.json"}
EXPECTED_CANTOS = {"Inferno": 34, "Purgatorio": 33, "Paradiso": 33}


def counts(path):
    recs = json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
    c = collections.OrderedDict()
    for r in recs:
        c[(r["cantica"], r["canto"])] = c.get((r["cantica"], r["canto"]), 0) + 1
    return recs, c


def main():
    per = {}
    for label, path in FILES.items():
        recs, c = counts(path)
        per[label] = c
        print("==", label, "total", len(recs))
        for cantica, ncanti in EXPECTED_CANTOS.items():
            cantos = [k for k in c if k[0] == cantica]
            print("  %-10s %5d lines, %d cantos" % (cantica, sum(c[k] for k in cantos), len(cantos)))
            if len(cantos) != ncanti:
                print("    FLAG: expected %d cantos" % ncanti)
        for (cantica, canto), v in c.items():
            if v % 3 != 1:
                print("    FLAG: %s %d has %d lines (not 3k+1)" % (cantica, canto, v))
        # line numbers contiguous from 1
        seen = collections.defaultdict(list)
        for r in recs:
            seen[(r["cantica"], r["canto"])].append(r["line_number"])
        for k, nums in seen.items():
            if nums != list(range(1, len(nums) + 1)):
                print("    FLAG: %s %d numbering not contiguous" % k)
    it, en = per["Petrocchi (it)"], per["Longfellow (en)"]
    diffs = [(k, it.get(k), en.get(k)) for k in it if it.get(k) != en.get(k)]
    print("== cantos where the two texts differ in length:", len(diffs))
    for k, a, b in diffs:
        print("   %s %d: it=%s en=%s" % (k[0], k[1], a, b))


if __name__ == "__main__":
    main()
