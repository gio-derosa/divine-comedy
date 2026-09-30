"""Build the static site's data files from data/petrocchi.json and data/longfellow.json.

Each source becomes site/data/<name>.js, which assigns the records (grouped by
cantica and canto) to a global. Script files are used instead of fetched JSON so
the site also works when index.html is opened straight from disk (file://).
Each tab loads only its own file.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = {"petrocchi": "DC_PETROCCHI", "longfellow": "DC_LONGFELLOW"}


def main():
    out_dir = os.path.join(ROOT, "site", "data")
    os.makedirs(out_dir, exist_ok=True)
    for name, global_name in SOURCES.items():
        records = json.load(open(os.path.join(ROOT, "data", name + ".json"), encoding="utf-8"))
        # { cantica: [ canto1_lines, canto2_lines, ... ] }, each line [text, translation(, language)]
        grouped = {}
        for r in records:
            if not r.get("translation", "").strip():
                raise SystemExit("missing translation: %s %s %s" % (r["cantica"], r["canto"], r["line_number"]))
            cantos = grouped.setdefault(r["cantica"], [])
            while len(cantos) < r["canto"]:
                cantos.append([])
            lines = cantos[r["canto"] - 1]
            if r["line_number"] != len(lines) + 1:
                raise SystemExit("line numbers out of order at %s %s %s" % (r["cantica"], r["canto"], r["line_number"]))
            line = [r["text"], r["translation"]]
            if r.get("language"):
                line.append(r["language"])
            lines.append(line)
        path = os.path.join(out_dir, name + ".js")
        with open(path, "w", encoding="utf-8") as f:
            f.write("window.%s = %s;\n" % (global_name, json.dumps(grouped, ensure_ascii=False, separators=(",", ":"))))
        print("wrote %s (%d lines, %d KB)" % (path, len(records), os.path.getsize(path) // 1024))


if __name__ == "__main__":
    main()
