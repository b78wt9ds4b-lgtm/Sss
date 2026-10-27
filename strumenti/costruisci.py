"""Costruisce le pagine HTML del sito in docs/ a partire da data/*.json.

    python3 strumenti/costruisci.py

Solo libreria standard. Foto, caratteri, stile.css e sito.js stanno già
in docs/ e non vengono toccati: qui si generano soltanto le pagine,
sitemap.xml e robots.txt.
"""
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

RADICE = Path(__file__).resolve().parent.parent
DOCS = RADICE / "docs"
NEGOZIO = json.loads((RADICE / "data" / "negozio.json").read_text(encoding="utf-8"))
PEZZI = json.loads((RADICE / "data" / "pezzi.json").read_text(encoding="utf-8"))
BASE = NEGOZIO["url"].rstrip("/")

# chiave interna -> percorso (uguale al vecchio sito), nomi e testi
CATEGORIE = {
    "mobili": {
        "percorso": "categoria/mobili/", "nome": "Mobili", "singolare": "mobile",
        "testo": "Credenze, cassettiere, armadi, tavoli e sedute d’epoca: restaurati e dipinti a mano, uno alla volta.",
    },
    "quadri": {
        "percorso": "categoria/quadri-e-ritratti/", "nome": "Quadri", "singolare": "quadro",
        "testo": "Dipinti originali ad acrilico su tela e su legno, firmati. Ritratti e composizioni floreali.",
    },
    "sculture": {
        "percorso": "categoria/altro-arredamento/", "nome": "Sculture", "singolare": "scultura",
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
    intero = f"{valore:,.0f}".replace(",", ".")
    if valore != int(valore):
        intero = f"{valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{intero} €"


def testo_semplice(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def riassunto(s, n=155):
    s = testo_semplice(s)
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",.;:—") + "…"


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


def mail(oggetto, corpo=""):
    return f"mailto:{NEGOZIO['email']}?subject={quote(oggetto)}&body={quote(corpo)}"


ICONE = {
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".9" fill="currentColor"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.3-.4.8-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.8-1.2.2-.6.2-1.1.1-1.2l-.4-.2Z"/></svg>',
    "pennello": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M18.4 2.6a2 2 0 0 1 2.9 2.9L11 15.8 8.2 13Z"/><path d="M8.2 13c-2.3 0-4 1.8-4 4 0 1.6-1 2.6-2.2 3 4.8 1 9-.5 9-4.2Z"/></svg>',
    "unico": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12l3 5-9 13L3 8Z"/><path d="M3 8h18M12 21 8 8l4-5 4 5Z"/></svg>',
    "furgone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M2 6h12v10H2zM14 9h4l4 4v3h-8z"/><circle cx="6" cy="17.5" r="1.8" fill="#fff"/><circle cx="17.5" cy="17.5" r="1.8" fill="#fff"/></svg>',
    "carrello": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M6 7h12l-1 13H7Z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>',
}


# ---------------------------------------------------------------- impaginazione

def menu_voci(r):
    return [
        (f"{r}negozio/", "Tutti i pezzi", "negozio"),
        (f"{r}{CATEGORIE['mobili']['percorso']}", "Mobili", "mobili"),
        (f"{r}{CATEGORIE['quadri']['percorso']}", "Quadri", "quadri"),
        (f"{r}{CATEGORIE['sculture']['percorso']}", "Sculture", "sculture"),
        (f"{r}#laboratorio" if r == "" else f"{r}index.html#laboratorio", "Il laboratorio", "laboratorio"),
        (f"{r}contatti/", "Contatti", "contatti"),
    ]


def pagina(*, percorso, titolo, descrizione, corpo, attivo="", immagine_og=None,
           dati_strutturati=None, classe_body="", wa_messaggio=None, indicizza=True):
    """Avvolge il corpo nel documento completo e lo scrive in docs/<percorso>."""
    profondita = percorso.count("/")
    r = "../" * profondita
    canonico = BASE + "/" + (percorso[:-len("index.html")] if percorso.endswith("index.html") else percorso)
    og = immagine_og or "foto/hero-1200.webp"
    voci = menu_voci(r)
    menu = "".join(
        f'<li><a href="{u}"{" aria-current=\"page\"" if k == attivo else ""}>{t}</a></li>' for u, t, k in voci)
    ld = ""
    for d in dati_strutturati or []:
        ld += f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n'
    legali = "".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in NEGOZIO["pagine_legali"].items())
    wa_link = wa(wa_messaggio or "Ciao DART, vorrei qualche informazione.")
    robots = "" if indicizza else '<meta name="robots" content="noindex">\n'
    documento = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titolo)}</title>
