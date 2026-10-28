"""Importa pezzi e foto dal vecchio sito WordPress (darthome.it).

Scrive data/pezzi.json e le foto in docs/foto/.
Va lanciato una volta sola, o di nuovo per riallinearsi al vecchio sito:
    python3 strumenti/importa.py
Con --tutte-le-foto riscarica e riconverte anche le foto già presenti
(serve se cambiano le misure o la compressione in immagini.py).
Richiede Pillow (pip install pillow).
"""
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image

from immagini import LARGHEZZE, originale, scarica, scrivi_varianti

SITO = "https://www.darthome.it"
RADICE = Path(__file__).resolve().parent.parent
FOTO = RADICE / "docs" / "foto"
DATI = RADICE / "data"

# Pezzi di prova da non importare.
ESCLUSI = {"cartolina"}

CATEGORIE = {
    "mobili": "mobili",
    "quadri-e-ritratti": "quadri",
    "altro-arredamento": "sculture",
    "utensili-a-tema": "utensili",
}


# Correzioni ai testi del vecchio sito.
CORREZIONI = {"Mibile": "Mobile", "Acrilico si tela": "Acrilico su tela"}


def testo(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def correggi(s):
    for sbagliato, giusto in CORREZIONI.items():
        s = s.replace(sbagliato, giusto)
    return s


def pulisci_html(s):
    s = re.sub(r"\s*(class|style|id)=\"[^\"]*\"", "", s or "")
    s = re.sub(r"<p>\s*(&nbsp;)?\s*</p>", "", s)
    return correggi(s.strip())


def specifiche(slug):
    """Legge la tabella 'specifiche' dalla scheda del vecchio sito."""
    pagina = scarica(f"{SITO}/pezzo/{slug}/").decode("utf-8")
    righe = re.findall(r'<span class="k">(.*?)</span><span class="v">(.*?)</span>', pagina)
    return {testo(k): testo(v) for k, v in righe}


TUTTE = "--tutte-le-foto" in sys.argv


def salva_foto(url, nome, forza=False):
    """Salva la foto in WebP alle LARGHEZZE di immagini.py; restituisce le proporzioni."""
    destinazioni = [FOTO / f"{nome}-{w}.webp" for w in LARGHEZZE]
    if not (forza or TUTTE) and all(d.exists() for d in destinazioni):
        with Image.open(destinazioni[-1]) as im:
            return im.width, im.height
    return scrivi_varianti(originale(url), nome)


def euro(minori):
    return int(minori) / 100 if minori else None


def date_pubblicazione():
    """Data in cui ogni pezzo è stato messo in vendita (serve per l'etichetta «Nuovo»)."""
    voci = json.loads(scarica(f"{SITO}/wp-json/wp/v2/product?per_page=100&_fields=slug,date"))
    return {v["slug"]: v["date"][:10] for v in voci}


def importa_pezzi():
    prodotti = json.loads(scarica(f"{SITO}/wp-json/wc/store/v1/products?per_page=100"))
    date = date_pubblicazione()
    # foto già scaricate e da dove venivano: se sul negozio una foto è stata tolta
    # o spostata, allo stesso nome corrisponde un'altra foto e va riscaricata
    prima = {}
    if (DATI / "pezzi.json").exists():
        for p in json.loads((DATI / "pezzi.json").read_text(encoding="utf-8")):
            prima.update({f["file"]: f.get("origine") for f in p["foto"]})
    pezzi = []
    for p in prodotti:
        slug = p["slug"]
        if slug in ESCLUSI:
            continue
        print("·", slug, file=sys.stderr)
        spec = specifiche(slug)
        breve = testo(p["short_description"])
        # Nel vecchio sito la descrizione breve finisce con le misure: le togliamo.
        sottotitolo = re.split(r"\s·\s(?=(H|Ø|\d))", breve)[0] if breve else ""
        foto = []
        for i, img in enumerate(p["images"]):
            nome = f"{slug}-{i + 1}"
            w, h = salva_foto(img["src"], nome, forza=prima.get(nome) not in (None, img["src"]))
            foto.append({"file": f"{slug}-{i + 1}", "w": w, "h": h, "origine": img["src"]})
        prezzo = euro(p["prices"]["price"])
        misure = re.sub(r"(\d)\.(\d)", r"\1,\2", spec.get("Misure", ""))  # 1.8 -> 1,8
        pezzi.append({
            "id": p["id"],
            "slug": slug,
            "pubblicato": date.get(slug, ""),
            "nome": correggi(html.unescape(p["name"])),
            "categoria": CATEGORIE.get(p["categories"][0]["slug"], "altro"),
            "sottotitolo": correggi(sottotitolo),
            "descrizione": pulisci_html(p["description"]),
            "prezzo": prezzo or None,
            "disponibile": bool(p["is_in_stock"]),
            "misure": "" if misure.lower().startswith("misure in arrivo") else misure,
            "tecnica": spec.get("Tecnica", ""),
            "spedizione": spec.get("Spedizione in Italia", ""),
            "spedizione_isole": spec.get("Spedizione in Sicilia e Sardegna", ""),
            "garanzia": spec.get("Garanzia", ""),
            "foto": foto,
        })
    return pezzi


def importa_immagini_tema():
    base = f"{SITO}/wp-content/themes/dart-child/assets/img/"
    salva_foto(base + "hero.jpg", "hero")
    salva_foto(base + "negozio.jpg", "negozio")
    (RADICE / "docs" / "logo.png").write_bytes(scarica(base + "logo.png"))


if __name__ == "__main__":
    FOTO.mkdir(parents=True, exist_ok=True)
    DATI.mkdir(exist_ok=True)
    importa_immagini_tema()
    pezzi = importa_pezzi()
    (DATI / "pezzi.json").write_text(
        json.dumps(pezzi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Importati {len(pezzi)} pezzi.", file=sys.stderr)
