# Pubblicare il nuovo sito

Il sito è statico: la cartella `docs/` contiene tutte le pagine, le foto, il CSS e il JavaScript.
Va bene su qualsiasi hosting statico con HTTPS. Non ci sono database, variabili d'ambiente o
credenziali da configurare: tutto quello che cambia da un ambiente all'altro è in `data/negozio.json`.

Carrello, pagamento (WooCommerce + Stripe), conferme d'ordine, account e pagine legali restano
sul sito WordPress. Il nuovo sito ci porta con il link «Acquista ora».

## 1. Installare da zero

Serve Python 3 (provato con 3.13). Node.js serve solo per le prove nel browser.

```
git clone https://github.com/b78wt9ds4b-lgtm/Sss.git dart
cd dart
git checkout claude/blissful-meitner-j3zu4f      # finché il lavoro non è unito al ramo principale
python3 -m venv .venv && . .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 strumenti/costruisci.py                  # rigenera docs/ (deve risultare identica a quella salvata)
python3 strumenti/controlla.py                   # 0 problemi
python3 strumenti/servi.py                       # http://localhost:8000
```

## 2. Prima di ogni pubblicazione

```
python3 strumenti/controlla.py --negozio         # prezzi, venduti e pezzi nuovi uguali al negozio?
# se elenca differenze:
python3 strumenti/importa.py && python3 strumenti/ritocca.py && python3 strumenti/costruisci.py
python3 strumenti/controlla.py --negozio         # ora 0 problemi
cd prove && npm ci && npx playwright test        # prove nel browser (vedi prove/README.md)
```

Poi salva su GitHub (commit e push): l'hosting pubblica `docs/` così com'è.

**Prezzi e venduti vanno tenuti allineati.** Il nuovo sito copia prezzi e disponibilità dal
negozio: se su WordPress cambia un prezzo o si vende un pezzo, finché il sito non viene
rigenerato e ripubblicato mostra il dato vecchio, mentre il carrello mostra quello nuovo (il 30
ottobre, in un'ora e mezza, un prezzo è cambiato). Prima di pubblicare in produzione va deciso
chi lo fa e quando. La soluzione consigliata è un aggiornamento automatico, per esempio ogni ora
con GitHub Actions (importa, ritocca, costruisci, controlla, pubblica), da preparare insieme alla
scelta dell'hosting. In alternativa, a mano dopo ogni modifica sul negozio.

## 3. Copia di prova (anteprima)

Per far vedere il sito prima di pubblicarlo, senza che Google lo trovi:

```
python3 strumenti/anteprima.py                   # crea anteprima/ (non va su GitHub)
python3 strumenti/controlla.py --anteprima anteprima
```

In `anteprima/` ogni pagina ha `noindex`, `robots.txt` chiude tutto, `_headers` aggiunge
`X-Robots-Tag: noindex`, e mancano sitemap e catalogo prodotti. Si carica così com'è su:

- **Netlify Drop** (app.netlify.com/drop): trascini la cartella e ottieni un indirizzo;
- **Cloudflare Pages**, caricamento diretto.

Non usare GitHub Pages dalla cartella `/docs` per la prova: pubblicherebbe il sito vero,
indicizzabile, con gli indirizzi canonici di darthome.it. Nella copia di prova «Acquista ora»
porta al carrello vero: non completare acquisti.

`controlla.py` (senza opzioni) blocca il caso opposto: se in `docs/` finisce una pagina con
`noindex`, un `robots.txt` chiuso o un `_headers` della prova, segnala l'errore.

## 4. Dove pubblicarlo: la decisione da prendere

### Scenario A — il nuovo sito su www.darthome.it, WordPress su un sottodominio (consigliato)

Gli indirizzi del nuovo sito sono gli stessi di WordPress: `/`, `/negozio/`, `/contatti/`,
`/categoria/mobili/`, `/categoria/quadri-e-ritratti/`, `/categoria/altro-arredamento/` e
`/pezzo/<nome>/` per ogni pezzo (controllato sulla sitemap di WordPress del 30 ottobre 2026: tutti
i 39 pezzi ci sono; manca solo `/pezzo/cartolina/`, un prodotto di prova). I risultati su Google
e i link già condivisi continuano a funzionare.

Passi (li fanno i ragazzi del sito o l'hosting, su una copia di prova prima):

1. **Backup completo di WordPress** (file e database), scaricato e conservato.
2. WordPress su `negozio.darthome.it` (o un altro nome): sottodominio con HTTPS, «Indirizzo WordPress» e
   «Indirizzo sito» nuovi, sostituzione degli indirizzi nel database (`wp search-replace`).
3. **Stripe**: aggiornare l'indirizzo del webhook al sottodominio (senza, gli ordini non passano a
   «pagato») e registrare il nuovo dominio per Apple Pay. Provare un pagamento in modalità test.
4. In `data/negozio.json`:
   - `wordpress`: `https://negozio.darthome.it`
   - `acquisto_online`: `https://negozio.darthome.it/carrello/?add-to-cart={id}`
   - `pagine_legali`: gli stessi percorsi sul sottodominio
   - `url` resta `https://www.darthome.it`

   Poi rigenera, controlla e prova (punto 2).
5. Sull'hosting statico, i reindirizzamenti per gli indirizzi che solo WordPress sa servire (file
   `_redirects` per Netlify e Cloudflare Pages; GitHub Pages non li supporta):

   ```
   /carrello/*               https://negozio.darthome.it/carrello/:splat               301
   /pagamento/*              https://negozio.darthome.it/pagamento/:splat              301
   /il-mio-account/*         https://negozio.darthome.it/il-mio-account/:splat         301
   /spedizioni-e-consegna/   https://negozio.darthome.it/spedizioni-e-consegna/        301
   /resi-e-rimborsi/         https://negozio.darthome.it/resi-e-rimborsi/              301
   /recesso/                 https://negozio.darthome.it/recesso/                      301
   /termini-e-condizioni/    https://negozio.darthome.it/termini-e-condizioni/         301
   /privacy/                 https://negozio.darthome.it/privacy/                      301
   /cookie-policy/           https://negozio.darthome.it/cookie-policy/                301
   /wp-admin/*               https://negozio.darthome.it/wp-admin/:splat               301
   /wp-login.php             https://negozio.darthome.it/wp-login.php                  301
   /wp-json/*                https://negozio.darthome.it/wp-json/:splat                301
   ```