<meta name="description" content="{e(descrizione)}">
{robots}<link rel="canonical" href="{canonico}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="DART">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="{e(titolo)}">
<meta property="og:description" content="{e(descrizione)}">
<meta property="og:url" content="{canonico}">
<meta property="og:image" content="{BASE}/{og}">
<meta name="twitter:card" content="summary_large_image">
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
    <a class="marchio" href="{r or './'}"><img src="{r}logo.png" alt="" width="32" height="32">DART</a>
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
        <a class="marchio" href="{r or './'}"><img src="{r}logo.png" alt="" width="32" height="32">DART</a>
        <p>Mobili restaurati e dipinti a mano, quadri originali. Laboratorio e negozio a Trieste.</p>
      </div>
      <div>
        <h2>Pezzi</h2>
        <ul>{"".join(f'<li><a href="{u}">{t}</a></li>' for u, t, _ in voci[:4])}</ul>
      </div>
      <div>
        <h2>Negozio</h2>
        <ul>
          <li><a href="{NEGOZIO['mappa']}">{e(NEGOZIO['indirizzo'])}, {e(NEGOZIO['citta'])}</a></li>
          <li><a href="tel:+39{NEGOZIO['telefono'].replace(' ', '')}">{e(NEGOZIO['telefono'])}</a></li>
          <li><a href="mailto:{NEGOZIO['email']}">{e(NEGOZIO['email'])}</a></li>
          <li><a href="{NEGOZIO['instagram']}">Instagram</a> · <a href="{NEGOZIO['facebook']}">Facebook</a></li>
        </ul>
      </div>
      <div>
        <h2>Acquisti</h2>
        <ul>{legali}</ul>
      </div>
    </div>
    <div class="piede-legale">
      <p>{e(NEGOZIO['titolare'])} · {e(NEGOZIO['indirizzo'])}, {NEGOZIO['cap']} {e(NEGOZIO['citta'])} ({NEGOZIO['provincia']}) · {e(NEGOZIO['orari_testo'])}</p>
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

def scheda_pezzo(r, p, sizes="(min-width: 1100px) 290px, (min-width: 760px) 31vw, 46vw"):
    foto = p["foto"]
    imgs = immagine(r, foto[0], p["nome"], sizes) if foto else ""
    if len(foto) > 1:
        imgs += immagine(r, foto[1], "", sizes)
    etichetta = ('<span class="etichetta">Pezzo unico</span>' if p["disponibile"]
                 else '<span class="etichetta etichetta-venduto">Venduto</span>')
    sotto = f'<p class="sotto">{e(p["sottotitolo"])}</p>' if p["sottotitolo"] else ""
    prezzo = f'<span class="prezzo">{euro(p["prezzo"])}</span>' if p["prezzo"] and p["disponibile"] else ""
    return f"""<article class="pezzo{'' if p['disponibile'] else ' venduto'}">
  <a href="{r}pezzo/{p['slug']}/">
    <div class="pezzo-foto">{imgs}{etichetta}</div>
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
    <p class="occhiello">Il negozio</p>
    <{titolo_tag}>Vieni a vederli <em>dal vivo</em></{titolo_tag}>
    <p>In negozio a Trieste trovi tutti i pezzi — e dal vivo, spesso, sono ancora più belli. Per il ritiro di un acquisto avvisaci prima: prepariamo il pezzo e l’imballo.</p>
    <dl>
      <div><dt>Indirizzo</dt><dd><a href="{NEGOZIO['mappa']}">{e(NEGOZIO['indirizzo'])}, {NEGOZIO['cap']} {e(NEGOZIO['citta'])}</a></dd></div>
      <div><dt>Orari</dt><dd>{e(NEGOZIO['orari_testo'])}</dd></div>
      <div><dt>Telefono e WhatsApp</dt><dd><a href="tel:+39{NEGOZIO['telefono'].replace(' ', '')}">{e(NEGOZIO['telefono'])}</a></dd></div>
      <div><dt>Email</dt><dd><a href="mailto:{NEGOZIO['email']}">{e(NEGOZIO['email'])}</a></dd></div>
    </dl>
    <div class="azioni">
      <a class="btn btn-scuro" href="{NEGOZIO['mappa']}">Indicazioni stradali</a>
      <a class="btn btn-whatsapp" href="{wa('Ciao DART, vorrei passare in negozio a vedere i pezzi.')}">{ICONE['whatsapp']}Scrivici</a>
    </div>
  </div>
  <a class="mappa" href="{NEGOZIO['mappa']}">
    {immagine(r, {"file": "negozio", "w": 1050, "h": 1400}, "Il negozio DART in via Luigi Cadorna a Trieste", "(min-width: 760px) 50vw, 100vw")}
    <span>Apri in Google Maps ↗</span>
  </a>
</div>"""


