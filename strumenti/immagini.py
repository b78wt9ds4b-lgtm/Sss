"""Immagini del sito, usate da importa.py, ritocca.py e costruisci.py.

- Varianti WebP di ogni foto (400, 800 e 1200 px di larghezza): il
  browser scarica la più piccola che basta per lo schermo.
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
import io
import json
import re
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

RADICE = Path(__file__).resolve().parent.parent
FOTO = RADICE / "docs" / "foto"
SOCIAL = FOTO / "social"
FONT = RADICE / "strumenti" / "fonts" / "Fraunces.ttf"
ORIGINALI = RADICE / ".originali"  # copie degli originali scaricati, non pubblicate

# Larghezze di ogni foto sul sito (srcset). Le foto molto dettagliate (quadri
# materici) vengono compresse un po' di più invece di pesare il doppio delle altre.
LARGHEZZE = (400, 800, 1200)
PESO_MAX = {400: 45_000, 800: 120_000, 1200: 230_000}

SABBIA = (246, 240, 230)
INCHIOSTRO = (43, 38, 34)
TENUE = (122, 111, 99)
TERRA = (169, 80, 47)
W, H = 1200, 630


def chiave(url):
    """Identità stabile di una foto: il suo percorso su WordPress, es. «2026/10/IMG_6651.jpg»."""
    return url.split("/uploads/", 1)[-1] if "/uploads/" in url else "tema/" + url.rsplit("/", 1)[-1]


def scarica(url, tentativi=5):
    """Scarica un indirizzo; se la connessione salta riprova, aspettando 2, 4, 8, 16 secondi."""
    for n in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (DART)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except OSError:
            if n == tentativi - 1:
                raise
            time.sleep(2 ** (n + 1))


def originale(url):
    """L'originale ad alta risoluzione, scaricato una volta sola in .originali/."""
    ORIGINALI.mkdir(exist_ok=True)
    copia = ORIGINALI / chiave(url).replace("/", "-")
    if not copia.exists():
        copia.write_bytes(scarica(url))
    return ImageOps.exif_transpose(Image.open(io.BytesIO(copia.read_bytes()))).convert("RGB")


def scrivi_varianti(im, nome):
    """Salva la foto in docs/foto/ alle LARGHEZZE; restituisce larghezza e altezza della più grande."""
    for w in LARGHEZZE:
        copia = im
        if copia.width > w:
            copia = copia.resize((w, round(copia.height * w / copia.width)), Image.LANCZOS)
        if w == LARGHEZZE[0]:  # rimpicciolendo molto si perde nitidezza: un velo di contrasto sui bordi
            copia = copia.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=2))
        for qualita in (78, 72, 66, 60):
            buf = io.BytesIO()
            copia.save(buf, "WEBP", quality=qualita, method=6)
            if buf.tell() <= PESO_MAX[w]:
                break
        (FOTO / f"{nome}-{w}.webp").write_bytes(buf.getvalue())
    larg = min(im.width, LARGHEZZE[-1])
    return larg, round(im.height * larg / im.width)


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


MINIATURA = 200  # miniature della galleria nella scheda: riquadri da 64 px, nitidi anche su schermi 3x


def miniatura(foto):
    """Variante piccola di una foto per le miniature della galleria, ricavata da quella da 800 px.
    Si rifà quando la foto di partenza cambia, per esempio dopo un ritocco. Restituisce il nome del file."""
    sorgente = FOTO / f"{foto}-800.webp"
    dest = FOTO / f"{foto}-{MINIATURA}.webp"
    if not dest.exists() or dest.stat().st_mtime < sorgente.stat().st_mtime:
        with Image.open(sorgente) as im:
            im = im.convert("RGB")
            im.thumbnail((MINIATURA, MINIATURA * 3), Image.LANCZOS)
            im.save(dest, "WEBP", quality=72, method=6)
    return dest.name


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
