"""Costruisce le pagine HTML del sito in docs/ a partire da data/*.json.

    python3 strumenti/costruisci.py

Le pagine si generano con la sola libreria standard. Se è installato
Pillow (pip install pillow) vengono create anche le anteprime per i
social e le foto JPEG per il catalogo prodotti (vedi strumenti/immagini.py).
Foto, caratteri, stile.css e sito.js stanno già in docs/ e non vengono
toccati: qui si generano le pagine, sitemap.xml, robots.txt e il catalogo
prodotti per Google e Meta (feed-prodotti.xml).
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

RADICE = Path(__file__).resolve().parent.parent
DOCS = RADICE / "docs"
DATI = RADICE / "data"

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import immagini
except ImportError:  # manca Pillow: niente anteprime social, il sito funziona lo stesso
    immagini = None


def leggi(nome):
    return json.loads((DATI / nome).read_text(encoding="utf-8"))


NEGOZIO = leggi("negozio.json")
PEZZI = leggi("pezzi.json")
DOMANDE = leggi("domande.json")
RECENSIONI = leggi("recensioni.json")
# Descrizioni riscritte per il nuovo sito: hanno la precedenza su quelle importate.
DESCRIZIONI = leggi("descrizioni.json")
for _p in PEZZI:
    _p["descrizione"] = DESCRIZIONI.get(_p["slug"], _p["descrizione"])
# Dal più recente al più vecchio: le pagine mostrano prima le novità.
PEZZI.sort(key=lambda p: p.get("pubblicato", ""), reverse=True)
DISPONIBILI = [p for p in PEZZI if p["disponibile"]]
VENDUTI = [p for p in PEZZI if not p["disponibile"]]

BASE = NEGOZIO["url"].rstrip("/")
CORRIERI = "BRT o Poste Italiane"
REGALI_MAX = 150  # € — soglia della sezione «idee regalo»

# chiave interna -> percorso (uguale al vecchio sito), nomi e testi
CATEGORIE = {
    "mobili": {
        "percorso": "categoria/mobili/", "nome": "Mobili",
        "descrittore": "mobile d’epoca restaurato e dipinto a mano",
        "social": "Mobile d’epoca · pezzo unico", "condizione": "refurbished", "affine": "quadri",
        "testo": "Credenze, cassettiere, armadi, tavoli e sedute d’epoca: restaurati e dipinti a mano, uno alla volta.",
    },
    "quadri": {
        "percorso": "categoria/quadri-e-ritratti/", "nome": "Quadri",
        "descrittore": "quadro originale dipinto a mano",
        "social": "Quadro originale · pezzo unico", "condizione": "new", "affine": "mobili",
        "testo": "Dipinti originali ad acrilico su tela e su legno, firmati. Composizioni floreali e ritratti.",
    },
    "sculture": {
        "percorso": "categoria/altro-arredamento/", "nome": "Sculture",
        "descrittore": "scultura in legno dipinta a mano",
        "social": "Scultura · pezzo unico", "condizione": "new", "affine": "quadri",
        "testo": "Piccole sculture in legno dipinto, nate anche dai frammenti dei mobili restaurati.",
    },
}

SPEDIZIONI = [
    ("Credenze, armadi e pezzi voluminosi", "150 €"),
    ("Mobile grande", "100 €"),
    ("Tavolino", "50 €"),
    ("Quadro grande", "35 €"),
    ("Quadro piccolo", "20 €"),
    ("Oggetto piccolo", "15 €"),
    ("Sicilia e Sardegna", "+50 €"),
]

e = html.escape


# ---------------------------------------------------------------- utilità

def euro(valore):
    if valore is None:
        return ""
    if valore == int(valore):
        return f"{valore:,.0f}".replace(",", ".") + " €"
    return f"{valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def numero(testo):
    """«150,00 €» -> 150.0; None se nel testo non c'è un importo."""
    m = re.search(r"\d[\d.]*(,\d+)?", testo or "")
    return float(m.group(0).replace(".", "").replace(",", ".")) if m else None


def tempi(p):
    """Tempi di consegna indicativi, come nelle condizioni di vendita."""
    costo = numero(p.get("spedizione"))
    if costo is None:
        return ""
    return "di solito entro due settimane" if costo >= 100 else "di solito entro dieci giorni lavorativi"


def testo_semplice(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def riassunto(s, n=155):
    s = testo_semplice(s)
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",.;:—") + "…"


def prima_frase(s):
    return re.split(r"(?<=[.!?])\s", testo_semplice(s))[0] if s else ""


def foto_url(r, nome, w):
    return f"{r}foto/{nome}-{w}.webp"


def immagine(r, foto, alt, sizes, lazy=True):
    """<img> con le due larghezze generate da importa.py."""
    caricamento = 'loading="lazy"' if lazy else 'fetchpriority="high"'
    return (f'<img src="{foto_url(r, foto["file"], 600)}" '
            f'srcset="{foto_url(r, foto["file"], 600)} 600w, {foto_url(r, foto["file"], 1200)} {foto["w"]}w" '
            f'sizes="{sizes}" width="{foto["w"]}" height="{foto["h"]}" alt="{e(alt)}" {caricamento} decoding="async">')


def trova_foto(nome):
    return next((f for p in PEZZI for f in p["foto"] if f["file"] == nome), PEZZI[0]["foto"][0])


def wa(messaggio):
    return f"https://wa.me/{NEGOZIO['whatsapp']}?text={quote(messaggio)}"


def wa_condividi(testo):
    """Link WhatsApp senza numero: chi lo apre sceglie a chi mandarlo."""
    return f"https://wa.me/?text={quote(testo)}"


def tel():
    return "tel:+39" + NEGOZIO["telefono"].replace(" ", "")


def corrente(condizione):
    return ' aria-current="page"' if condizione else ""


def _svg(contenuto, riempito=False):
    stile = ('fill="currentColor"' if riempito else
             'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"')
    return f'<svg viewBox="0 0 24 24" {stile} aria-hidden="true">{contenuto}</svg>'


