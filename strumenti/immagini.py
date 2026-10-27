"""Immagini derivate dalle foto, usate da costruisci.py.

- Anteprime social (1200×630, JPEG): quello che compare quando un pezzo
  viene condiviso su WhatsApp, Facebook o Instagram. Foto a sinistra,
  nome e prezzo a destra.
- Foto JPEG per il catalogo prodotti di Google e Meta, che non sempre
  accettano il WebP.

Servono Pillow (pip install pillow) e il carattere in strumenti/fonts/.
I nomi dei file contengono un'impronta dei dati: se cambiano nome, prezzo
o disponibilità, l'immagine viene rifatta e i social non mostrano quella
vecchia rimasta in memoria.
"""
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RADICE = Path(__file__).resolve().parent.parent
FOTO = RADICE / "docs" / "foto"
SOCIAL = FOTO / "social"
FONT = RADICE / "strumenti" / "fonts" / "Fraunces.ttf"

SABBIA = (246, 240, 230)
INCHIOSTRO = (43, 38, 34)
TENUE = (122, 111, 99)
TERRA = (169, 80, 47)
W, H = 1200, 630


def _font(dimensione, peso=400, ottica=72):
    f = ImageFont.truetype(str(FONT), dimensione)
    # assi: dimensione ottica, peso, morbidezza, "wonky"
    f.set_variation_by_axes([ottica, peso, 0, 0])
    return f


def _impronta(*dati):
    return hashlib.sha1(json.dumps(dati, ensure_ascii=False).encode()).hexdigest()[:8]


def _a_capo(disegno, testo, font, larghezza, righe_max):
    parole, righe, riga = testo.split(), [], ""
    for parola in parole:
        prova = f"{riga} {parola}".strip()
        if disegno.textlength(prova, font=font) <= larghezza:
            riga = prova
        else:
            righe.append(riga)
            riga = parola
    righe.append(riga)
    if len(righe) > righe_max:
        righe = righe[:righe_max]
        righe[-1] = righe[-1].rstrip(",.;:") + "…"
    return righe


def _impronta_file(percorso):
    return hashlib.sha1(percorso.read_bytes()).hexdigest()[:8]


def anteprima_social(nome_file, foto, occhiello, titolo, prezzo="", nota=""):
    """Crea (se manca) docs/foto/social/<nome_file>-<impronta>.jpg e ne restituisce il percorso relativo a docs/."""
    impronta = _impronta(foto, occhiello, titolo, prezzo, nota, _impronta_file(FOTO / f"{foto}-1200.webp"), 3)
    dest = SOCIAL / f"{nome_file}-{impronta}.jpg"
    relativo = f"foto/social/{dest.name}"
    if dest.exists():
        return relativo
    SOCIAL.mkdir(parents=True, exist_ok=True)
    for vecchio in SOCIAL.glob(f"{nome_file}-*.jpg"):
        vecchio.unlink()

    tela = Image.new("RGB", (W, H), SABBIA)
    with Image.open(FOTO / f"{foto}-1200.webp") as im:
        im = im.convert("RGB")
        if im.width / im.height <= 560 / H:
            # foto verticale: alta quanto la tela, il pezzo si vede tutto
            larg = round(im.width * H / im.height)
            tela.paste(im.resize((larg, H), Image.LANCZOS), (0, 0))
        else:
            # foto orizzontale (un quadro): intera, centrata, con un margine
            larg = 560
            w = larg - 80
            h = round(im.height * w / im.width)
            tela.paste(im.resize((w, h), Image.LANCZOS), (40, (H - h) // 2))
    x0 = larg + 64
    larghezza = W - x0 - 64
    d = ImageDraw.Draw(tela)

    f_occhiello = _font(22, 500, 14)
    f_titolo = _font(62, 400, 72)
    f_prezzo = _font(54, 400, 72)
    f_nota = _font(24, 400, 14)
    f_firma = _font(30, 500, 24)

    y = 92
    d.text((x0, y), occhiello.upper(), font=f_occhiello, fill=TERRA)
    y += 52
    for riga in _a_capo(d, titolo, f_titolo, larghezza, 3):
        d.text((x0, y), riga, font=f_titolo, fill=INCHIOSTRO)
        y += 72
    y += 18
    if prezzo:
        d.text((x0, y), prezzo, font=f_prezzo, fill=INCHIOSTRO)
        y += 74
    if nota:
        for riga in _a_capo(d, nota, f_nota, larghezza, 2):
            d.text((x0, y), riga, font=f_nota, fill=TENUE)
            y += 34

    with Image.open(RADICE / "docs" / "logo.png") as logo:
        logo = logo.convert("RGBA").resize((44, 44), Image.LANCZOS)
        tela.paste(logo, (x0, H - 92), logo)
    d.text((x0 + 60, H - 86), "DART · darthome.it", font=f_firma, fill=INCHIOSTRO)

    tela.save(dest, "JPEG", quality=84, optimize=True, progressive=True)
    return relativo


def foto_jpeg(foto):
    """Copia JPEG (1200 px) di una foto, per i cataloghi prodotti. Restituisce il percorso relativo a docs/."""
    sorgente = FOTO / f"{foto}-1200.webp"
    dest = FOTO / f"{foto}-{_impronta_file(sorgente)}.jpg"
    if not dest.exists():
        for vecchio in FOTO.iterdir():  # versioni della stessa foto fatte prima di un ritocco
            if re.fullmatch(re.escape(foto) + r"(-[0-9a-f]{8})?\.jpg", vecchio.name):
                vecchio.unlink()
        with Image.open(sorgente) as im:
            im.convert("RGB").save(dest, "JPEG", quality=84, optimize=True, progressive=True)
    return f"foto/{dest.name}"
