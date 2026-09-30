"""Verify translation output for one slice, e.g. `python scripts/check_translations.py it_inferno`.

Each canto's output is data/work/<slice>/canto_NN.txt with one line per source
line: "<line_number>|<translation>" (no source text contains "|"). A canto passes when every source line_number
appears exactly once, in order, with a non-empty translation and nothing extra.
Prints one line per failing canto and exits non-zero if any fail.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_canto(slice_name, canto_file):
    src = json.load(open(os.path.join(ROOT, "data", "slices", slice_name, canto_file), encoding="utf-8"))
    expected = [r["line_number"] for r in src]
    out_path = os.path.join(ROOT, "data", "work", slice_name, canto_file.replace(".json", ".txt"))
    if not os.path.exists(out_path):
        return "missing output file"
    got, problems = [], []
    with open(out_path, encoding="utf-8-sig") as f:
        for i, raw in enumerate(f.read().splitlines(), 1):
            if not raw.strip():
                continue
            parts = raw.split("|")
            if len(parts) != 2 or not parts[0].strip().isdigit():
                problems.append("bad row %d: %r" % (i, raw[:60]))
                continue
            if not parts[1].strip():
                problems.append("empty translation for line %s" % parts[0])
            got.append(int(parts[0]))
    if got != expected:
        missing = sorted(set(expected) - set(got))
        extra = sorted(set(got) - set(expected))
        dupes = sorted({n for n in got if got.count(n) > 1})
        problems.append("expected %d rows, got %d; missing=%s extra=%s dupes=%s"
                        % (len(expected), len(got), missing[:10], extra[:10], dupes[:10]))
    return "; ".join(problems[:5])


def check_slice(slice_name):
    d = os.path.join(ROOT, "data", "slices", slice_name)
    failures = {}
    for canto_file in sorted(os.listdir(d)):
        err = check_canto(slice_name, canto_file)
        if err:
            failures[canto_file] = err
    return failures


def main():
    names = sys.argv[1:] or sorted(os.listdir(os.path.join(ROOT, "data", "slices")))
    bad = 0
    for name in names:
        failures = check_slice(name)
        total = len(os.listdir(os.path.join(ROOT, "data", "slices", name)))
        print("%-16s %d/%d cantos OK" % (name, total - len(failures), total))
        for canto_file, err in failures.items():
            print("   FAIL %s: %s" % (canto_file, err))
        bad += len(failures)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