ICONE = {
    "menu": _svg('<path d="M4 7h16M4 12h16M4 17h16"/>'),
    "instagram": _svg('<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".9" fill="currentColor"/>'),
    "whatsapp": _svg('<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.3-.4.8-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.8-1.2.2-.6.2-1.1.1-1.2l-.4-.2Z"/>', riempito=True),
    "pennello": _svg('<path d="M18.4 2.6a2 2 0 0 1 2.9 2.9L11 15.8 8.2 13Z"/><path d="M8.2 13c-2.3 0-4 1.8-4 4 0 1.6-1 2.6-2.2 3 4.8 1 9-.5 9-4.2Z"/>'),
    "unico": _svg('<path d="M6 3h12l3 5-9 13L3 8Z"/><path d="M3 8h18M12 21 8 8l4-5 4 5Z"/>'),
    "furgone": _svg('<path d="M2 6h12v10H2zM14 9h4l4 4v3h-8z"/><circle cx="6" cy="17.5" r="1.8"/><circle cx="17.5" cy="17.5" r="1.8"/>'),
    "carrello": _svg('<path d="M6 7h12l-1 13H7Z"/><path d="M9 7a3 3 0 0 1 6 0"/>'),
    "camera": _svg('<path d="M4 8h3l2-2.5h6L17 8h3v11H4Z"/><circle cx="12" cy="13" r="3.2"/>'),
    "condividi": _svg('<path d="M12 3v12M7.5 7.5 12 3l4.5 4.5"/><path d="M5 12v8h14v-8"/>'),
    "lucchetto": _svg('<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>'),
    "reso": _svg('<path d="M4 9h11a5 5 0 0 1 0 10H8"/><path d="M8 5 4 9l4 4"/>'),
    "scudo": _svg('<path d="M12 3 4.5 6v5.5c0 4.7 3.2 8.2 7.5 9.5 4.3-1.3 7.5-4.8 7.5-9.5V6Z"/><path d="m8.8 12 2.2 2.2 4.4-4.4"/>'),
    "pacco": _svg('<path d="M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5Z"/><path d="M3.5 7.5 12 12l8.5-4.5M12 12v9"/>'),
    "spunta": _svg('<path d="m5 12.5 4.5 4.5L19 7.5"/>'),
    "campanella": _svg('<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15Z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>'),
}


def _marchio(nome, titolo):
    svg = (RADICE / "strumenti" / "icone" / f"{nome}.svg").read_text(encoding="utf-8")
    return titolo, re.search(r'<path d="([^"]+)"', svg).group(1)


PAGAMENTI = [_marchio("visa", "Visa"), _marchio("mastercard", "Mastercard"),
             _marchio("applepay", "Apple Pay"), _marchio("googlepay", "Google Pay")]


def pagamenti_html(classe=""):
    marchi = "".join(
        f'<li title="{t}"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="{d}"/></svg>'
        f'<span class="sr">{t}</span></li>' for t, d in PAGAMENTI)
    return f'<ul class="pagamenti {classe}" aria-label="Metodi di pagamento accettati">{marchi}<li>Bonifico</li></ul>'


def rassicura_html():
    voci = ["Pagamento sicuro", "Reso entro 14 giorni", f"Spedizione con {CORRIERI}"]
    return '<ul class="rassicura">' + "".join(f"<li>{ICONE['spunta']}{v}</li>" for v in voci) + "</ul>"


# ---------------------------------------------------------------- anteprime social

def og_social(nome_file, foto, occhiello, titolo, prezzo="", nota="", alt=""):
    """Anteprima 1200×630 per i social; senza Pillow ripiega sulla foto WebP."""
    if immagini:
        return (immagini.anteprima_social(nome_file, foto, occhiello, titolo, prezzo, nota), 1200, 630, alt or titolo)
    f = trova_foto(foto) if foto not in ("hero", "negozio") else {"w": 1050, "h": 1400}
    return (f"foto/{foto}-1200.webp", f["w"], f["h"], alt or titolo)


OG_HOME = None  # calcolata in main()


# ---------------------------------------------------------------- impaginazione

def menu_voci(r):
    return [
        (f"{r}negozio/", "Tutti i pezzi", "negozio"),
        (f"{r}{CATEGORIE['mobili']['percorso']}", "Mobili", "mobili"),
        (f"{r}{CATEGORIE['quadri']['percorso']}", "Quadri", "quadri"),
        (f"{r}{CATEGORIE['sculture']['percorso']}", "Sculture", "sculture"),
        (f"{r}#domande" if r == "" else f"{r}index.html#domande", "Domande", "domande"),
        (f"{r}contatti/", "Contatti", "contatti"),
    ]


def pagina(*, percorso, titolo, descrizione, corpo, attivo="", og=None, og_tipo="website", og_extra="",
           dati_strutturati=None, classe_body="", wa_messaggio=None, indicizza=True):
    """Avvolge il corpo nel documento completo e lo scrive in docs/<percorso>."""
    r = "../" * percorso.count("/")
    canonico = BASE + "/" + (percorso[:-len("index.html")] if percorso.endswith("index.html") else percorso)
    og = og or OG_HOME
    voci = menu_voci(r)
    menu = "".join(f'<li><a href="{u}"{corrente(k == attivo)}>{t}</a></li>' for u, t, k in voci)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n'
                 for d in dati_strutturati or [])
    legali = "".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in NEGOZIO["pagine_legali"].items())
    pezzi_menu = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t, _ in voci[:4])
    wa_link = wa(wa_messaggio or "Ciao DART, vorrei qualche informazione.")
    robots = "" if indicizza else '<meta name="robots" content="noindex">\n'
    home = r or "./"
    documento = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titolo)}</title>
<meta name="description" content="{e(descrizione)}">
{robots}<link rel="canonical" href="{canonico}">
<meta property="og:type" content="{og_tipo}">
<meta property="og:site_name" content="DART">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="{e(titolo)}">
<meta property="og:description" content="{e(descrizione)}">
<meta property="og:url" content="{canonico}">
<meta property="og:image" content="{BASE}/{og[0]}">
<meta property="og:image:width" content="{og[1]}">
<meta property="og:image:height" content="{og[2]}">
<meta property="og:image:alt" content="{e(og[3])}">
{og_extra}<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F6F0E6">
<link rel="icon" type="image/png" href="{r}favicon.png">
<link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
<link rel="preload" href="{r}fonts/fraunces-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}fonts/inter-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}stile.css">
{ld}</head>
<body class="{classe_body}">
<a class="salta" href="#contenuto">Vai al contenuto</a>
<header class="testata">
  <div class="contenitore">
    <a class="marchio" href="{home}"><img src="{r}logo.png" alt="" width="32" height="32">DART</a>
    <nav class="menu" aria-label="Principale"><ul>{menu}</ul></nav>
    <div class="testata-azioni">
      <a class="icona-btn" href="{NEGOZIO['instagram']}" aria-label="DART su Instagram">{ICONE['instagram']}</a>
      <button class="icona-btn apri-menu" aria-expanded="false" aria-controls="menu-mobile" aria-label="Menu">{ICONE['menu']}</button>
    </div>
  </div>
  <nav class="menu-mobile" id="menu-mobile" aria-label="Principale" hidden><ul>{menu}</ul></nav>
