"""Controlli automatici sul sito generato in docs/, da lanciare dopo costruisci.py.

    python3 strumenti/controlla.py             # solo i file in docs/
    python3 strumenti/controlla.py --negozio   # in più: i dati sono ancora quelli del negozio?

Senza programmi esterni verifica che:
- ogni collegamento e ogni risorsa interna (pagine, foto, CSS, JS, caratteri) esista;
- ogni pagina abbia titolo, descrizione e un solo h1; l'indirizzo canonico solo se indicizzabile;
- ogni <img> abbia alt, width e height, e un indirizzo (src, o data-src nella galleria);
- i dati strutturati (JSON-LD) siano JSON valido;
- nelle schede il prezzo e la disponibilità per Google siano quelli di data/pezzi.json, e il
  link «Acquista ora» ci sia solo per i pezzi disponibili;
- nella galleria si scarichi subito solo la prima foto, e le altre abbiano la copia in <noscript>.

Con --negozio confronta data/pezzi.json con il negozio WordPress (prezzi, venduti, pezzi
nuovi): se qualcosa è cambiato, va rilanciato importa.py.

Indicizzazione: docs/ è il sito vero, quindi nessuna pagina (tranne la 404) deve avere noindex
e robots.txt non deve chiudere il sito. Con --anteprima CARTELLA controlla invece la copia di
prova fatta da anteprima.py: lì ogni pagina deve essere chiusa a Google.
Esce con codice 1 se trova problemi.
"""
import json
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

RADICE = Path(__file__).resolve().parent.parent
DOCS = RADICE / "docs"
NEGOZIO = json.loads((RADICE / "data" / "negozio.json").read_text(encoding="utf-8"))
PEZZI = json.loads((RADICE / "data" / "pezzi.json").read_text(encoding="utf-8"))

problemi = []


def segnala(pagina, testo):
    problemi.append(f"{pagina}: {testo}")


