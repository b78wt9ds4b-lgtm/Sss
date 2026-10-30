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
- origine: il percorso della foto su WordPress (es. «2026/10/IMG_6651.jpg»);
  così la regola resta sulla foto giusta anche se sul negozio cambiano
  l'ordine o il numero delle foto
- frontali: per i quadri, una foto dritta e pulita della sola tela,
  ricavata dagli angoli indicati (in frazioni) e messa per prima;
  con "sostituisci" prende il posto della foto di partenza, con "margine"
  si taglia un po' di più sui bordi (frazione del lato corto)

Con --per-wordpress non tocca il sito: salva in per-wordpress/foto/ le foto
ritoccate in JPEG grande, da caricare sul negozio WordPress, con l'elenco di
cosa sostituire (ELENCO.md).
Con --alta-risoluzione fa lo stesso alla risoluzione piena degli originali, in
JPEG di qualità massima, con i file chiamati come i pezzi e un ELENCO.txt, in
foto-alta-risoluzione/ (non pubblicata: è da comprimere e mandare così com'è).

Richiede Pillow e numpy (pip install pillow numpy).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageFilter

from immagini import originale, scrivi_varianti

RADICE = Path(__file__).resolve().parent.parent
FOTO = RADICE / "docs" / "foto"
DATI = RADICE / "data"
TEMA = "https://www.darthome.it/wp-content/themes/dart-child/assets/img/"
PER_WP = RADICE / "per-wordpress" / "foto"
LATO_WP = 2048  # lato lungo delle copie per WordPress: basta per lo zoom e pesa poco
ALTA = RADICE / "foto-alta-risoluzione"


# ---------------------------------------------------------------- originali

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
    return scrivi_varianti(im, nome)


def salva_copia(im, nome, alta=False):
    """Copia JPEG da caricare sul negozio al posto della foto vecchia. Con alta: risoluzione
    piena, qualità massima, colori senza sottocampionamento e profilo sRGB dichiarato."""
    cartella = ALTA if alta else PER_WP
    cartella.mkdir(parents=True, exist_ok=True)
    if alta:
        srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        im.save(cartella / f"{nome}.jpg", "JPEG", quality=95, subsampling=0, optimize=True, progressive=True,
                icc_profile=srgb)
        return im.size
    im = im.copy()
    im.thumbnail((LATO_WP, LATO_WP), Image.LANCZOS)
    im.save(cartella / f"{nome}.jpg", "JPEG", quality=86, optimize=True, progressive=True)
    return im.size


def nome_leggibile(p, pos, nuova):
    """«Bordeaux in fiore - foto principale»: per chi riceve le foto, il nome del pezzo dice già tutto."""
    dove = "nuova foto principale" if nuova else ("foto principale" if pos == 1 else f"foto {pos}")
    return re.sub(r'[\\/:*?"<>|]', "-", f"{p['nome']} - {dove}")


def scrivi_elenco(righe):
    """per-wordpress/foto/ELENCO.md: per ogni file, il pezzo e cosa farne sul negozio."""
    testo = [
        "# Foto ritoccate da caricare su WordPress",
        "",
        "Generato da `python3 strumenti/ritocca.py --per-wordpress`. «Foto sul negozio» è il nome",
        "della foto nella Libreria media; la posizione conta la prima foto della scheda come 1ª.",
        "",
        "| Pezzo | Foto sul negozio | Cosa fare | File | Perché |",
        "|---|---|---|---|---|",
    ]
    for p, pos, origine, nuova, file, motivo, _ in righe:
        pezzo = f"{p['nome']} (ID {p['id']})" + ("" if p["disponibile"] else " · venduto, facoltativo")
        if nuova:
            foto = f"nessuna: è una foto in più, ricavata da {Path(origine).stem}"
            azione = "Caricarla come immagine principale; quella di adesso passa nella galleria"
        else:
            foto = f"{Path(origine).stem} · " + ("immagine principale" if pos == 1 else f"{pos}ª foto")
            azione = "Sostituirla"
        testo.append(f"| {pezzo} | {foto} | {azione} | `{file}` | {motivo} |")
    (PER_WP / "ELENCO.md").write_text("\n".join(testo) + "\n", encoding="utf-8")


def scrivi_elenco_alta(righe):
    """foto-alta-risoluzione/ELENCO.txt: testo semplice, si apre ovunque."""
    testo = [
        "DART - foto ritoccate in alta risoluzione",
        "",
        "Ogni foto è alla risoluzione piena del file caricato sul negozio, in JPEG di qualità massima.",
        "I ritocchi sono leggeri: il pezzo è lo stesso, si vede meglio.",
        "Generato da: python3 strumenti/ritocca.py --alta-risoluzione",
    ]
    for p, pos, origine, nuova, file, motivo, (w, h) in righe:
        if nuova:
            dove = f"foto in più, da mettere come immagine principale (ricavata da {Path(origine).stem})"
        else:
            dove = f"al posto di {Path(origine).stem}, " + ("l’immagine principale" if pos == 1 else f"la {pos}ª foto")
        testo += ["", file, f"  Pezzo: {p['nome']} (ID {p['id']})" + ("" if p["disponibile"] else ", venduto"),
                  f"  Sul negozio: {dove}", f"  Ritocco: {motivo[:1].lower() + motivo[1:]}", f"  Dimensioni: {w} × {h} pixel"]
    (ALTA / "ELENCO.txt").write_text("\n".join(testo) + "\n", encoding="utf-8")


def cancella(nome):
    """Toglie da docs/foto/ tutte le versioni di una foto (WebP e JPEG del catalogo)."""
    for f in FOTO.iterdir():
        if re.fullmatch(re.escape(nome) + r"-\d+\.webp|" + re.escape(nome) + r"(-[0-9a-f]{8})?\.jpg", f.name):
            f.unlink()


# ---------------------------------------------------------------- principale

def proporzione_da_misure(misure):
    """«H 50 · L 70 · P 3 cm» -> 70/50."""
    h = re.search(r"H\s*([\d.,]+)", misure or "")
    l = re.search(r"L\s*([\d.,]+)", misure or "")
    if not (h and l):
        return None
    return float(l.group(1).replace(",", ".")) / float(h.group(1).replace(",", "."))


def posizione(p, f):
    """Posizione della foto nella scheda del negozio: 1 = immagine principale."""
    return [x for x in p["foto"] if not x.get("derivata")].index(f) + 1


def trova(pezzi, nome, origine):
    """La foto a cui si applica una regola. Con «origine» la si cerca per il suo percorso
    su WordPress, che non cambia se sul negozio le foto vengono tolte o riordinate."""
    for p in pezzi:
        for f in p["foto"]:
            if f.get("derivata"):
                continue
            if (f.get("origine", "").endswith("/" + origine)) if origine else f["file"] == nome:
                return p, f
    return None, None


def main():
    regole = json.loads((DATI / "ritocchi.json").read_text(encoding="utf-8"))
    pezzi = json.loads((DATI / "pezzi.json").read_text(encoding="utf-8"))
    temi = {"hero": TEMA + "hero.jpg", "negozio": TEMA + "negozio.jpg"}
    alta = "--alta-risoluzione" in sys.argv
    per_wp = "--per-wordpress" in sys.argv or alta
    righe = []  # per l'elenco di --per-wordpress e --alta-risoluzione

    for nome, r in regole["foto"].items():
        p, f = trova(pezzi, nome, r.get("origine"))
        if f is None and nome not in temi:
            stato = "già tolta dal negozio" if r.get("togli") else "foto non trovata, salto"
            print(f"! {nome}: {stato}", file=sys.stderr)
            continue
        if r.get("togli"):
            if per_wp:
                print(f"- da togliere sul negozio: {f['origine']}")
                continue
            p["foto"].remove(f)
            cancella(f["file"])
            print(f"- tolta {f['file']}")
            continue
        nome = f["file"] if f else nome
        im = originale(f["origine"] if f else temi[nome])
        if "ritaglio" in r:
            x0, y0, x1, y1 = r["ritaglio"]
            im = im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))
        im = tono(im, r.get("luce", 1.0), r.get("bilanciamento", 0.0))
        if per_wp:
            if f:
                pos = posizione(p, f)
                file = nome_leggibile(p, pos, False) if alta else nome
                misure = salva_copia(im, file, alta)
                righe.append((p, pos, f["origine"], False, f"{file}.jpg", r.get("motivo", ""), misure))
            continue
        w, h = salva(im, nome)
        if f:
            f.update(w=w, h=h)
        print(f"· ritoccata {nome}")

    for slug, r in regole["frontali"].items():
        p, sorgente = trova(pezzi, r["da"], r.get("origine"))
        if sorgente is None or p["slug"] != slug:
            print(f"! {slug}: foto di partenza non trovata, salto", file=sys.stderr)
            continue
        im = originale(sorgente["origine"])
        tela, misurata = frontale(im, r["angoli"], proporzione_da_misure(p["misure"]), r.get("margine", 0.006))
        tela = tono(tela, r.get("luce", 1.0), r.get("bilanciamento", 0.0), cast=dominante(im))
        if per_wp:
            pos, nuova = posizione(p, sorgente), not r.get("sostituisci")
            if alta:
                nome = nome_leggibile(p, pos, nuova)
            else:
                nome = f"{slug}-frontale" if nuova else sorgente["file"]
            misure = salva_copia(tela, nome, alta)
            righe.append((p, pos, sorgente["origine"], nuova, f"{nome}.jpg", r.get("motivo", ""), misure))
            continue
        if r.get("sostituisci"):
            nome = sorgente["file"]
            w, h = salva(tela, nome)
            sorgente.update(w=w, h=h)
        else:
            nome = f"{slug}-frontale"
            w, h = salva(tela, nome)
            voce = {"file": nome, "w": w, "h": h, "origine": sorgente["origine"], "derivata": True}
            p["foto"] = [voce] + [f for f in p["foto"] if f["file"] != nome]
        attesa = proporzione_da_misure(p["misure"])
        avviso = ""
        if attesa and abs(attesa / misurata - 1) >= 0.05:
            avviso = f"  (attenzione: proporzioni dalla foto {misurata:.2f}, dalle misure {attesa:.2f}: controlla le misure)"
        print(f"· frontale {nome}{avviso}")

    if per_wp:
        # via le foto di un giro precedente che non servono più (per esempio perché sul negozio la
        # foto di partenza è già stata cambiata): caricarle rimetterebbe al suo posto quella vecchia
        fatte = {r[4] for r in righe}
        for vecchia in (ALTA if alta else PER_WP).glob("*.jpg"):
            if vecchia.name not in fatte:
                vecchia.unlink()
        righe.sort(key=lambda r: (r[0]["nome"], r[1]))
        if alta:
            scrivi_elenco_alta(righe)
        else:
            scrivi_elenco(righe)
        cartella = ALTA if alta else PER_WP
        print(f"· {len(righe)} foto in {cartella.relative_to(RADICE)}, elenco in {'ELENCO.txt' if alta else 'ELENCO.md'}")
        return
    (DATI / "pezzi.json").write_text(json.dumps(pezzi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
