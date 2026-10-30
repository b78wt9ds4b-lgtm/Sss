"""Copia di prova del sito, da mettere online senza che Google la indicizzi.

    python3 strumenti/anteprima.py              # crea anteprima/ (non va su GitHub)
    python3 strumenti/anteprima.py CARTELLA     # altrove

Parte da docs/ (il sito vero, che resta com'è) e nella copia:
- mette <meta name="robots" content="noindex, nofollow"> in ogni pagina;
- scrive un robots.txt che chiude tutto e un _headers con X-Robots-Tag: noindex
  (lo leggono Netlify e Cloudflare Pages);
- toglie sitemap.xml e feed-prodotti.xml, così nessuno li registra per sbaglio.
I link «Acquista ora» portano comunque al carrello vero di darthome.it: nella copia
di prova non completare acquisti.
Poi controlla.py --anteprima CARTELLA verifica che la copia sia chiusa a Google, e
controlla.py (senza opzioni) che il sito vero in docs/ sia aperto.
"""
import re
import shutil
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
DOCS = RADICE / "docs"
ROBOTS = '<meta name="robots" content="noindex, nofollow">'


def main():
    dest = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else RADICE / "anteprima"
    if dest == DOCS or DOCS in dest.parents:
        sys.exit("La copia di prova non può stare dentro docs/: è la cartella del sito vero.")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(DOCS, dest, ignore=shutil.ignore_patterns("sitemap.xml", "feed-prodotti.xml"))
    pagine = 0
    for f in dest.rglob("*.html"):
        s = f.read_text(encoding="utf-8")
        s = re.sub(r'<meta name="robots"[^>]*>\n?', "", s)
        s = s.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n{ROBOTS}', 1)
        f.write_text(s, encoding="utf-8")
        pagine += 1
    (dest / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (dest / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n", encoding="utf-8")
    print(f"Copia di prova in {dest}: {pagine} pagine chiuse a Google (noindex).")


if __name__ == "__main__":
    main()