</header>
<main id="contenuto">
{corpo}
</main>
<footer class="piede">
  <div class="contenitore">
    <div class="piede-griglia">
      <div>
        <a class="marchio" href="{home}"><img src="{r}logo.png" alt="" width="32" height="32">DART</a>
        <p>Mobili d’epoca restaurati e dipinti a mano, quadri originali e sculture. Dal laboratorio di Trieste a casa tua, in tutta Italia.</p>
      </div>
      <div>
        <h2>Pezzi</h2>
        <ul>{pezzi_menu}</ul>
      </div>
      <div>
        <h2>Contatti</h2>
        <ul>
          <li><a href="{wa('Ciao DART, vorrei qualche informazione.')}">WhatsApp {e(NEGOZIO['telefono'])}</a></li>
          <li><a href="mailto:{NEGOZIO['email']}">{e(NEGOZIO['email'])}</a></li>
          <li><a href="{NEGOZIO['instagram']}">Instagram</a> · <a href="{NEGOZIO['facebook']}">Facebook</a></li>
          <li>{e(NEGOZIO['indirizzo'])}, {e(NEGOZIO['citta'])}</li>
        </ul>
      </div>
      <div>
        <h2>Acquisti</h2>
        <ul>{legali}</ul>
      </div>
    </div>
    {pagamenti_html("pagamenti-scuri")}
    <div class="piede-legale">
      <p>{e(NEGOZIO['titolare'])} · {e(NEGOZIO['indirizzo'])}, {NEGOZIO['cap']} {e(NEGOZIO['citta'])} ({NEGOZIO['provincia']})</p>
      <p>P.IVA {NEGOZIO['piva']} · REA {NEGOZIO['rea']} · PEC {e(NEGOZIO['pec'])}</p>
      <p>Operazione non soggetta a IVA ai sensi dell’art. 1, commi 54-89, Legge 190/2014 — regime forfettario. I prezzi indicati sono finali. Vendita esclusivamente in Italia. © {date.today().year} DART</p>
    </div>
  </div>
</footer>
<a class="wa-flottante" href="{wa_link}" aria-label="Scrivici su WhatsApp">{ICONE['whatsapp']}</a>
<script src="{r}sito.js" defer></script>
</body>
</html>
"""
    dest = DOCS / percorso
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(documento, encoding="utf-8")
    return canonico


# ---------------------------------------------------------------- blocchi

def etichette(p):
    if not p["disponibile"]:
        return '<span class="etichetta etichetta-venduto">Venduto</span>'
    # «Nuovo» lo mostra sito.js solo nei 30 giorni dopo la messa in vendita
    nuovo = (f'<span class="etichetta etichetta-nuovo" data-nuovo="{p["pubblicato"]}" hidden>Nuovo</span>'
             if p.get("pubblicato") else "")
    return '<span class="etichetta">Pezzo unico</span>' + nuovo


def scheda_pezzo(r, p, sizes="(min-width: 1100px) 290px, (min-width: 760px) 31vw, 46vw"):
    foto = p["foto"]
    imgs = immagine(r, foto[0], p["nome"], sizes) if foto else ""
    if len(foto) > 1:
        imgs += immagine(r, foto[1], "", sizes)
    conta = (f'<span class="conta-foto">{ICONE["camera"]}{len(foto)}<span class="sr"> foto</span></span>'
             if len(foto) > 1 else "")
    sotto = f'<p class="sotto">{e(p["sottotitolo"])}</p>' if p["sottotitolo"] else ""
    prezzo = f'<span class="prezzo">{euro(p["prezzo"])}</span>' if p["prezzo"] and p["disponibile"] else ""
    classe = "pezzo" if p["disponibile"] else "pezzo venduto"
    return f"""<article class="{classe}">
  <a href="{r}pezzo/{p['slug']}/">
    <div class="pezzo-foto">{imgs}<div class="etichette">{etichette(p)}</div>{conta}</div>
    <h3>{e(p['nome'])}</h3>
    {sotto}
    <div class="riga"><span class="misure">{e(p['misure'])}</span>{prezzo}</div>
  </a>
</article>"""


def griglia(r, pezzi, classe="griglia"):
    return f'<div class="{classe}">' + "".join(scheda_pezzo(r, p) for p in pezzi) + "</div>"


def blocco_visita(r, titolo_tag="h2"):
    return f"""<div class="visita">
  <div>
    <p class="occhiello">Contatti</p>
    <{titolo_tag}>Hai una domanda <em>su un pezzo?</em></{titolo_tag}>
    <p>Misure, colori, altre foto o un video, tempi di consegna: scrivici su WhatsApp o per email, ti rispondiamo noi direttamente.</p>
    <dl>
      <div><dt>WhatsApp e telefono</dt><dd><a href="{tel()}">{e(NEGOZIO['telefono'])}</a></dd></div>
      <div><dt>Email</dt><dd><a href="mailto:{NEGOZIO['email']}">{e(NEGOZIO['email'])}</a></dd></div>
      <div><dt>Laboratorio</dt><dd>{e(NEGOZIO['indirizzo'])}, {NEGOZIO['cap']} {e(NEGOZIO['citta'])} · {e(NEGOZIO['orari_testo'])}</dd></div>
    </dl>
    <div class="azioni">
      <a class="btn btn-whatsapp" href="{wa('Ciao DART, vorrei qualche informazione su un pezzo.')}">{ICONE['whatsapp']}Scrivici su WhatsApp</a>
      <a class="btn btn-chiaro" href="mailto:{NEGOZIO['email']}">Scrivi un’email</a>
    </div>
  </div>
  <a class="mappa" href="{NEGOZIO['mappa']}">
    {immagine(r, {"file": "negozio", "w": 1050, "h": 1400}, "Il laboratorio DART in via Luigi Cadorna a Trieste", "(min-width: 760px) 50vw, 100vw")}
    <span>Il laboratorio a Trieste ↗</span>
  </a>
</div>"""


def blocco_info(r):
    righe = "".join(f"<li><span>{e(t)}</span><b>{e(v)}</b></li>" for t, v in SPEDIZIONI)
    legali = NEGOZIO["pagine_legali"]
    return f"""<ol class="passi-acquisto">
  <li><span class="num">1</span><div><strong>Scegli il tuo pezzo</strong><span>Foto, misure e prezzo finale sono nella scheda. Hai un dubbio? Chiedici altre foto o un video su WhatsApp.</span></div></li>
  <li><span class="num">2</span><div><strong>Paga in sicurezza</strong><span>Carta, Apple Pay, Google Pay o bonifico. Il prezzo è finale: nessuna IVA da aggiungere.</span></div></li>
  <li><span class="num">3</span><div><strong>Lo ricevi a casa</strong><span>Lo imballiamo a mano e lo spediamo con {CORRIERI}. Ti mandiamo il codice per seguirlo.</span></div></li>
</ol>
<div class="info">
  <div class="info-scheda">
    <h3>Spedizione</h3>
    <p>Tariffa fissa in base al pezzo, scritta in ogni scheda prima di pagare.</p>
    <ul>{righe}</ul>
  </div>
  <div class="info-scheda">
    <h3>Consegna</h3>
    <p>La consegna è <b>al piano strada</b>: il corriere lascia il pezzo all’ingresso dell’edificio, non lo porta su per le scale. Per i mobili più grandi, organizzati con qualcuno che ti aiuti a portarli in casa.</p>
    <p>Di solito i mobili arrivano entro due settimane; quadri, tavolini e oggetti entro dieci giorni lavorativi.</p>
    <p><a href="{legali['Spedizioni e consegna']}">Tutti i dettagli sulla spedizione</a></p>
  </div>
  <div class="info-scheda">
    <h3>Resi e garanzia</h3>
    <p>Hai 14 giorni dalla consegna per cambiare idea, senza dover spiegare il motivo. Ti rimborsiamo sullo stesso metodo di pagamento.</p>
    <p>Garanzia legale: 12 mesi sui mobili restaurati, 24 sui quadri.</p>
    <p><a href="{legali['Resi e rimborsi']}">Resi e rimborsi</a> · <a href="{legali['Recedere dal contratto qui']}">Recedere dal contratto</a></p>
  </div>