def blocco_info(r):
    righe = "".join(f"<li><span>{e(t)}</span><b>{e(v)}</b></li>" for t, v in SPEDIZIONI)
    legali = NEGOZIO["pagine_legali"]
    return f"""<div class="info">
  <div class="info-scheda">
    <h3>Spedizione</h3>
    <p>Tariffa fissa in base al pezzo, imballaggio fatto a mano da noi.</p>
    <ul>{righe}</ul>
  </div>
  <div class="info-scheda">
    <h3>Consegna e ritiro</h3>
    <p>Dopo l’ordine ti chiamiamo per concordare il giorno: di solito i mobili arrivano entro due settimane, quadri e tavolini entro dieci giorni lavorativi.</p>
    <p>Il ritiro in negozio a Trieste è gratuito, su appuntamento. Piano, ascensore, ZTL: diccelo e ci organizziamo.</p>
    <p><a href="{legali['Spedizioni e consegna']}">Tutti i dettagli sulla spedizione</a></p>
  </div>
  <div class="info-scheda">
    <h3>Resi e garanzia</h3>
    <p>Hai 14 giorni per cambiare idea, come previsto dal Codice del Consumo. Il rimborso avviene sullo stesso metodo di pagamento.</p>
    <p>Garanzia legale: 12 mesi sui mobili restaurati, 24 sui quadri nuovi.</p>
    <p><a href="{legali['Resi e rimborsi']}">Resi e rimborsi</a> · <a href="{legali['Recedere dal contratto qui']}">Recedere dal contratto</a></p>
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
    disponibili = [p for p in PEZZI if p["disponibile"]]
    copertine = {"mobili": "armadio-botanico-1", "quadri": "fiori-di-mezzanotte-1", "sculture": "pesce-doro-1"}
    categorie = ""
    for k, c in CATEGORIE.items():
        n = sum(1 for p in disponibili if p["categoria"] == k)
        foto = trova_foto(copertine[k])
        categorie += f"""<a class="categoria" href="{c['percorso']}">
  {immagine(r, foto, "", "(min-width: 640px) 33vw, 100vw")}
  <div><h3>{c['nome']}</h3><span>{n} {'pezzo disponibile' if n == 1 else 'pezzi disponibili'}</span></div>
</a>"""
    orari_json = e(json.dumps(NEGOZIO["orari"]))
    corpo = f"""<section class="apertura">
  <div class="contenitore">
    <div>
      <p class="occhiello">Trieste · dal laboratorio</p>
      <h1>Mobili che <em>raccontano</em> qualcosa</h1>
      <p class="lead">Pezzi d’epoca restaurati e dipinti a mano, uno per uno. E i quadri che li accompagnano. Ogni pezzo è unico: quando è venduto, è venduto.</p>
      <div class="azioni">
        <a class="btn btn-scuro" href="negozio/">Guarda i {len(disponibili)} pezzi disponibili</a>
        <a class="btn btn-chiaro" href="#visita">Vieni in negozio</a>
      </div>
      <p class="stato-negozio" data-orari="{orari_json}"><span class="punto"></span><span class="testo">{e(NEGOZIO['orari_testo'])}</span></p>
    </div>
    <figure>
      {immagine(r, {"file": "hero", "w": 1050, "h": 1400}, "Interno del negozio DART a Trieste: un mobile dipinto a mano con uccelli e i quadri alle pareti", "(min-width: 760px) 45vw, 100vw", lazy=False)}
      <figcaption>Via Luigi Cadorna 13, Trieste</figcaption>
    </figure>
  </div>
