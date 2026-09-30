"""Merge verified translations (data/work/<slice>/canto_NN.txt) into the source JSON.

Adds a "translation" field to every record of data/petrocchi.json and
data/longfellow.json. Refuses to write anything if any canto fails the check.
"""
import json
import os
import sys

from check_translations import ROOT, check_slice

SOURCES = {"it": "data/petrocchi.json", "en": "data/longfellow.json"}


def load_translations(slice_name, canto):
    path = os.path.join(ROOT, "data", "work", slice_name, "canto_%02d.txt" % canto)
    with open(path, encoding="utf-8-sig") as f:
        rows = [line.split("|") for line in f.read().splitlines() if line.strip()]
    return {int(n): t.strip() for n, t in rows}


def main():
    slices = sorted(os.listdir(os.path.join(ROOT, "data", "slices")))
    failures = {s: check_slice(s) for s in slices}
    if any(failures.values()):
        for s, f in failures.items():
            for canto_file, err in f.items():
                print("FAIL %s/%s: %s" % (s, canto_file, err))
        sys.exit("not merging: fix the failures above first")

    for lang, path in SOURCES.items():
        full = os.path.join(ROOT, path)
        records = json.load(open(full, encoding="utf-8"))
        cache = {}
        for r in records:
            key = (r["cantica"], r["canto"])
            if key not in cache:
                cache[key] = load_translations("%s_%s" % (lang, r["cantica"].lower()), r["canto"])
            r["translation"] = cache[key][r["line_number"]]
        with open(full, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=1)
        print("merged %d translations into %s" % (len(records), path))


if __name__ == "__main__":
    main()
