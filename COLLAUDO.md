# Collaudo del nuovo sito — 30 ottobre 2026

Versione collaudata: ramo `claude/blissful-meitner-j3zu4f`, dal commit `c66943e` (prima delle
correzioni) a quello che contiene questo file. Nulla è stato pubblicato e darthome.it non è
stato modificato.

## Stato

**Non pronto per sostituire darthome.it; pronto per un'anteprima.** Il sito è corretto e
collaudato. Restano tre blocchi, che non sono difetti del codice:

1. **Dove pubblicarlo.** Se va su www.darthome.it, WordPress (carrello, pagamento, account, pagine
   legali) deve passare su un sottodominio, con il webhook di Stripe e il dominio di Apple Pay
   aggiornati. I passi sono in `PUBBLICAZIONE.md`, scenario A.
2. **Prezzi e venduti copiati.** Il sito li prende dal negozio con `strumenti/importa.py`. Il 30
   ottobre un prezzo è cambiato sul negozio durante il collaudo (Fiori di mezzanotte, da 180 a
   200 €). Prima della produzione serve un aggiornamento automatico, per esempio ogni ora con
   GitHub Actions, oppure una persona incaricata.
3. **Pagamento non provato.** Carrello e pagamento sono WooCommerce + Stripe in produzione: non è
   stato aggiunto nulla al carrello vero. È verificato che ogni «Acquista ora» porti
   all'`add-to-cart` con l'ID giusto, e che ogni prodotto sia in vendita sull'API Store del negozio.
   Per il collaudo completo serve una copia di prova di WordPress con Stripe in modalità test.

## Che cosa è stato verificato

