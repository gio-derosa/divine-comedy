# La Divina Commedia — line-by-line reader

A static site for reading Dante's *Divine Comedy* in Italian (Petrocchi text, from
Italian Wikisource) and English (Longfellow's translation, from Project Gutenberg #1004).
Tap any line to swap it for a literal translation; tap again to swap back.

## Run it

Open `site/index.html` in a browser (works straight from disk), or serve the folder:

    python -m http.server 8000 --directory site

The `site/` folder is the whole deployable site — copy it to any static host.
Links like `index.html#en/purgatorio/26` open a specific tab and canto.

Pushing to `main` deploys to GitHub Pages via `.github/workflows/pages.yml`, which
runs `scripts/build_site.py` and publishes `site/`.

## Data pipeline

    python scripts/fetch_wikisource.py     # download 100 canto pages (cached in scripts/cache/)
    python scripts/parse_wikisource.py     # -> data/petrocchi.json
    python scripts/parse_gutenberg.py      # -> data/longfellow.json
    python scripts/report_counts.py        # line counts per cantica, flags odd cantos
    python scripts/split_slices.py         # -> data/slices/<lang>_<cantica>/canto_NN.json
    #   (translation: data/work/<lang>_<cantica>/canto_NN.txt, rows "<line_number>|<translation>")
    python scripts/check_translations.py   # every line translated exactly once?
    python scripts/audit_translations.py   # heuristic check for lines shifted onto neighbours
    python scripts/merge_translations.py   # adds "translation" to data/*.json
    python scripts/build_site.py           # -> site/data/*.js

Rerunning the two `parse_*` scripts rewrites `data/*.json` without translations;
run `merge_translations.py` afterwards to restore them from `data/work/`.

## Tests

With a server running at the project root (`python -m http.server 8765`), open
`http://127.0.0.1:8765/tests/browser_test.html`; it drives the app in an iframe and
lists PASS/FAIL for line counts, tercet numbering, toggling, tabs and navigation.