</div>
<div class="info-pagamenti"><span>Paghi con</span>{pagamenti_html()}</div>"""


def blocco_domande(r, titolo_tag="h2"):
    voci = "".join(f"<details><summary>{e(d['domanda'])}</summary><p>{e(d['risposta'])}</p></details>"
                   for d in DOMANDE)
    return f"""<div class="faq">
  <div>
    <p class="occhiello">Domande frequenti</p>
    <{titolo_tag}>Prima di comprare</{titolo_tag}>
    <p>Non trovi la risposta? <a href="{wa('Ciao DART, ho una domanda prima di comprare.')}">Scrivici su WhatsApp</a>.</p>
  </div>
  <div class="fisarmonica">{voci}</div>
</div>"""


def domande_ld():
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": d["domanda"],
         "acceptedAnswer": {"@type": "Answer", "text": d["risposta"]}} for d in DOMANDE]}


def blocco_recensioni(r):
    """Compare solo quando in data/recensioni.json ci sono recensioni vere."""
    if not RECENSIONI:
        return ""
    schede = ""
    for v in RECENSIONI:
        pezzo = next((p for p in PEZZI if p["slug"] == v.get("pezzo")), None)
        link = f' · <a href="{r}pezzo/{pezzo["slug"]}/">{e(pezzo["nome"])}</a>' if pezzo else ""
        chi = e(v["nome"]) + (", " + e(v["citta"]) if v.get("citta") else "")
        schede += (f'<figure class="recensione"><blockquote>“{e(v["testo"])}”</blockquote>'
                   f'<figcaption>{chi}{link}</figcaption></figure>')
    return f"""<section class="sezione">
  <div class="contenitore">
    <div class="sezione-testa"><div><p class="occhiello">Chi ha già comprato</p><h2>Cosa dicono di DART</h2></div></div>
    <div class="recensioni">{schede}</div>
  </div>
</section>"""


def blocco_chiusura():
    return f"""<div class="chiusura">
  <div class="chiusura-scheda">
    <h2>Hai una domanda <em>su un pezzo?</em></h2>
    <p>Misure, colori, altre foto o un video: scrivici, ti rispondiamo noi direttamente.</p>
    <div class="azioni">
      <a class="btn btn-whatsapp" href="{wa('Ciao DART, vorrei qualche informazione su un pezzo.')}">{ICONE['whatsapp']}Scrivici su WhatsApp</a>
      <a class="btn btn-chiaro" href="mailto:{NEGOZIO['email']}">Scrivi un’email</a>
    </div>
  </div>
  <div class="chiusura-scheda chiusura-scura">
    <h2>Vedi i nuovi pezzi <em>per primo</em></h2>
    <p>Ogni pezzo esiste una volta sola: quando è venduto, non torna. Scrivici «Avvisami» su WhatsApp e ti mandiamo i nuovi arrivi, oppure seguici su Instagram.</p>
    <div class="azioni">
      <a class="btn btn-crema" href="{wa('Ciao DART! Avvisatemi quando arrivano nuovi pezzi.')}">{ICONE['campanella']}Avvisami su WhatsApp</a>
      <a class="btn btn-contorno-chiaro" href="{NEGOZIO['instagram']}">{ICONE['instagram']}Seguici su Instagram</a>
    </div>
  </div>
</div>"""


def negozio_ld():
    giorni = {"Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday", "Th": "Thursday",
              "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday"}
    orari = [{"@type": "OpeningHoursSpecification", "dayOfWeek": [giorni[g] for g in o["giorni"]],
              "opens": a, "closes": c} for o in NEGOZIO["orari"] for a, c in o["fasce"]]
    return {
        "@context": "https://schema.org", "@type": "FurnitureStore", "@id": BASE + "/#negozio",
        "name": "DART", "description": NEGOZIO["descrizione"], "url": BASE + "/",
        "image": BASE + "/foto/hero-1200.webp", "logo": BASE + "/logo.png",
        "telephone": "+39 " + NEGOZIO["telefono"], "email": NEGOZIO["email"],
        "address": {"@type": "PostalAddress", "streetAddress": NEGOZIO["indirizzo"],
                    "postalCode": NEGOZIO["cap"], "addressLocality": NEGOZIO["citta"],
                    "addressRegion": NEGOZIO["provincia"], "addressCountry": "IT"},
        "openingHoursSpecification": orari, "priceRange": "€€",
        "sameAs": [NEGOZIO["instagram"], NEGOZIO["facebook"]],
        "vatID": "IT" + NEGOZIO["piva"],
    }


# ---------------------------------------------------------------- pagine

def home():
    r = ""
    copertine = {"mobili": "armadio-botanico-1", "quadri": "fiori-di-mezzanotte-1", "sculture": "pesce-doro-1"}
    categorie = ""
    for k, c in CATEGORIE.items():
        pezzi = [p for p in DISPONIBILI if p["categoria"] == k]
        prezzi = [p["prezzo"] for p in pezzi if p["prezzo"]]
        conta = f"{len(pezzi)} {'pezzo' if len(pezzi) == 1 else 'pezzi'}" + (f" · da {euro(min(prezzi))}" if prezzi else "")
        categorie += f"""<a class="categoria" href="{c['percorso']}">
  {immagine(r, trova_foto(copertine[k]), "", "(min-width: 640px) 33vw, 100vw")}
  <div><h3>{c['nome']}</h3><span>{conta}</span></div>
</a>"""

    regali = sorted((p for p in DISPONIBILI if p["prezzo"] and p["prezzo"] <= REGALI_MAX), key=lambda p: p["prezzo"])
    sezione_regali = ""
    if len(regali) >= 3:
        sezione_regali = f"""<section class="sezione">
  <div class="contenitore">
    <div class="sezione-testa">
      <div><p class="occhiello">Da regalare, o da regalarsi</p><h2>Idee regalo fino a {REGALI_MAX} €</h2>
      <p>Piccoli pezzi unici, dipinti a mano: un regalo che non si trova da nessun’altra parte.</p></div>
    </div>
    {griglia(r, regali[:8], "griglia griglia-4")}
  </div>
</section>"""

    sezione_venduti = ""
    if VENDUTI:
        con_foto = [p for p in VENDUTI if len(p["foto"]) > 1][:4]
        sezione_venduti = f"""<section class="sezione">
  <div class="contenitore">
    <div class="sezione-testa">
      <div><p class="occhiello">Già venduti</p><h2>{len(VENDUTI)} pezzi hanno già trovato casa</h2>
      <p>Ogni pezzo esiste una volta sola: quando è venduto, non torna. Ecco alcuni di quelli già partiti.</p></div>
      <a class="link-freccia" href="negozio/#venduti">Vedi tutti i venduti →</a>
    </div>
    {griglia(r, con_foto, "griglia griglia-4")}
  </div>