</section>
<section class="forza" aria-label="Perché DART">
  <ul>
    <li>{ICONE['unico']}<strong>Ogni pezzo è unico</strong><span>Niente repliche, niente produzione in serie.</span></li>
    <li>{ICONE['pennello']}<strong>Restauro e pittura a mano</strong><span>Tutto fatto in laboratorio, a Trieste.</span></li>
    <li>{ICONE['furgone']}<strong>Spedizione in tutta Italia</strong><span>Imballaggio curato, consegna concordata con te.</span></li>
  </ul>
</section>
<section class="sezione">
  <div class="contenitore">
    <div class="sezione-testa">
      <div><p class="occhiello">Disponibili ora</p><h2>Gli ultimi pezzi</h2></div>
      <a class="link-freccia" href="negozio/">Vedi tutti →</a>
    </div>
    {griglia(r, disponibili[:8], "griglia griglia-4")}
  </div>
</section>
<section class="sezione sezione-alt">
  <div class="contenitore">
    <div class="sezione-testa"><div><p class="occhiello">Sfoglia</p><h2>Cosa cerchi?</h2></div></div>
    <div class="categorie">{categorie}</div>
  </div>
</section>
<section class="sezione" id="laboratorio">
  <div class="contenitore storia">
    <figure>{immagine(r, trova_foto("armadio-botanico-3"), "Dettaglio di un mobile dipinto a mano da DART", "(min-width: 760px) 40vw, 100vw")}</figure>
    <div>
      <p class="occhiello">Il laboratorio</p>
      <h2>Un laboratorio, <em>prima</em> che un negozio</h2>
      <p>DART nasce dal recupero: mobili d’epoca che vengono smontati, puliti, restaurati e poi dipinti a mano, uno alla volta. Nessun pezzo è uguale a un altro, e nessuno viene rifatto.</p>
      <ol class="passi">
        <li><strong>Il recupero</strong><span>Scegliamo mobili d’epoca con una buona struttura e una storia da raccontare.</span></li>
        <li><strong>Il restauro</strong><span>Smontaggio, pulizia, consolidamento del legno: il mobile torna solido e funzionale.</span></li>
        <li><strong>La pittura</strong><span>Fiori, uccelli, foglie: il decoro è dipinto a mano e segue la forma del mobile.</span></li>
      </ol>
    </div>
  </div>
</section>
<section class="sezione sezione-alt">
  <div class="contenitore">
    <div class="sezione-testa"><div><p class="occhiello">Come funziona</p><h2>Dall’ordine a casa tua</h2></div></div>
    {blocco_info(r)}
  </div>
</section>
<section class="sezione" id="visita">
  <div class="contenitore">{blocco_visita(r)}</div>
</section>"""
    return pagina(percorso="index.html", titolo="DART — Mobili restaurati e quadri dipinti a mano · Trieste",
                  descrizione=NEGOZIO["descrizione"], corpo=corpo, dati_strutturati=[negozio_ld()])


def catalogo(percorso, titolo_h1, testo, pezzi, attivo, titolo, descrizione):
    r = "../" * percorso.count("/")
    chips = [(f"{r}negozio/", "Tutti", "negozio", sum(p["disponibile"] for p in PEZZI))]
    for k, c in CATEGORIE.items():
        chips.append((f"{r}{c['percorso']}", c["nome"], k, sum(p["disponibile"] for p in PEZZI if p["categoria"] == k)))
    chip_html = "".join(
        f'<a class="chip" href="{u}"{" aria-current=\"page\"" if k == attivo else ""}>{t} <small>{n}</small></a>'
        for u, t, k, n in chips)
    disponibili = [p for p in pezzi if p["disponibile"]]
    venduti = [p for p in pezzi if not p["disponibile"]]
    corpo_disp = griglia(r, disponibili) if disponibili else (
        f'<p class="vuoto">In questo momento non ci sono pezzi disponibili qui. '
        f'<a href="{wa("Ciao DART, quando arrivano nuovi pezzi?")}">Scrivici</a> e ti avvisiamo quando ne arrivano di nuovi.</p>')
    corpo_venduti = ""
    if venduti:
        corpo_venduti = f"""<section class="venduti" hidden>
  <h2>Già venduti</h2>
  <p>Restano qui come portfolio. Se ti piace qualcosa di simile, scrivici: spesso abbiamo pezzi in lavorazione.</p>
  {griglia(r, venduti)}
