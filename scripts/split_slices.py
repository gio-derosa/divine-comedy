"""Split each source JSON into per-cantica slices for the translation subagents.

data/slices/<lang>_<cantica>/canto_NN.json holds one canto's records,
one compact record per line so each file is easy to read in full.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = {"it": "data/petrocchi.json", "en": "data/longfellow.json"}


def main():
    for lang, path in SOURCES.items():
        records = json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
        by_canto = {}
        for r in records:
            r = {k: v for k, v in r.items() if k != "translation"}
            by_canto.setdefault((r["cantica"], r["canto"]), []).append(r)
        for (cantica, canto), recs in by_canto.items():
            d = os.path.join(ROOT, "data", "slices", "%s_%s" % (lang, cantica.lower()))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "canto_%02d.json" % canto), "w", encoding="utf-8") as f:
                f.write("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n]\n")
    print("slices written to data/slices/")


if __name__ == "__main__":
    main()