</section>"""

    corpo = f"""<section class="apertura">
  <div class="contenitore">
    <div>
      <p class="occhiello">Trieste · dal laboratorio</p>
      <h1>Mobili che <em>raccontano</em> qualcosa</h1>
      <p class="lead">Mobili d’epoca restaurati e dipinti a mano, quadri originali e piccole sculture. Ogni pezzo è unico e arriva a casa tua, in tutta Italia.</p>
      <div class="azioni">
        <a class="btn btn-scuro" href="negozio/">Guarda i {len(DISPONIBILI)} pezzi disponibili</a>
        <a class="btn btn-chiaro" href="#come-funziona">Come funziona</a>
      </div>
      {rassicura_html()}
    </div>
    <figure>
      {immagine(r, {"file": "hero", "w": 1050, "h": 1400}, "Un mobile dipinto a mano da DART, con uccelli sulle ante, e quadri originali alle pareti", "(min-width: 760px) 45vw, 100vw", lazy=False)}
      <figcaption>Restaurati e dipinti a mano a Trieste</figcaption>
    </figure>
  </div>
</section>
<section class="forza" aria-label="Perché DART">
  <ul>
    <li>{ICONE['unico']}<strong>Pezzi unici, dipinti a mano</strong><span>Niente repliche: ogni pezzo esiste in un solo esemplare.</span></li>
    <li>{ICONE['pacco']}<strong>Imballati a mano, uno per uno</strong><span>Spediti in tutta Italia con {CORRIERI}.</span></li>
    <li>{ICONE['lucchetto']}<strong>Prezzi finali, senza sorprese</strong><span>La spedizione è scritta in ogni scheda, prima di pagare.</span></li>
  </ul>
</section>
<section class="sezione">
  <div class="contenitore">
    <div class="sezione-testa">
      <div><p class="occhiello">Disponibili ora</p><h2>Gli ultimi arrivati</h2></div>
      <a class="link-freccia" href="negozio/">Vedi tutti i {len(DISPONIBILI)} pezzi →</a>
    </div>
    {griglia(r, DISPONIBILI[:8], "griglia griglia-4")}
  </div>
</section>
<section class="sezione sezione-alt">
  <div class="contenitore">
    <div class="sezione-testa"><div><p class="occhiello">Sfoglia</p><h2>Cosa cerchi?</h2></div></div>
    <div class="categorie">{categorie}</div>
  </div>
</section>
{sezione_regali}
<section class="sezione sezione-alt" id="come-funziona">
  <div class="contenitore">
    <div class="sezione-testa"><div><p class="occhiello">Come funziona</p><h2>Dall’ordine a casa tua</h2></div></div>
    {blocco_info(r)}
  </div>
</section>
{sezione_venduti}
{blocco_recensioni(r)}
<section class="sezione sezione-alt" id="laboratorio">
  <div class="contenitore storia">
    <figure>{immagine(r, trova_foto("armadio-botanico-3"), "Interno di un armadio restaurato e dipinto a mano da DART", "(min-width: 760px) 40vw, 100vw")}</figure>
    <div>
      <p class="occhiello">Il laboratorio</p>
      <h2>Un laboratorio, <em>prima</em> che un negozio</h2>
      <p>DART è la ditta artigiana di Dejana Mandic, a Trieste. Nasce dal recupero: mobili d’epoca che vengono smontati, puliti, restaurati e poi dipinti a mano, uno alla volta. Nessun pezzo è uguale a un altro, e nessuno viene rifatto.</p>
      <ol class="passi">
        <li><strong>Il recupero</strong><span>Scegliamo mobili d’epoca con una buona struttura e una storia da raccontare.</span></li>
        <li><strong>Il restauro</strong><span>Smontaggio, pulizia, consolidamento del legno: il mobile torna solido e funzionale.</span></li>
        <li><strong>La pittura</strong><span>Fiori, uccelli, foglie: il decoro è dipinto a mano e segue la forma del mobile.</span></li>
      </ol>
    </div>
  </div>
</section>
<section class="sezione" id="domande">
  <div class="contenitore">{blocco_domande(r)}</div>
</section>
<section class="sezione sezione-alt" id="contatti">
  <div class="contenitore">{blocco_chiusura()}</div>
</section>"""
    return pagina(percorso="index.html", titolo="DART — Mobili d’epoca dipinti a mano e quadri originali · Trieste",
                  descrizione=NEGOZIO["descrizione"], corpo=corpo, dati_strutturati=[negozio_ld(), domande_ld()])


def catalogo(percorso, titolo_h1, testo, pezzi, attivo, titolo, descrizione, og):
    r = "../" * percorso.count("/")
    chips = [(f"{r}negozio/", "Tutti", "negozio", len(DISPONIBILI))]
    for k, c in CATEGORIE.items():
        chips.append((f"{r}{c['percorso']}", c["nome"], k, sum(1 for p in DISPONIBILI if p["categoria"] == k)))
    chip_html = "".join(f'<a class="chip" href="{u}"{corrente(k == attivo)}>{t} <small>{n}</small></a>'
                        for u, t, k, n in chips)
    disponibili = [p for p in pezzi if p["disponibile"]]
    venduti = [p for p in pezzi if not p["disponibile"]]
    if disponibili:
        corpo_disp = griglia(r, disponibili)
    else:
        corpo_disp = (f'<p class="vuoto">In questo momento non ci sono pezzi disponibili qui. '
                      f'<a href="{wa("Ciao DART! Avvisatemi quando arrivano nuovi pezzi.")}">Scrivici</a> '
                      f'e ti avvisiamo quando ne arrivano di nuovi.</p>')
    corpo_venduti = ""
    if venduti:
        simile = wa("Ciao DART! Cerco un pezzo simile a quelli già venduti: avvisatemi quando arriva qualcosa.")
        corpo_venduti = f"""<section class="venduti" id="venduti" hidden>
  <h2>Hanno già trovato casa</h2>
  <p>Restano qui come portfolio. Ti piace qualcosa di simile? <a href="{simile}">Scrivici</a>: spesso abbiamo pezzi in lavorazione.</p>
  {griglia(r, venduti)}
</section>"""
        chip_html += (f'<button class="chip" type="button" data-solo-disponibili aria-pressed="false">'
                      f'Mostra anche i venduti <small>{len(venduti)}</small></button>')
    corpo = f"""<div class="contenitore catalogo-testa">
  <h1>{titolo_h1}</h1>
  <p>{e(testo)}</p>
  {rassicura_html()}
</div>
<nav class="filtri" aria-label="Categorie"><div class="contenitore">{chip_html}</div></nav>
<div class="contenitore catalogo-corpo">
  {corpo_disp}
  {corpo_venduti}
</div>
<section class="sezione sezione-alt" id="come-funziona">
  <div class="contenitore">
    <div class="sezione-testa"><div><p class="occhiello">Come funziona</p><h2>Dall’ordine a casa tua</h2></div></div>
    {blocco_info(r)}
  </div>