</section>"""
        chip_html += '<button class="chip" type="button" data-solo-disponibili aria-pressed="false">Mostra anche i venduti</button>'
    corpo = f"""<div class="contenitore catalogo-testa">
  <h1>{titolo_h1}</h1>
  <p>{e(testo)}</p>
</div>
<nav class="filtri" aria-label="Categorie"><div class="contenitore">{chip_html}</div></nav>
<div class="contenitore" style="padding-top:28px;padding-bottom:80px">
  {corpo_disp}
  {corpo_venduti}
</div>"""
    elenco = {"@context": "https://schema.org", "@type": "CollectionPage", "name": titolo,
              "url": BASE + "/" + percorso.replace("index.html", ""),
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/pezzo/{p['slug']}/"}
                  for i, p in enumerate(disponibili)]}}
    og = f"foto/{disponibili[0]['foto'][0]['file']}-1200.webp" if disponibili and disponibili[0]["foto"] else None
    return pagina(percorso=percorso, titolo=titolo, descrizione=descrizione, corpo=corpo,
                  attivo=attivo, immagine_og=og, dati_strutturati=[elenco])


def scheda(p):
    percorso = f"pezzo/{p['slug']}/index.html"
    r = "../../"
    cat = CATEGORIE.get(p["categoria"], CATEGORIE["mobili"])
    url = f"{BASE}/pezzo/{p['slug']}/"
    foto = p["foto"]

    nastro = "".join(
        f'<button type="button" data-grande="{foto_url(r, f["file"], 1200)}" aria-label="Ingrandisci foto {i + 1}">'
        f'{immagine(r, f, p["nome"] + (f" — foto {i + 1}" if i else ""), "(min-width: 900px) 55vw, 100vw", lazy=i > 0)}</button>'
        for i, f in enumerate(foto))
    miniature = ""
    if len(foto) > 1:
        miniature = '<div class="miniature">' + "".join(
            f'<button type="button" aria-label="Foto {i + 1}" aria-current="{str(i == 0).lower()}">'
            f'<img src="{foto_url(r, f["file"], 600)}" alt="" loading="lazy" width="64" height="80"></button>'
            for i, f in enumerate(foto)) + f'</div><p class="galleria-conta" aria-live="polite">1 di {len(foto)}</p>'

    if p["disponibile"]:
        msg = f"Ciao DART, mi interessa «{p['nome']}» ({url}). È ancora disponibile?"
        azioni = ""
        if p["prezzo"] and NEGOZIO.get("acquisto_online"):
            azioni += (f'<a class="btn btn-scuro btn-pieno" href="{NEGOZIO["acquisto_online"].format(id=p["id"])}">'
                       f'{ICONE["carrello"]}Acquista online</a>')
        azioni += f'<a class="btn btn-whatsapp btn-pieno" href="{wa(msg)}">{ICONE["whatsapp"]}Chiedi su WhatsApp</a>'
        azioni += f'<a class="btn btn-chiaro btn-pieno" href="{wa("Ciao DART, vorrei passare in negozio a vedere «" + p["nome"] + "».")}">Vieni a vederlo in negozio</a>'
        nota = "Pagamento sicuro con carta, Apple Pay, Google Pay o bonifico. Ti contattiamo dopo l’ordine per concordare la consegna."
        etichetta = '<span class="etichetta">Pezzo unico</span>'
        prezzo = euro(p["prezzo"]) if p["prezzo"] else "Prezzo su richiesta"
    else:
        msg = f"Ciao DART, ho visto «{p['nome']}» sul sito, ma è venduto. Avete qualcosa di simile?"
        azioni = f'<a class="btn btn-whatsapp btn-pieno" href="{wa(msg)}">{ICONE["whatsapp"]}Cerchi qualcosa di simile? Scrivici</a>'
        nota = "Questo pezzo è già stato venduto. Ne abbiamo spesso altri in lavorazione: chiedici pure."
        etichetta = '<span class="etichetta etichetta-venduto">Venduto</span>'
        prezzo = ""

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
        spec.append(("Ritiro in negozio", "Gratuito, a Trieste"))
    if p["garanzia"]:
        spec.append(("Garanzia", p["garanzia"]))
    spec_html = "".join(f"<li><span>{e(k)}</span><span>{e(v)}</span></li>" for k, v in spec)

    legali = NEGOZIO["pagine_legali"]
    simili = [q for q in PEZZI if q["categoria"] == p["categoria"] and q["slug"] != p["slug"] and q["disponibile"]][:4]
    simili_html = ""
    if simili:
        simili_html = f"""<section class="sezione sezione-alt">
  <div class="contenitore">
    <div class="sezione-testa"><h2>Potrebbe piacerti anche</h2><a class="link-freccia" href="{r}{cat['percorso']}">Tutti i {cat['nome'].lower()} →</a></div>
    {griglia(r, simili, "griglia griglia-4")}
  </div>
