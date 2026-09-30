"""Parse cached Wikisource wikitext (see fetch_wikisource.py) into JSON.

Output: data/petrocchi.json, a list of {cantica, canto, line_number, text}.
Only the <poem> block is kept; the rubric above it and interwiki links are dropped.
Wikisource's own {{r|N}} tercet markers are used to verify our line numbering.
"""
import json
import os
import re

from fetch_wikisource import CANTICHE, ROOT, cache_path

OUT = os.path.join(ROOT, "data", "petrocchi.json")

# Templates whose visible text is one of their arguments.
KEEP_ARG = {
    "§": -1,             # {{§|anchor}} -> "", {{§|anchor|text}} -> text
    "Ancora": -1,
    "AutoreCitato": -1,  # {{AutoreCitato|target|label}} -> label
    "Ac": -1,
    "Wl": -1,
    "TestoCitato": -1,
    "§§/Tc": 2,          # {{§§/Tc|anchor|text|work|page}} -> text
}
MARKER = "\u0000R%d\u0000"  # stands in for {{r|N}} so we can check numbering

# Arnaut Daniel speaks in Provençal; these records get "language": "Provençal".
PROVENCAL = {("Purgatorio", 26, n) for n in range(140, 148)}


class ParseError(Exception):
    pass


def split_args(body):
    """Split template body on top-level '|' (not inside nested {{ }} or [[ ]])."""
    args, depth, cur, i = [], 0, [], 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth += 1; cur.append(two); i += 2; continue
        if two in ("}}", "]]"):
            depth -= 1; cur.append(two); i += 2; continue
        if body[i] == "|" and depth == 0:
            args.append("".join(cur)); cur = []; i += 1; continue
        cur.append(body[i]); i += 1
    args.append("".join(cur))
    return args


def expand(text):
    """Expand templates recursively, innermost handled via recursion on arguments."""
    out, i = [], 0
    while i < len(text):
        if text.startswith("{{", i):
            depth, j = 0, i
            while j < len(text):
                if text.startswith("{{", j):
                    depth += 1; j += 2
                elif text.startswith("}}", j):
                    depth -= 1; j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            if depth != 0:
                raise ParseError("unbalanced template near: " + text[i:i + 60])
            args = split_args(text[i + 2:j - 2])
            name = args[0].strip()
            if name.lower() == "r":
                out.append(MARKER % int(args[1]))
            elif name in KEEP_ARG:
                if name in ("§", "Ancora") and len(args) == 2:
                    visible = ""  # bare anchor, no visible text
                else:
                    visible = args[KEEP_ARG[name]]
                out.append(expand(visible))
            else:
                raise ParseError("unknown template: " + name)
            i = j
        else:
            out.append(text[i]); i += 1
    return "".join(out)


def clean_links(text):
    return re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", text)


def parse_canto(wikitext, cantica, canto):
    m = re.search(r"<poem[^>]*>(.*?)</poem>", wikitext, re.S)
    body = expand(m.group(1))
    body = clean_links(body)
    body = re.sub(r"</?span[^>]*>", "", body)
    if re.search(r"[{}\[\]<>|]", body):
        raise ParseError("leftover markup in %s %d" % (cantica, canto))

    records, n, problems = [], 0, []
    for raw in body.split("\n"):
        markers = [int(x) for x in re.findall("\u0000R(\\d+)\u0000", raw)]
        line = re.sub("\u0000R\\d+\u0000", "", raw)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            n += 1
            records.append({"cantica": cantica, "canto": canto, "line_number": n, "text": line})
        for mk in markers:
            if mk != n:
                problems.append("marker r|%d on our line %d" % (mk, n))
    return records, problems


def main():
    records, all_problems = [], []
    for cantica, total in CANTICHE:
        for canto in range(1, total + 1):
            with open(cache_path(cantica, canto), encoding="utf-8") as f:
                recs, problems = parse_canto(f.read(), cantica, canto)
            for r in recs:
                if (r["cantica"], r["canto"], r["line_number"]) in PROVENCAL:
                    r["language"] = "Provençal"
            records.extend(recs)
            all_problems.extend("%s %d: %s" % (cantica, canto, p) for p in problems)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
    print("wrote", len(records), "lines to", OUT)
    for p in all_problems:
        print("NUMBERING:", p)


if __name__ == "__main__":
    main()