</section>"""
    elenco = {"@context": "https://schema.org", "@type": "CollectionPage", "name": titolo,
              "url": BASE + "/" + percorso.replace("index.html", ""),
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/pezzo/{p['slug']}/"}
                  for i, p in enumerate(disponibili)]}}
    return pagina(percorso=percorso, titolo=titolo, descrizione=descrizione, corpo=corpo,
                  attivo=attivo, og=og, dati_strutturati=[elenco])


def suggeriti(p):
    """Due pezzi della stessa categoria e due da abbinare; per i venduti, alternative simili."""
    altri = [q for q in DISPONIBILI if q["slug"] != p["slug"]]
    stessi = [q for q in altri if q["categoria"] == p["categoria"]]
    affini = [q for q in altri if q["categoria"] == CATEGORIE[p["categoria"]]["affine"]]
    if not p["disponibile"]:
        return (stessi + affini)[:4]
    scelta = stessi[:2] + affini[:2]
    resto = [q for q in stessi + affini + altri if q not in scelta]
    return (scelta + resto)[:4]


def scheda(p):
    percorso = f"pezzo/{p['slug']}/index.html"
    r = "../../"
    cat = CATEGORIE[p["categoria"]]
    url = f"{BASE}/pezzo/{p['slug']}/"
    foto = p["foto"]
    legali = NEGOZIO["pagine_legali"]
    descr = p["descrizione"] or (f"<p>{e(p['sottotitolo'])}</p>" if p["sottotitolo"] else "")

    nastro = "".join(
        f'<button type="button" data-grande="{foto_url(r, f["file"], 1200)}" aria-label="Ingrandisci la foto {i + 1}">'
        f'{immagine(r, f, p["nome"] + (" — foto " + str(i + 1) if i else ""), "(min-width: 900px) 55vw, 100vw", lazy=i > 0)}</button>'
        for i, f in enumerate(foto))
    miniature = ""
    if len(foto) > 1:
        miniature = '<div class="miniature">' + "".join(
            f'<button type="button" aria-label="Foto {i + 1}" aria-current="{str(i == 0).lower()}">'
            f'<img src="{foto_url(r, f["file"], 600)}" alt="" loading="lazy" width="64" height="80"></button>'
            for i, f in enumerate(foto)) + f'</div><p class="galleria-conta" aria-live="polite">1 di {len(foto)}</p>'

    costo = numero(p["spedizione"])
    compra = ""
    if p["disponibile"]:
        msg = f"Ciao DART, mi interessa «{p['nome']}» ({url}). Potreste mandarmi altre foto o un video?"
        if p["prezzo"] and NEGOZIO.get("acquisto_online"):
            compra = NEGOZIO["acquisto_online"].format(id=p["id"])
        prezzo = euro(p["prezzo"]) if p["prezzo"] else "Prezzo su richiesta"
        if compra:
            azioni = (f'<a class="btn btn-scuro btn-pieno btn-grande" href="{compra}">{ICONE["carrello"]}Acquista ora</a>'
                      f'<a class="btn btn-chiaro btn-pieno" href="{wa(msg)}">{ICONE["whatsapp"]}Chiedi altre foto o un video</a>')
        else:
            azioni = (f'<a class="btn btn-whatsapp btn-pieno btn-grande" href="{wa(msg)}">'
                      f'{ICONE["whatsapp"]}Chiedi il prezzo su WhatsApp</a>')
        nota_prezzo = "Prezzo finale"
        if costo is not None:
            nota_prezzo += f" · spedizione {euro(costo)} con {CORRIERI}"
        stima = tempi(p)
        stima_html = f'<p class="stima">{ICONE["furgone"]}Arriva {stima}, al piano strada</p>' if stima else ""
        garanzia = p["garanzia"] or "12 mesi"
        garanzie = f"""<ul class="garanzie">
        <li>{ICONE['lucchetto']}<span><strong>Pagamento sicuro</strong> con Stripe, o bonifico</span></li>
        <li>{ICONE['reso']}<span><strong>Reso entro 14 giorni</strong>, senza dover spiegare il motivo</span></li>
        <li>{ICONE['scudo']}<span><strong>Garanzia di {e(garanzia)}</strong> sul pezzo</span></li>
        <li>{ICONE['pacco']}<span><strong>Imballato a mano</strong> da noi, con codice di tracciamento</span></li>
      </ul>"""
        acquisto = f"""<div class="scheda-prezzo"><span class="prezzo">{e(prezzo)}</span>{etichette(p)}</div>
      <p class="prezzo-nota">{e(nota_prezzo)}</p>
      {stima_html}
      <div class="scheda-azioni">{azioni}</div>
      <p class="unico">Ne esiste uno solo: quando è venduto, non torna.</p>
      {garanzie}
      {pagamenti_html()}"""
        condividi = (f'<p class="condividi"><a href="{wa_condividi(p["nome"] + " — " + url)}" data-condividi '
                     f'data-titolo="{e(p["nome"])}" data-url="{url}">{ICONE["condividi"]}'
                     f'Condividilo con chi deve decidere con te</a></p>')
    else:
        msg = f"Ciao DART! Ho visto «{p['nome']}», che è già venduto. Avvisatemi se arriva qualcosa di simile."
        prezzo = ""
        acquisto = f"""<div class="scheda-prezzo">{etichette(p)}</div>
      <p class="prezzo-nota">Questo pezzo ha già trovato casa. Ne arrivano spesso di nuovi: vuoi che ti avvisiamo?</p>
      <div class="scheda-azioni">
        <a class="btn btn-whatsapp btn-pieno btn-grande" href="{wa(msg)}">{ICONE['campanella']}Avvisami se arriva qualcosa di simile</a>
        <a class="btn btn-chiaro btn-pieno" href="{r}{cat['percorso']}">Guarda i {cat['nome'].lower()} disponibili</a>
      </div>"""
        condividi = ""

    spec = []
    if p["misure"]:
        spec.append(("Misure", p["misure"]))
    if p["tecnica"]:
        spec.append(("Tecnica", p["tecnica"]))
    spec.append(("Disponibilità", "Pezzo unico disponibile" if p["disponibile"] else "Venduto"))
    if p["disponibile"]:
        if p["spedizione"]:
            spec.append(("Spedizione in Italia", p["spedizione"]))
        if p["spedizione_isole"]:
            spec.append(("Spedizione in Sicilia e Sardegna", p["spedizione_isole"]))
        spec.append(("Consegna", f"Al piano strada, con {CORRIERI}"))
        if tempi(p):
            spec.append(("Tempi", tempi(p).capitalize()))
    if p["garanzia"]:
        spec.append(("Garanzia", p["garanzia"]))
    spec_html = "".join(f"<li><span>{e(k)}</span><span>{e(v)}</span></li>" for k, v in spec)

    simili = suggeriti(p)
    simili_html = ""
    if simili:
        titolo_simili = "Potrebbe piacerti anche" if p["disponibile"] else "Disponibili ora"
        simili_html = f"""<section class="sezione sezione-alt">
  <div class="contenitore">
    <div class="sezione-testa"><h2>{titolo_simili}</h2><a class="link-freccia" href="{r}negozio/">Tutti i pezzi →</a></div>
    {griglia(r, simili, "griglia griglia-4")}
  </div>