</section>"""

    barra = ""
    if p["disponibile"]:
        barra = f"""<div class="barra-acquisto" aria-hidden="true">
  <div><strong>{e(p['nome'])}</strong><span>{e(prezzo)}</span></div>
  <a class="btn btn-whatsapp" href="{wa(msg)}" tabindex="-1">{ICONE['whatsapp']}Chiedi</a>
</div>"""

    descr = p["descrizione"] or (f"<p>{e(p['sottotitolo'])}</p>" if p["sottotitolo"] else "")
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
      {f'<p class="sotto">{e(p["sottotitolo"])}</p>' if p['sottotitolo'] else ''}
      <div class="scheda-prezzo">{f'<span class="prezzo">{e(prezzo)}</span>' if prezzo else ''}{etichetta}</div>
      <div class="scheda-azioni">{azioni}</div>
      <p class="nota-acquisto">{nota}</p>
      <div class="descrizione">{descr}</div>
      <ul class="specifiche">{spec_html}</ul>
      <div class="fisarmonica">
        <details><summary>Spedizione e consegna</summary>
          <p>Spedizione in tutta Italia con corriere, a tariffa fissa in base al pezzo; per Sicilia e Sardegna c’è un supplemento. Dopo l’ordine ti contattiamo per concordare il giorno di consegna.</p>
          <p>In alternativa puoi ritirare gratuitamente in negozio a Trieste, su appuntamento. <a href="{legali['Spedizioni e consegna']}">Tutti i dettagli</a></p>
        </details>
        <details><summary>Resi e garanzia</summary>
          <p>Hai 14 giorni dalla consegna per esercitare il diritto di recesso, come previsto dal Codice del Consumo. Il rimborso avviene sullo stesso metodo di pagamento.</p>
          <p>Garanzia legale di {e(p['garanzia'] or '12 mesi')}. <a href="{legali['Resi e rimborsi']}">Resi e rimborsi</a></p>
        </details>
        <details><summary>Un pezzo restaurato e dipinto a mano</summary>
          <p>Piccole irregolarità nella pittura, segni del tempo nel legno e lievi differenze di colore rispetto allo schermo fanno parte del carattere di un pezzo restaurato e dipinto a mano.</p>
        </details>
      </div>
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

    condizione = ("https://schema.org/RefurbishedCondition" if p["categoria"] == "mobili"
                  else "https://schema.org/NewCondition")
    prodotto = {
        "@context": "https://schema.org", "@type": "Product", "name": p["nome"],
        "description": riassunto(descr or p["nome"], 500), "sku": p["slug"], "url": url,
        "image": [f"{BASE}/foto/{f['file']}-1200.webp" for f in foto],
        "brand": {"@type": "Brand", "name": "DART"}, "category": cat["nome"],
    }
    if p["prezzo"]:
        prodotto["offers"] = {
            "@type": "Offer", "url": url, "priceCurrency": "EUR", "price": f"{p['prezzo']:.2f}",
            "availability": "https://schema.org/InStock" if p["disponibile"] else "https://schema.org/SoldOut",
            "itemCondition": condizione, "seller": {"@id": BASE + "/#negozio"},
            "shippingDetails": {"@type": "OfferShippingDetails",
                                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "IT"}},
        }
    briciole = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": cat["nome"], "item": f"{BASE}/{cat['percorso']}"},
        {"@type": "ListItem", "position": 3, "name": p["nome"], "item": url},
    ]}

    prima_frase = re.split(r"(?<=[.!?])\s", testo_semplice(descr))[0] if descr else ""
    parti = [p["sottotitolo"] or riassunto(prima_frase, 100), p["misure"]]
    if p["disponibile"] and p["prezzo"]:
        parti.append(euro(p["prezzo"]))
    parti.append("Pezzo unico dipinto a mano a Trieste" if p["disponibile"] else "Venduto")
    descrizione = riassunto(" · ".join(x for x in parti if x), 158)
    titolo = f"{p['nome']} — {cat['singolare'].capitalize()} dipinto a mano | DART Trieste"
    if p["categoria"] == "sculture":
        titolo = f"{p['nome']} — Scultura in legno dipinto | DART Trieste"
    return pagina(percorso=percorso, titolo=titolo, descrizione=descrizione, corpo=corpo,
                  attivo=p["categoria"], immagine_og=f"foto/{foto[0]['file']}-1200.webp" if foto else None,
                  dati_strutturati=[prodotto, briciole], classe_body="ha-barra" if p["disponibile"] else "",
                  wa_messaggio=msg)


def contatti():
    corpo = f"""<div class="contenitore sezione">{blocco_visita("../", "h1")}</div>
