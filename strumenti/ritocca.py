"""Ritocca le foto meno riuscite, partendo dagli originali ad alta risoluzione.

    python3 strumenti/ritocca.py

Legge data/ritocchi.json, scarica gli originali dal vecchio sito in
.originali/ (cartella non pubblicata), riscrive le foto in docs/foto/ e
aggiorna data/pezzi.json. Poi va rigenerato il sito con costruisci.py.
Se rilanci importa.py, rilancia anche questo.

I ritocchi sono leggeri e non cambiano il pezzo: lo mostrano meglio.
- togli: la foto non compare più sul sito
- ritaglio: [sinistra, alto, destra, basso], in frazioni della foto
- luce: schiarisce le foto scure (1 = invariata, 1.15 = più luminosa)
- bilanciamento: toglie in parte la dominante gialla della luce di casa
  (0 = niente, 1 = del tutto)
- frontali: per i quadri, una foto dritta e pulita della sola tela,
  ricavata dagli angoli indicati (in frazioni) e messa per prima;
  con "sostituisci" prende il posto della foto di partenza, con "margine"
  si taglia un po' di più sui bordi (frazione del lato corto)

Richiede Pillow e numpy (pip install pillow numpy).
"""
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

RADICE = Path(__file__).resolve().parent.parent
ORIGINALI = RADICE / ".originali"
FOTO = RADICE / "docs" / "foto"
DATI = RADICE / "data"
TEMA = "https://www.darthome.it/wp-content/themes/dart-child/assets/img/"
LARGHEZZE = (600, 1200)


# ---------------------------------------------------------------- originali

def originale(nome, url):
    ORIGINALI.mkdir(exist_ok=True)
    trovati = [f for f in ORIGINALI.iterdir() if f.stem == nome]
    if trovati:
        dati = trovati[0].read_bytes()
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ritocca DART)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dati = r.read()
        (ORIGINALI / f"{nome}{Path(url).suffix.lower() or '.jpg'}").write_bytes(dati)
    return ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")


# ---------------------------------------------------------------- geometria

def omografia(da, a):
    """Coefficienti per Image.transform(PERSPECTIVE): ogni punto di `a` (foto finale) va preso da `da`."""
    righe, noti = [], []
    for (x, y), (u, v) in zip(a, da):
        righe.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        righe.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        noti += [u, v]
    return np.linalg.solve(np.array(righe, float), np.array(noti, float)).tolist()