</section>"""

    barra = ""
    if p["disponibile"]:
        if compra:
            bottone = f'<a class="btn btn-scuro" href="{compra}" tabindex="-1">Acquista</a>'
        else:
            bottone = f'<a class="btn btn-whatsapp" href="{wa(msg)}" tabindex="-1">{ICONE["whatsapp"]}Chiedi</a>'
        barra = f"""<div class="barra-acquisto" aria-hidden="true">
  <div><strong>{e(p['nome'])}</strong><span>{e(prezzo)} · pezzo unico</span></div>
  {bottone}
</div>"""

    sotto = f'<p class="sotto">{e(p["sottotitolo"])}</p>' if p["sottotitolo"] else ""
    misure = f'<p class="scheda-misure">{e(p["misure"])}</p>' if p["misure"] else ""
    corpo = f"""<div class="contenitore">
  <nav class="briciole" aria-label="Sei qui"><ol>
    <li><a href="{r}">Home</a></li>
    <li><a href="{r}{cat['percorso']}">{cat['nome']}</a></li>
    <li aria-current="page">{e(p['nome'])}</li>
  </ol></nav>
  <div class="scheda">
    <div class="galleria">
      <div class="galleria-nastro">{nastro}</div>
      {miniature}
    </div>
    <div class="scheda-corpo">
      <h1>{e(p['nome'])}</h1>
      {sotto}
      {misure}
      {acquisto}
      <div class="descrizione">{descr}</div>
      <ul class="specifiche">{spec_html}</ul>
      <div class="fisarmonica">
        <details><summary>Spedizione e consegna</summary>
          <p>Spediamo in tutta Italia con {CORRIERI}, a tariffa fissa in base al pezzo; per Sicilia e Sardegna c’è un supplemento. Imballiamo noi ogni pezzo, a mano.</p>
          <p>La consegna è al piano strada: il corriere lascia il pezzo all’ingresso dell’edificio e non lo porta su per le scale. Quando il pezzo parte ti mandiamo il codice per seguire la spedizione.</p>
          <p>Abiti a Trieste? Puoi anche ritirarlo gratis in laboratorio, su appuntamento. <a href="{legali['Spedizioni e consegna']}">Tutti i dettagli</a></p>
        </details>
        <details><summary>Pagamento</summary>
          <p>Carta di credito o debito, Apple Pay e Google Pay tramite Stripe: i dati della carta vanno direttamente a Stripe e non passano da noi.</p>
          <p>Oppure bonifico: il pezzo resta riservato per te 7 giorni e parte quando il bonifico è arrivato. Il prezzo è finale, senza IVA da aggiungere.</p>
        </details>
        <details><summary>Resi e garanzia</summary>
          <p>Hai 14 giorni dalla consegna per recedere, senza dover spiegare il motivo. Ti rimborsiamo il prezzo e le spese di consegna, sullo stesso metodo di pagamento; la spedizione di ritorno è a carico tuo.</p>
          <p>Garanzia legale di {e(p['garanzia'] or '12 mesi')}. <a href="{legali['Resi e rimborsi']}">Resi e rimborsi</a></p>
        </details>
        <details><summary>Un pezzo restaurato e dipinto a mano</summary>
          <p>Piccole irregolarità nella pittura, segni del tempo nel legno e lievi differenze di colore rispetto allo schermo fanno parte del carattere di un pezzo restaurato e dipinto a mano. Hai un dubbio? Chiedici altre foto o un video.</p>
        </details>
      </div>
      {condividi}
    </div>
  </div>
</div>
{simili_html}
{barra}
<dialog class="visore" aria-label="Foto a schermo intero">
  <img src="" alt="">
  <button class="chiudi" type="button" aria-label="Chiudi">✕</button>
  <button class="prec" type="button" aria-label="Foto precedente">‹</button>
  <button class="succ" type="button" aria-label="Foto successiva">›</button>
</dialog>"""

    prodotto = {
        "@context": "https://schema.org", "@type": "Product", "name": p["nome"],
        "description": riassunto(descr or p["nome"], 500), "sku": p["slug"], "url": url,
        "image": [f"{BASE}/foto/{f['file']}-1200.webp" for f in foto],
        "brand": {"@type": "Brand", "name": "DART"}, "category": cat["nome"],
    }
    if p["prezzo"]:
        condizione = "RefurbishedCondition" if cat["condizione"] == "refurbished" else "NewCondition"
        offerta = {
            "@type": "Offer", "url": url, "priceCurrency": "EUR", "price": f"{p['prezzo']:.2f}",
            "availability": "https://schema.org/InStock" if p["disponibile"] else "https://schema.org/SoldOut",
            "itemCondition": "https://schema.org/" + condizione,
            "seller": {"@id": BASE + "/#negozio"},
            "shippingDetails": {"@type": "OfferShippingDetails",
                                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "IT"}},
            "hasMerchantReturnPolicy": {
                "@type": "MerchantReturnPolicy", "applicableCountry": "IT",
                "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail",
                "returnFees": "https://schema.org/ReturnShippingFees"},
        }
        if costo is not None:
            offerta["shippingDetails"]["shippingRate"] = {"@type": "MonetaryAmount", "value": f"{costo:.2f}",
                                                          "currency": "EUR"}
        prodotto["offers"] = offerta
    briciole = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": cat["nome"], "item": f"{BASE}/{cat['percorso']}"},
        {"@type": "ListItem", "position": 3, "name": p["nome"], "item": url},
    ]}

    parti = [riassunto(prima_frase(descr), 100) if descr else p["sottotitolo"], p["misure"]]
    if p["disponibile"] and p["prezzo"]:
        parti.append(euro(p["prezzo"]))
    # la coda più lunga che sta nei 160 caratteri che Google mostra
    code = (["Pezzo unico, spedizione in tutta Italia", "Spedizione in tutta Italia", "Pezzo unico"]
            if p["disponibile"] else ["Venduto"])
    descrizione = next((" · ".join(x for x in parti + [c] if x) for c in code
                        if len(" · ".join(x for x in parti + [c] if x)) <= 160),
                       riassunto(" · ".join(x for x in parti if x), 158))
    titolo = f"{p['nome']} — {cat['descrittore'][0].upper()}{cat['descrittore'][1:]} | DART"

    og_extra = ""
    if p["disponibile"]:
        nota = " · ".join(x for x in [p["misure"], "Spedizione in tutta Italia"] if x)
        og = og_social(p["slug"], foto[0]["file"], cat["social"], p["nome"], prezzo, nota, p["nome"])
        if p["prezzo"]:
            og_extra = (f'<meta property="product:price:amount" content="{p["prezzo"]:.2f}">\n'
                        '<meta property="product:price:currency" content="EUR">\n'
                        '<meta property="product:availability" content="in stock">\n')
    else:
        og = og_social(p["slug"], foto[0]["file"], "Venduto", p["nome"], "",
                       "Scopri i pezzi disponibili su darthome.it", p["nome"])
    return pagina(percorso=percorso, titolo=titolo, descrizione=descrizione, corpo=corpo,
                  attivo=p["categoria"], og=og, og_tipo="product" if p["disponibile"] else "website",
                  og_extra=og_extra, dati_strutturati=[prodotto, briciole],
                  classe_body="ha-barra" if p["disponibile"] else "", wa_messaggio=msg)


def contatti():
    corpo = f"""<div class="contenitore sezione">{blocco_visita("../", "h1")}</div>