6. **DNS**: il giorno prima abbassa il TTL. `www` punta all'hosting statico; `darthome.it` senza www
   reindirizza a `https://www.darthome.it`. **Non toccare i record della posta** (MX, SPF, DKIM, DMARC):
   ne dipende `assistenza@darthome.it`. Annota i record di prima, per tornare indietro.
7. HTTPS obbligatorio sull'hosting; controlla il certificato su `www` e senza www.
8. **Privacy**: l'informativa (su WordPress) deve nominare il nuovo hosting tra i fornitori che
   trattano i dati di navigazione (indirizzo IP nei log).

### Scenario B — il nuovo sito su un altro indirizzo, WordPress resta su www.darthome.it

Va bene solo come prova (punto 3). Pubblicato e indicizzabile, farebbe concorrenza a darthome.it
con le stesse pagine. Se serve comunque: `url` in `data/negozio.json` con il nuovo indirizzo.

### Scenario C — restare su WordPress

Le migliorie si portano con la cartella `per-wordpress/` (istruzioni nel suo README).

## 5. Che cosa deve offrire l'hosting

HTTPS con dominio proprio, compressione (gzip o brotli), HTTP/2, pagina `404.html` per gli
indirizzi inesistenti, indirizzi con la barra finale, e per lo scenario A i reindirizzamenti
(`_redirects`). Netlify e Cloudflare Pages offrono tutto nel piano gratuito; GitHub Pages tutto
tranne i reindirizzamenti. Prima di attivare un piano a pagamento, chiedi.

Cache: le foto possono essere rifatte con lo stesso nome (dopo un ritocco), quindi niente cache
«immutable» lunga su `/foto/`, `stile.css` e `sito.js`; vanno bene le impostazioni predefinite
dell'hosting. Le anteprime per i social e le foto JPEG dei cataloghi hanno un'impronta nel nome.

## 6. Subito dopo la pubblicazione

- Dal telefono: home, negozio, una scheda, «Acquista ora» fino alla pagina di pagamento (senza pagare), contatti.
- `https://www.darthome.it/indirizzo-che-non-esiste/` mostra la pagina 404.
- Google Search Console: invia `https://www.darthome.it/sitemap.xml`; Merchant Center: `https://www.darthome.it/feed-prodotti.xml`.
- Nei giorni successivi: errori 404 nei dati dell'hosting e in Search Console.
- I dati reali di velocità (Chrome UX Report, in PageSpeed Insights) arrivano dopo circa 28 giorni di visite.

## 7. Backup e ripristino

- Ogni versione del sito è un commit su GitHub: per tornare indietro si ripubblica il commit precedente
  (Netlify e Cloudflare hanno un pulsante «rollback»; con GitHub Pages si annulla il commit).
- Versione di partenza di questo collaudo: commit `6bf7897`.
- WordPress: backup completo prima di ogni intervento; il ripristino lo fa l'hosting.
- DNS: i record annotati al punto 4.6 permettono di tornare al sito di prima in pochi minuti (dopo il TTL).

## 8. Dati personali e log

Il sito statico non raccoglie dati: niente moduli, niente cookie, niente statistiche né script di
terze parti (lo verificano le prove nel browser). Ordini, account e pagamenti restano su WordPress
e Stripe. L'hosting tiene i normali log di accesso.
