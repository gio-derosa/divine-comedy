"""Download Longfellow's Divine Comedy (Project Gutenberg #1004) and save as JSON.

Output: data/longfellow.json, a list of {cantica, canto, line_number, text}.
"""
import json
import os
import re
import urllib.request

URL = "https://www.gutenberg.org/cache/epub/1004/pg1004.txt"
HEADERS = {"User-Agent": "DanteReaderBot/0.1 (personal study project)"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "scripts", "cache", "pg1004.txt")
OUT = os.path.join(ROOT, "data", "longfellow.json")

HEADING = re.compile(r"^(Inferno|Purgatorio|Paradiso): Canto ([IVXLC]+)\s*$")
SECTION_TITLES = {"INFERNO", "PURGATORIO", "PARADISO", "APPENDIX"}
FOOTNOTE_MARK = re.compile(r"(?<=\S)\*$")

# Arnaut Daniel speaks in Provençal; these records get "language": "Provençal".
PROVENCAL = {("Purgatorio", 26, n) for n in range(140, 148)}


def roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    total = 0
    for i, ch in enumerate(s):
        v = vals[ch]
        if i + 1 < len(s) and vals[s[i + 1]] > v:
            total -= v
        else:
            total += v
    return total


def fetch():
    if not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        data = urllib.request.urlopen(urllib.request.Request(URL, headers=HEADERS)).read()
        with open(CACHE, "wb") as f:
            f.write(data)
    with open(CACHE, "rb") as f:
        return f.read().decode("utf-8")


def main():
    text = fetch().replace("\r\n", "\n").replace("\r", "\n")
    start = text.index("*** START OF THE PROJECT GUTENBERG EBOOK")
    end = text.index("*** END OF THE PROJECT GUTENBERG EBOOK")
    lines = text[start:end].split("\n")

    records = []
    current = None  # (cantica, canto)
    n = 0
    for raw in lines:
        line = raw.strip()
        m = HEADING.match(line)
        if m:
            current = (m.group(1), roman_to_int(m.group(2)))
            n = 0
            continue
        if line in SECTION_TITLES:
            current = None  # cantica title page, or the appendix of sonnets
            continue
        if current is None:
            continue  # front matter / table of contents / appendix
        if not line:
            continue
        if line.startswith("* "):
            current = None  # footnote block (Purgatorio XXVI gloss) runs to next canto
            continue
        line = FOOTNOTE_MARK.sub("", line)
        n += 1
        record = {"cantica": current[0], "canto": current[1], "line_number": n, "text": line}
        if (current[0], current[1], n) in PROVENCAL:
            record["language"] = "Provençal"
        records.append(record)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
    print("wrote", len(records), "lines to", OUT)


if __name__ == "__main__":
    main()