<section class="sezione sezione-alt"><div class="contenitore">{blocco_domande("../")}</div></section>
<section class="sezione"><div class="contenitore">
  <div class="sezione-testa"><div><p class="occhiello">Come funziona</p><h2>Spedizione, consegna e resi</h2></div></div>
  {blocco_info("../")}
  <p class="nota-ordine">Se ci scrivi per un ordine già fatto, mettici il numero dell’ordine: facciamo prima.</p>
</div></section>"""
    return pagina(percorso="contatti/index.html", titolo="Contatti — DART, mobili e quadri dipinti a mano",
                  descrizione=(f"Domande su un pezzo, una spedizione o un ordine? Scrivi a DART su WhatsApp "
                               f"al {NEGOZIO['telefono']} o a {NEGOZIO['email']}."),
                  corpo=corpo, attivo="contatti", dati_strutturati=[negozio_ld(), domande_ld()])


def pagina_404():
    corpo = """<div class="contenitore pagina">
  <h1>Questa pagina non c’è</h1>
  <p>Forse il pezzo che cercavi è stato venduto, o l’indirizzo è cambiato.</p>
  <p><a class="btn btn-scuro" href="/negozio/">Guarda i pezzi disponibili</a></p>
</div>"""
    pagina(percorso="404.html", titolo="Pagina non trovata — DART", descrizione="Pagina non trovata.",
           corpo=corpo, indicizza=False)


def feed_prodotti():
    """Catalogo per Google Merchant Center e Meta (Facebook e Instagram Shopping)."""
    voci = ""
    for p in DISPONIBILI:
        if not p["prezzo"] or not p["foto"]:
            continue
        cat = CATEGORIE[p["categoria"]]
        url = f"{BASE}/pezzo/{p['slug']}/"
        if immagini:
            principale = immagini.foto_jpeg(p["foto"][0]["file"])
        else:
            principale = f"foto/{p['foto'][0]['file']}-1200.webp"
        altre = "".join(f"<g:additional_image_link>{BASE}/foto/{f['file']}-1200.webp</g:additional_image_link>\n"
                        for f in p["foto"][1:10])
        descr = testo_semplice(p["descrizione"]) or p["nome"]
        if p["misure"]:
            descr += f" Misure: {p['misure']}."
        costo = numero(p["spedizione"])
        spedizione = (f"<g:shipping><g:country>IT</g:country><g:price>{costo:.2f} EUR</g:price></g:shipping>\n"
                      if costo is not None else "")
        voci += f"""<item>
<g:id>{p['slug']}</g:id>
<g:title>{e(p['nome'] + ' – ' + cat['descrittore'])}</g:title>
<g:description>{e(riassunto(descr, 4900))}</g:description>
<g:link>{url}</g:link>
<g:image_link>{BASE}/{principale}</g:image_link>
{altre}<g:availability>in_stock</g:availability>
<g:price>{p['prezzo']:.2f} EUR</g:price>
<g:condition>{cat['condizione']}</g:condition>
<g:brand>DART</g:brand>
<g:identifier_exists>no</g:identifier_exists>
<g:product_type>{e(cat['nome'])}</g:product_type>
{spedizione}</item>
"""
    (DOCS / "feed-prodotti.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n<channel>\n'
        f"<title>DART</title>\n<link>{BASE}/</link>\n<description>{e(NEGOZIO['descrizione'])}</description>\n"
        f"{voci}</channel>\n</rss>\n", encoding="utf-8")


def main():
    global OG_HOME
    if not immagini:
        print("Pillow non è installato: salto anteprime social e foto JPEG (pip install pillow).", file=sys.stderr)
    OG_HOME = og_social("home", "hero", "Trieste · dal laboratorio", "Mobili che raccontano qualcosa", "",
                        "Mobili d’epoca dipinti a mano e quadri originali. Pezzi unici, spedizione in tutta Italia.",
                        "Mobili d’epoca restaurati e dipinti a mano da DART")
    indirizzi = [home()]
    primo = DISPONIBILI[0]
    indirizzi.append(catalogo(
        "negozio/index.html", "Tutti i pezzi",
        "Mobili restaurati, quadri e sculture: tutto dipinto a mano a Trieste, tutto in un solo esemplare.",
        PEZZI, "negozio", "Tutti i pezzi — Mobili dipinti a mano, quadri e sculture | DART",
        ("Mobili d’epoca restaurati e dipinti a mano, quadri originali e sculture in legno. Pezzi unici "
         f"dal laboratorio DART di Trieste, spedizione in tutta Italia con {CORRIERI}."),
        og_social("negozio", primo["foto"][0]["file"], "Pezzi unici · dipinti a mano", "Tutti i pezzi disponibili",
                  "", f"{len(DISPONIBILI)} pezzi unici: mobili d’epoca, quadri e sculture. Spedizione in tutta Italia.")))
    for k, c in CATEGORIE.items():
        pezzi = [p for p in PEZZI if p["categoria"] == k]
        disp = [p for p in pezzi if p["disponibile"]]
        prezzi = [p["prezzo"] for p in disp if p["prezzo"]]
        da = f", da {euro(min(prezzi))}" if prezzi else ""
        dipinti = f"{c['nome']} dipint{'e' if k == 'sculture' else 'i'} a mano"
        copertina = (disp or pezzi)[0]["foto"][0]["file"]
        indirizzi.append(catalogo(
            c["percorso"] + "index.html", c["nome"], c["testo"], pezzi, k,
            f"{dipinti} — Pezzi unici | DART",
            c["testo"] + f" Acquisto online, spedizione in tutta Italia con {CORRIERI}.",
            og_social(f"categoria-{k}", copertina, "DART · Trieste", dipinti,
                      "", f"{len(disp)} pezzi unici disponibili{da}. Spedizione in tutta Italia.")))
    for p in PEZZI:
        indirizzi.append(scheda(p))
    indirizzi.append(contatti())
    pagina_404()
    feed_prodotti()

    oggi = date.today().isoformat()
    voci = "".join(f"<url><loc>{u}</loc><lastmod>{oggi}</lastmod></url>\n" for u in indirizzi)
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{voci}</urlset>\n', encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"Costruite {len(indirizzi) + 1} pagine in docs/, più sitemap.xml e feed-prodotti.xml.")


if __name__ == "__main__":
    main()