| Controllo | Strumento | Esito |
|---|---|---|
| Collegamenti, risorse, title/description/h1, canonical, JSON-LD, prezzi e disponibilità per Google, galleria, indicizzazione | `strumenti/controlla.py` | 46 pagine, 0 problemi |
| Dati uguali al negozio | `controlla.py --negozio` (API Store di WooCommerce) | 0 differenze |
| Validità HTML e CSS | W3C Nu Html Checker 26.10.12 | 46 pagine e `stile.css`: 0 errori |
| Percorsi, funzioni, schermi, accessibilità | `prove/` con Playwright 1.63: Chromium, Firefox 155, WebKit 26.6, ognuno su telefono (390×844) e computer (1440×900) | 293 superate, 0 fallite (175 saltate apposta, per esempio la barra d'acquisto sul computer) |
| Larghezze | 320×568, 375×667, 390×844, 768×1024, 1024×768, 1440×900, 568×320, 667×375, 844×390, 1024×1366 su 7 pagine e 3 motori | niente scorrimento di lato, niente fuori schermo, pulsanti ≥ 24 px, zoom non bloccato |
| Accessibilità | axe-core 4.10.2 (WCAG 2.2 A e AA) su 7 pagine, anche con ingrandimento e menu aperti; tastiera | 0 violazioni |
| Link esterni | 76 indirizzi distinti (pagine legali, WhatsApp, mappa, social) | tutti 200; Instagram risponde 429 ai controlli automatici |
| Segreti | ricerca nei file e in tutta la storia git | nessuno |
| Dipendenze | `npm audit` (prove), `pip-audit` (requirements) | 0 per le prove; Pillow 12.3 aveva oltre 40 vulnerabilità → 13.0.0 |
| Installazione da zero | clone da GitHub, venv, `pip install -r requirements.txt`, build, controlli, prove | build identica (0 file cambiati), controlli e prove superati |
| Snippet WordPress | 72 prove in PHP con WordPress simulato, sostituzioni sull'HTML vero di oggi | tutte superate |

Non verificati: telefoni veri e Safari vero (WebKit su Linux è un'approssimazione), lettori di
schermo, pagamento ed email d'ordine, dati dei visitatori reali (arrivano dopo la pubblicazione).

## Errori trovati e corretti (riprodotti prima)

| Errore | Causa | Correzione |
|---|---|---|
| Foto principale tardiva in negozio, categorie e contatti | l'immagine visibile all'apertura aveva `loading="lazy"` | parte subito con `fetchpriority="high"`; con rete lenta da 2,26 a 0,60 s |
| Foto principale della scheda tardiva | le 6 foto successive della galleria e le miniature (variante da 400 px per riquadri da 64) partivano insieme alla prima | foto rimandate a dopo `load` o al primo tocco; miniature da 200 px |
| Preload dei caratteri | toglieva banda a CSS e foto principale | tolto dove la pagina si apre con una foto; resta in contatti e 404 (lì toglierlo non migliorava) |
| Barra d'acquisto (telefono): copriva le misure all'apertura | si mostrava ogni volta che i pulsanti non erano sullo schermo, anche se ancora sotto | compare solo dopo i pulsanti; con `rootMargin` funziona anche dopo un salto (link, tasto Home) |
| 112 errori W3C nelle gallerie, `<img src="">` nel visore | foto rimandate senza `src`/`srcset`, `sizes` senza `srcset` | `src` = miniatura, `data-sizes`; immagine del visore creata da `sito.js` |
| Telefono in orizzontale: foto alta più di due schermi | galleria in 4:5 a tutta larghezza | altezza dello schermo, foto intera |
| 404 con canonical verso una pagina inesistente | canonical anche sulle pagine `noindex` | canonical e `og:url` solo sulle pagine indicizzabili |
| Dati vecchi: 6 prezzi, un venduto in vendita, un pezzo nuovo mancante | copia del 28 ottobre | riallineati; `controlla.py --negozio` li segnala |
| Garanzia dei quadri a 12 mesi alla prossima importazione | il negozio ha spostato la garanzia nel testo «Resi e garanzia» | `importa.py` la legge da lì |
| Pacchetto WordPress: avrebbe rimesso le vecchie foto di «Bordeaux in fiore» | sul negozio le foto sono già state cambiate | elenco rigenerato; `ritocca.py --per-wordpress` toglie le foto superate |
| Build non riproducibile; pezzi rimescolati a ogni importazione | miniature basate sulle date dei file; l'API restituisce un ordine diverso a ogni richiesta | miniature invalidate quando cambia la foto; ordine fisso (data, poi ID) |
| Pillow 12.3 (solo strumenti, non il sito pubblicato) | vulnerabilità nell'apertura di immagini malformate | 13.0.0, provata: pagine identiche |

Aggiunti anche: `strumenti/servi.py` (il sito come lo serve l'hosting), `strumenti/anteprima.py`
(copia chiusa a Google, con controllo che il `noindex` non finisca nel sito vero), la chiave
`wordpress` in `data/negozio.json` (spostare il negozio su un sottodominio cambiando solo la
configurazione), `requirements.txt` con le versioni fissate, `PUBBLICAZIONE.md`.

## Prestazioni prima e dopo (telefono, laboratorio)

Stesso server locale per entrambe le versioni (HTTP/2, gzip). Lighthouse 12.2.1 simulato (150 ms,
1,6 Mbit/s, CPU 4×), mediana di 3; rete rallentata davvero in Chromium (stessi valori), mediana di 5.

| Pagina | Lighthouse | LCP simulato | LCP rete rallentata | Peso |
|---|---|---|---|---|
| Home | 99 → 98 | 2,25 → 2,18 s | 2,36 → 2,05 s | 797 → 799 KB |
| Negozio | 99 → 100 | 2,02 → 1,06 s | 2,45 → 0,60 s | 805 → 776 KB |
| Categoria mobili | 99 → 99 | 2,10 → 1,80 s | 2,25 → 0,60 s | 461 → 452 KB |
| Scheda (Armadio botanico) | 97 → 100 | 2,55 → 1,36 s | 3,27 → 1,86 s | 917 → 747 KB |
| Pezzo venduto (Credenza antica) | 94 → 98 | 3,15 → 2,25 s | 3,38 → 1,78 s | 974 → 812 KB |
| Contatti | 98 → 98 | 2,28 → 2,28 s | 1,84 → 1,83 s | 304 → 305 KB |

Computer: home e scheda restano a 100 (scheda: LCP da 0,52 a 0,44 s, da 856 a 685 KB). Nella
home la simulazione dà il primo testo più tardi (FCP da 1,05 a 1,65 s, sotto la soglia di 1,8 s),
con la rete rallentata davvero più presto (da 0,75 a 0,59 s): è un limite noto della simulazione
con i caratteri in `font-display: swap`. Nessun dato di utenti reali: il sito non è online.

## darthome.it (WordPress), solo con l'accesso pubblico

Telefono simulato, Lighthouse, mediana di 3, 30 ottobre 2026:

| Pagina | Punteggio | LCP | Peso | Richieste |
|---|---|---|---|---|
| Home | 94 | 2,88 s (risposta del server 0,8 s) | 1.247 KB | 28 |
| Scheda Armadio botanico | 80 | 3,56 s (FCP 2,78 s, TBT 135 ms) | 4.708 KB | 151 |

Cause verificate:

- **Pagamento rapido di Stripe nella scheda.** Circa 2,1 MB di script Stripe in 28 richieste,
  circa 1 MB di hCaptcha e una ventina di script di WordPress (React, wp-data) per l'elemento
  express checkout. Fanno anche 3 cookie di terze parti (Best Practices 79).
- **Cache e immagini.** 73 risorse senza `Cache-Control`. Logo PNG da 70 KB mostrato a 30–32 px,
  due volte per pagina. Foto solo in JPEG (circa 435 KB risparmiabili secondo Lighthouse).

Problemi trovati:

- **SEO:** manca la meta description.
- **Prodotti correlati:** propongono pezzi venduti (2 su 3 nella scheda dell'Armadio botanico).
- **Contenuti di prova pubblicati e nella sitemap:** «Ciao mondo!», «Senza categoria» e il
  prodotto «Cartolina» (ID 415, 1 €, esaurito).

Con il pacchetto `per-wordpress/` aggiunto solo nel browser (CSS e script della galleria), axe non
trova più problemi nella scheda: prima segnalava 12–14 elementi tra contrasto e galleria non
raggiungibile da tastiera. Nella home resta `aria-allowed-attr` sui 6 link delle categorie
(`aria-pressed` su `a.chip`), da correggere nel template.

## Che cosa serve per andare avanti

- **Dalla titolare:** scelta di dove pubblicare; via libera all'anteprima; chi aggiorna i prezzi.
- **Dai ragazzi o dall'hosting, sul sito WordPress di adesso:**
  - installare il pacchetto `per-wordpress/` (istruzioni nel suo README, su una copia di prova prima);
  - preparare una copia di prova di WordPress con Stripe in modalità test, per collaudare
    carrello, pagamento ed email;
  - nel tema: `aria-current` al posto di `aria-pressed` sui link delle categorie, logo leggero,
    `Cache-Control` per le immagini;
  - togliere i contenuti di prova;
  - decidere sui pulsanti di pagamento rapido nella scheda.
- **Dai ragazzi o dall'hosting, per il nuovo sito (scenario A di `PUBBLICAZIONE.md`):**
  WordPress su un sottodominio, Stripe, DNS e reindirizzamenti.

## Come ripetere i controlli

```
python3 -m pip install -r requirements.txt
python3 strumenti/costruisci.py && python3 strumenti/controlla.py --negozio
cd prove && npm ci && npx playwright install chromium firefox webkit && npx playwright test
```
