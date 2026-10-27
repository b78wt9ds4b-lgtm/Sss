"""Importa pezzi e foto dal vecchio sito WordPress (darthome.it).

Scrive data/pezzi.json e le foto in docs/foto/.
Va lanciato una volta sola, o di nuovo per riallinearsi al vecchio sito:
    python3 strumenti/importa.py
Richiede Pillow (pip install pillow).
"""
import html
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

SITO = "https://www.darthome.it"
RADICE = Path(__file__).resolve().parent.parent
FOTO = RADICE / "docs" / "foto"
DATI = RADICE / "data"

# Larghezze generate per ogni foto (srcset).
LARGHEZZE = (600, 1200)

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


def scarica(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (importa DART)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


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


def salva_foto(url, nome, larghezze=LARGHEZZE):
    """Salva la foto in WebP alle larghezze indicate; restituisce le proporzioni."""
    destinazioni = [FOTO / f"{nome}-{w}.webp" for w in larghezze]
    if all(d.exists() for d in destinazioni):
        with Image.open(destinazioni[-1]) as im:
            return im.width, im.height
    with Image.open(io.BytesIO(scarica(url))) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        for w, dest in zip(larghezze, destinazioni):
            copia = im.copy()
            if copia.width > w:
                copia = copia.resize((w, round(copia.height * w / copia.width)), Image.LANCZOS)
            copia.save(dest, "WEBP", quality=78, method=6)
        larghezza = min(im.width, larghezze[-1])
        return larghezza, round(im.height * larghezza / im.width)


def euro(minori):
    return int(minori) / 100 if minori else None


def importa_pezzi():
    prodotti = json.loads(scarica(f"{SITO}/wp-json/wc/store/v1/products?per_page=100"))
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
            w, h = salva_foto(img["src"], f"{slug}-{i + 1}")
            foto.append({"file": f"{slug}-{i + 1}", "w": w, "h": h})
        prezzo = euro(p["prices"]["price"])
        misure = spec.get("Misure", "")
        pezzi.append({
            "id": p["id"],
            "slug": slug,
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