class Lettore(HTMLParser):
    """Raccoglie da una pagina quello che serve ai controlli."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.risorse, self.immagini, self.jsonld, self.h1 = [], [], [], 0
        self.titolo = self.descrizione = self.canonico = None
        self.noindex = False
        self.dentro = None          # "title", "jsonld" o None
        self.testo = ""
        self.nastro = 0             # profondità dentro .galleria-nastro
        self.noscript = 0
        self.galleria = []          # (attributi dell'img, dentro <noscript>?)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.nastro:
            self.nastro += tag not in ("img", "source", "br")
        if tag == "div" and "galleria-nastro" in (a.get("class") or "").split():
            self.nastro = 1
        if tag == "noscript":
            self.noscript += 1
        for chiave in ("href", "src", "data-src"):
            if chiave in a and tag in ("a", "link", "script", "img", "source"):
                if tag == "link" and a.get("rel") in ("canonical", "alternate"):
                    continue
                self.risorse.append(a[chiave])
        for chiave in ("srcset", "data-srcset", "imagesrcset"):
            if a.get(chiave):
                self.risorse += [voce.strip().split(" ")[0] for voce in a[chiave].split(",") if voce.strip()]
        if tag == "img":
            self.immagini.append(a)
            if self.nastro:
                self.galleria.append((a, self.noscript > 0))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "title":
            self.dentro, self.testo = "title", ""
        elif tag == "meta" and a.get("name") == "description":
            self.descrizione = a.get("content")
        elif tag == "meta" and a.get("name") == "robots" and "noindex" in (a.get("content") or ""):
            self.noindex = True
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonico = a.get("href")
        elif tag == "script" and a.get("type") == "application/ld+json":
            self.dentro, self.testo = "jsonld", ""

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.nastro and tag not in ("img", "source", "br"):
            self.nastro -= 1

    def handle_endtag(self, tag):
        if self.nastro:
            self.nastro -= 1
        if tag == "noscript":
            self.noscript -= 1
        if tag == "title" and self.dentro == "title":
            self.titolo, self.dentro = self.testo.strip(), None
        elif tag == "script" and self.dentro == "jsonld":
            self.jsonld.append(self.testo)
            self.dentro = None

    def handle_data(self, data):
        if self.dentro:
            self.testo += data


def esiste(url, pagina):
    """Una risorsa interna esiste in docs/? Le cartelle valgono come cartella/index.html."""
    p = urlparse(url)
    if p.scheme or url.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return True
    # la 404 viene servita a qualsiasi indirizzo e usa la radice come base
    base = "http://x/" if pagina.name == "404.html" else "http://x/" + pagina.relative_to(DOCS).as_posix()
    percorso = unquote(urlparse(urljoin(base, p.path)).path).lstrip("/")
    destinazione = DOCS / percorso
    return (destinazione / "index.html").is_file() if destinazione.is_dir() or percorso.endswith("/") or not percorso else destinazione.is_file()


def controlla_pagina(f):
    nome = f.relative_to(DOCS).as_posix()
    lettore = Lettore()
    lettore.feed(f.read_text(encoding="utf-8"))
    for url in sorted(set(lettore.risorse)):
        if not esiste(url, f):
            segnala(nome, f"collegamento o risorsa mancante: {url}")
    if not lettore.titolo:
        segnala(nome, "manca il titolo")
    if not lettore.descrizione:
        segnala(nome, "manca la descrizione")
    if lettore.h1 != 1:
        segnala(nome, f"{lettore.h1} titoli h1 invece di 1")
    if lettore.noindex and lettore.canonico:
        segnala(nome, "pagina da non indicizzare con indirizzo canonico")
    if not lettore.noindex and not lettore.canonico:
        segnala(nome, "manca l'indirizzo canonico")
    for img in lettore.immagini:
        if not img.get("src") and not img.get("data-src"):
            segnala(nome, "immagine senza indirizzo (src vuoto o assente: HTML non valido)")
        if "alt" not in img:
            segnala(nome, f"immagine senza alt: {img.get('src') or img.get('data-src')}")
        if not (img.get("width") and img.get("height")):
            segnala(nome, f"immagine senza width/height: {img.get('src') or img.get('data-src')}")
    dati = []
    for blocco in lettore.jsonld:
        try:
            dati.append(json.loads(blocco))
        except ValueError:
            segnala(nome, "JSON-LD non valido")
    return nome, lettore, dati


def controlla_scheda(p, lettore, dati, nome):
    prodotto = next((d for d in dati if d.get("@type") == "Product"), None)
    acquisto = NEGOZIO.get("acquisto_online", "").format(id=p["id"]) if NEGOZIO.get("acquisto_online") else ""
    ha_link = acquisto and acquisto in lettore.risorse
    if not prodotto:
        segnala(nome, "mancano i dati del prodotto (JSON-LD)")
        return
    offerta = prodotto.get("offers") or {}
    if p["prezzo"] and abs(float(offerta.get("price", -1)) - p["prezzo"]) > 0.001:
        segnala(nome, f"prezzo nei dati per Google {offerta.get('price')} invece di {p['prezzo']}")
    disponibile = offerta.get("availability", "").endswith("InStock")
    if p["prezzo"] and disponibile != p["disponibile"]:
        segnala(nome, "disponibilità nei dati per Google diversa da data/pezzi.json")
    if p["disponibile"] and p["prezzo"] and acquisto and not ha_link:
        segnala(nome, "manca il collegamento «Acquista ora»")
    if not p["disponibile"] and ha_link:
        segnala(nome, "pezzo venduto con il collegamento «Acquista ora»")
    galleria = [a for a, nascosta in lettore.galleria if not nascosta]
    copie = [a for a, nascosta in lettore.galleria if nascosta]
    if galleria:
        prima, altre = galleria[0], galleria[1:]
        if not prima.get("src") or prima.get("loading") == "lazy" or prima.get("fetchpriority") != "high":
            segnala(nome, "la prima foto della galleria deve partire subito, con priorità alta")
        if any(not a.get("data-src") or not a.get("data-srcset") or a.get("srcset") for a in altre):
            segnala(nome, "le foto dopo la prima devono avere l'indirizzo in data-src e data-srcset")
        if any(not (a.get("src") or "").endswith("-200.webp") for a in altre):
            segnala(nome, "le foto rimandate devono avere come src la miniatura da 200 px (HTML valido)")
        if any(a.get("sizes") and not a.get("srcset") for a in galleria):
            segnala(nome, "sizes senza srcset (HTML non valido)")
        if len(copie) != len(altre):
            segnala(nome, "manca la copia in <noscript> di qualche foto della galleria")


def controlla_negozio():
    """Confronto con il negozio WordPress: prezzi, venduti, pezzi nuovi o tolti."""
    url = NEGOZIO["wordpress"].rstrip("/") + "/wp-json/wc/store/v1/products?per_page=100"
    with urllib.request.urlopen(url, timeout=60) as r:
        negozio = {x["id"]: x for x in json.load(r)}
    nostri = {p["id"]: p for p in PEZZI}
    for i, x in negozio.items():
        prezzo = int(x["prices"]["price"] or 0) / 10 ** x["prices"].get("currency_minor_unit", 2)
        if i not in nostri:
            if x["is_purchasable"] and x["is_in_stock"]:
                segnala("dati", f"pezzo nuovo sul negozio, assente qui: {x['name']} (ID {i})")
            continue
        p = nostri[i]
        if x["is_in_stock"] != p["disponibile"]:
            segnala("dati", f"{p['nome']}: sul negozio è {'disponibile' if x['is_in_stock'] else 'venduto'}")
        if prezzo and p["prezzo"] and abs(prezzo - p["prezzo"]) > 0.001:
            segnala("dati", f"{p['nome']}: sul negozio costa {prezzo:g} €, qui {p['prezzo']:g} €")
    for i, p in nostri.items():
        if i not in negozio:
            segnala("dati", f"{p['nome']} (ID {i}) non è più sul negozio")


def controlla_indicizzazione(pagina, lettore):
    """Il sito vero si fa trovare: una pagina con noindex in docs/ è un resto di una copia di prova."""
    if lettore.noindex and pagina.name != "404.html":
        segnala(pagina.relative_to(DOCS).as_posix(), "noindex: nel sito vero la pagina sparirebbe da Google")


def controlla_anteprima(cartella):
    """La copia di prova è chiusa a Google in ogni pagina, e non porta sitemap né catalogo prodotti."""
    pagine = sorted(cartella.rglob("*.html"))
    for f in pagine:
        lettore = Lettore()
        lettore.feed(f.read_text(encoding="utf-8"))
        if not lettore.noindex:
            segnala(f.relative_to(cartella).as_posix(), "manca noindex: Google potrebbe indicizzare la copia di prova")
    robots = cartella / "robots.txt"
    if not robots.is_file() or "Disallow: /\n" not in robots.read_text(encoding="utf-8"):
        segnala("robots.txt", "nella copia di prova deve chiudere tutto (Disallow: /)")
    if "noindex" not in ((cartella / "_headers").read_text(encoding="utf-8") if (cartella / "_headers").is_file() else ""):
        segnala("_headers", "manca X-Robots-Tag: noindex")
    for f in ("sitemap.xml", "feed-prodotti.xml"):
        if (cartella / f).exists():
            segnala(f, "non deve stare nella copia di prova")
    return pagine


def main():
    if "--anteprima" in sys.argv:
        cartella = Path(sys.argv[sys.argv.index("--anteprima") + 1]).resolve()
        pagine = controlla_anteprima(cartella)
        for riga in problemi:
            print("✗", riga)
        print(f"Copia di prova: {len(pagine)} pagine controllate, {len(problemi)} problemi.")
        sys.exit(1 if problemi else 0)
    pagine = sorted(DOCS.rglob("*.html"))
    per_slug = {p["slug"]: p for p in PEZZI}
    for f in pagine:
        nome, lettore, dati = controlla_pagina(f)
        controlla_indicizzazione(f, lettore)
        parti = f.relative_to(DOCS).parts
        if len(parti) == 3 and parti[0] == "pezzo" and parti[1] in per_slug:
            controlla_scheda(per_slug[parti[1]], lettore, dati, nome)
    for p in PEZZI:
        if not (DOCS / "pezzo" / p["slug"] / "index.html").is_file():
            segnala("dati", f"manca la scheda di {p['nome']}")
    robots = (DOCS / "robots.txt").read_text(encoding="utf-8") if (DOCS / "robots.txt").is_file() else ""
    if "Disallow: /\n" in robots or "Sitemap:" not in robots:
        segnala("robots.txt", "il sito vero deve essere aperto ai motori di ricerca e indicare la sitemap")
    if (DOCS / "_headers").exists():
        segnala("_headers", "file della copia di prova finito nel sito vero")
    if "--negozio" in sys.argv:
        controlla_negozio()
    for riga in problemi:
        print("✗", riga)
    print(f"{len(pagine)} pagine controllate, {len(problemi)} problemi.")
    sys.exit(1 if problemi else 0)


if __name__ == "__main__":
    main()