def affina_lato(arr, p0, p1, banda):
    """Cerca il bordo vero vicino al segmento p0-p1 e ne restituisce la retta (punto, direzione)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-d[1], d[0]])
    t = np.arange(-banda, banda + 1)
    punti = []
    for s in np.linspace(0.08, 0.92, 80):
        p = p0 + s * (p1 - p0)
        xy = p + t[:, None] * n
        xs = np.clip(np.round(xy[:, 0]).astype(int), 0, arr.shape[1] - 1)
        ys = np.clip(np.round(xy[:, 1]).astype(int), 0, arr.shape[0] - 1)
        salto = np.abs(np.diff(arr[ys, xs], axis=0)).sum(1)
        salto = np.convolve(salto, [1, 2, 3, 2, 1], "same")
        punti.append(p + (t[salto.argmax()] + 0.5) * n)
    punti = np.array(punti)
    for _ in range(3):  # retta ai minimi quadrati, scartando i punti lontani
        centro = punti.mean(0)
        _, _, v = np.linalg.svd(punti - centro)
        direzione = v[0]
        dist = np.abs((punti - centro) @ np.array([-direzione[1], direzione[0]]))
        soglia = max(1.5, 2.5 * np.median(dist))
        if (dist <= soglia).sum() < 10:
            break
        punti = punti[dist <= soglia]
    return centro, direzione


def incrocio(r1, r2):
    (p, d), (q, e) = r1, r2
    t = np.linalg.solve(np.array([d, -e]).T, q - p)[0]
    return p + t * d


def frontale(im, angoli, proporzione_attesa=None, margine=0.006):
    """Raddrizza la tela: angoli (frazioni) in ordine alto-sx, alto-dx, basso-dx, basso-sx."""
    w, h = im.size
    stima = [np.array([x * w, y * h]) for x, y in angoli]
    arr = np.asarray(im.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32)
    banda = int(0.03 * min(w, h))
    lati = [affina_lato(arr, stima[i], stima[(i + 1) % 4], banda) for i in range(4)]
    vertici = [incrocio(lati[(i - 1) % 4], lati[i]) for i in range(4)]
    for v, s in zip(vertici, stima):  # se l'affinamento sbanda, restano gli angoli indicati
        if np.linalg.norm(v - s) > 2 * banda:
            vertici = stima
            break
    alto, basso = np.linalg.norm(vertici[1] - vertici[0]), np.linalg.norm(vertici[2] - vertici[3])
    sx, dx = np.linalg.norm(vertici[3] - vertici[0]), np.linalg.norm(vertici[2] - vertici[1])
    misurata = (alto + basso) / (sx + dx)
    proporzione = misurata
    # con le misure del pezzo le proporzioni vengono esatte; se però la foto
    # dice tutt'altro (oltre il 5%), le misure sono probabilmente sbagliate
    if proporzione_attesa and abs(proporzione_attesa / misurata - 1) < 0.05:
        proporzione = proporzione_attesa
    larg = round(max(alto, basso))
    alt = round(larg / proporzione)
    coeff = omografia([tuple(v) for v in vertici], [(0, 0), (larg, 0), (larg, alt), (0, alt)])
    tela = im.transform((larg, alt), Image.PERSPECTIVE, coeff, Image.BICUBIC)
    m = round(margine * min(larg, alt))  # via l'ultimo filo di muro sui bordi
    return tela.crop((m, m, larg - m, alt - m)), misurata



# ---------------------------------------------------------------- colore e luce

def dominante(im):
    """Colore medio delle zone chiare e quasi neutre (muri, tela grezza), normalizzato."""
    piccola = im.copy()
    piccola.thumbnail((500, 500))
    a = np.asarray(piccola).astype(np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    sat = (a.max(2) - a.min(2)) / (a.max(2) + 1e-6)
    neutri = (sat < 0.18) & (lum > 0.45)
    if neutri.sum() < 300:
        return np.ones(3)
    m = a[neutri].mean(0)
    return m / m.mean()


def tono(im, luce=1.0, bilanciamento=0.0, cast=None, livelli=0.5):
    a = np.asarray(im).astype(np.float32) / 255
    if bilanciamento:
        cast = dominante(im) if cast is None else cast
        a = a * (1 / cast) ** bilanciamento
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    basso, alto = np.percentile(lum, 0.2), np.percentile(lum, 99.8)
    if alto - basso < 0.97:  # allarga i livelli solo se la foto è spenta, e solo a metà
        a = a + livelli * ((a - basso) / (alto - basso) - a)
    a = np.clip(a, 0, 1)
    if luce != 1.0:
        a = a ** (1 / luce)
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8))


# ---------------------------------------------------------------- salvataggio

def salva(im, nome):
    for w in LARGHEZZE:
        copia = im.copy()
        if copia.width > w:
            copia = copia.resize((w, round(copia.height * w / copia.width)), Image.LANCZOS)
        copia = copia.filter(ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=2))
        copia.save(FOTO / f"{nome}-{w}.webp", "WEBP", quality=80, method=6)
    larg = min(im.width, LARGHEZZE[-1])
    return larg, round(im.height * larg / im.width)


def cancella(nome):
    """Toglie da docs/foto/ tutte le versioni di una foto (WebP e JPEG del catalogo)."""
    for f in FOTO.iterdir():
        if re.fullmatch(re.escape(nome) + r"-(600|1200)\.webp|" + re.escape(nome) + r"(-[0-9a-f]{8})?\.jpg", f.name):
            f.unlink()


# ---------------------------------------------------------------- principale

def proporzione_da_misure(misure):
    """«H 50 · L 70 · P 3 cm» -> 70/50."""
    h = re.search(r"H\s*([\d.,]+)", misure or "")
    l = re.search(r"L\s*([\d.,]+)", misure or "")
    if not (h and l):
        return None
    return float(l.group(1).replace(",", ".")) / float(h.group(1).replace(",", "."))


def main():
    regole = json.loads((DATI / "ritocchi.json").read_text(encoding="utf-8"))
    pezzi = json.loads((DATI / "pezzi.json").read_text(encoding="utf-8"))
    per_nome = {f["file"]: (p, f) for p in pezzi for f in p["foto"]}
    temi = {"hero": TEMA + "hero.jpg", "negozio": TEMA + "negozio.jpg"}

    for nome, r in regole["foto"].items():
        if nome not in per_nome and nome not in temi:
            print(f"! {nome}: foto non trovata, salto", file=sys.stderr)
            continue
        if r.get("togli"):
            if nome in per_nome:
                p, f = per_nome[nome]
                p["foto"].remove(f)
            cancella(nome)
            print(f"- tolta {nome}")
            continue
        url = per_nome[nome][1]["origine"] if nome in per_nome else temi[nome]
        im = originale(nome, url)
        if "ritaglio" in r:
            x0, y0, x1, y1 = r["ritaglio"]
            im = im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))
        im = tono(im, r.get("luce", 1.0), r.get("bilanciamento", 0.0))
        w, h = salva(im, nome)
        if nome in per_nome:
            per_nome[nome][1].update(w=w, h=h)
        print(f"· ritoccata {nome}")

    for slug, r in regole["frontali"].items():
        p = next(q for q in pezzi if q["slug"] == slug)
        sorgente = next(f for f in p["foto"] if f["file"] == r["da"])
        im = originale(r["da"], sorgente["origine"])
        tela, misurata = frontale(im, r["angoli"], proporzione_da_misure(p["misure"]), r.get("margine", 0.006))
        tela = tono(tela, r.get("luce", 1.0), r.get("bilanciamento", 0.0), cast=dominante(im))
        if r.get("sostituisci"):
            nome = r["da"]
            w, h = salva(tela, nome)
            sorgente.update(w=w, h=h)
        else:
            nome = f"{slug}-frontale"
            w, h = salva(tela, nome)
            voce = {"file": nome, "w": w, "h": h, "origine": sorgente["origine"]}
            p["foto"] = [voce] + [f for f in p["foto"] if f["file"] != nome]
        attesa = proporzione_da_misure(p["misure"])
        avviso = ""
        if attesa and abs(attesa / misurata - 1) >= 0.05:
            avviso = f"  (attenzione: proporzioni dalla foto {misurata:.2f}, dalle misure {attesa:.2f}: controlla le misure)"
        print(f"· frontale {nome}{avviso}")

    (DATI / "pezzi.json").write_text(json.dumps(pezzi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
