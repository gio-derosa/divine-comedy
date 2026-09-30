"""Download wikitext of all 100 cantos of the Divina Commedia from it.wikisource.org.

The Wikisource text follows Petrocchi, "La Commedia secondo l'antica vulgata"
(stated in the Infotesto on Discussione:Divina_Commedia). Pages are cached in
scripts/cache/wikisource/ so parsing can be rerun offline.
"""
import json
import os
import urllib.parse
import urllib.request

API = "https://it.wikisource.org/w/api.php"
HEADERS = {"User-Agent": "DanteReaderBot/0.1 (personal study project)"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "scripts", "cache", "wikisource")

CANTICHE = [("Inferno", 34), ("Purgatorio", 33), ("Paradiso", 33)]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
         "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX",
         "XXXI", "XXXII", "XXXIII", "XXXIV"]


def title(cantica, canto):
    return "Divina Commedia/%s/Canto %s" % (cantica, ROMAN[canto - 1])


def cache_path(cantica, canto):
    return os.path.join(CACHE_DIR, "%s_%02d.wiki" % (cantica, canto))


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    wanted = [(c, n) for c, total in CANTICHE for n in range(1, total + 1)
              if not os.path.exists(cache_path(c, n))]
    by_title = {title(c, n): (c, n) for c, n in wanted}
    titles = list(by_title)
    for i in range(0, len(titles), 50):
        params = {"action": "query", "prop": "revisions", "rvprop": "content",
                  "rvslots": "main", "format": "json", "formatversion": "2",
                  "titles": "|".join(titles[i:i + 50])}
        url = API + "?" + urllib.parse.urlencode(params)
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)).read())
        for page in data["query"]["pages"]:
            if page.get("missing"):
                raise SystemExit("missing page: " + page["title"])
            c, n = by_title[page["title"]]
            with open(cache_path(c, n), "w", encoding="utf-8") as f:
                f.write(page["revisions"][0]["slots"]["main"]["content"])
    print("cached", len(os.listdir(CACHE_DIR)), "cantos in", CACHE_DIR)


if __name__ == "__main__":
    main()