<section class="sezione sezione-alt"><div class="contenitore">
  <div class="sezione-testa"><div><p class="occhiello">Domande frequenti</p><h2>Prima di acquistare</h2></div></div>
  {blocco_info("../")}
  <p style="margin-top:28px">Se ci scrivi per un ordine già fatto, mettici il numero dell’ordine: facciamo prima.</p>
</div></section>"""
    return pagina(percorso="contatti/index.html", titolo="Contatti e orari — DART, Via Luigi Cadorna 13, Trieste",
                  descrizione=f"Il negozio DART è in {NEGOZIO['indirizzo']}, Trieste. {NEGOZIO['orari_testo']}. Telefono e WhatsApp {NEGOZIO['telefono']}.",
                  corpo=corpo, attivo="contatti", dati_strutturati=[negozio_ld()])


def pagina_404():
    corpo = """<div class="contenitore pagina">
  <h1>Questa pagina non c’è</h1>
  <p>Forse il pezzo che cercavi è stato venduto, o l’indirizzo è cambiato.</p>
  <p><a class="btn btn-scuro" href="/negozio/">Guarda i pezzi disponibili</a></p>
</div>"""
    pagina(percorso="404.html", titolo="Pagina non trovata — DART", descrizione="Pagina non trovata.",
           corpo=corpo, indicizza=False)


def main():
    indirizzi = [home()]
    indirizzi.append(catalogo(
        "negozio/index.html", "Tutti i pezzi",
        "Mobili restaurati, quadri e sculture: tutto dipinto a mano a Trieste, tutto in un solo esemplare.",
        PEZZI, "negozio", "Tutti i pezzi — Mobili dipinti, quadri e sculture | DART Trieste",
        "Mobili d’epoca restaurati e dipinti a mano, quadri originali e sculture in legno. Pezzi unici dal laboratorio DART di Trieste, spedizione in tutta Italia."))
    for k, c in CATEGORIE.items():
        pezzi = [p for p in PEZZI if p["categoria"] == k]
        indirizzi.append(catalogo(
            c["percorso"] + "index.html", c["nome"], c["testo"], pezzi, k,
            f"{c['nome']} dipint{'e' if k == 'sculture' else 'i'} a mano — Pezzi unici | DART Trieste",
            c["testo"] + " Spedizione in tutta Italia o ritiro in negozio a Trieste."))
    for p in PEZZI:
        indirizzi.append(scheda(p))
    indirizzi.append(contatti())
    pagina_404()

    oggi = date.today().isoformat()
    voci = "".join(f"<url><loc>{u}</loc><lastmod>{oggi}</lastmod></url>\n" for u in indirizzi)
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{voci}</urlset>\n', encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"Costruite {len(indirizzi) + 1} pagine in docs/.")


if __name__ == "__main__":
    main()
