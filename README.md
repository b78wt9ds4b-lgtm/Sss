# DART — nuovo sito

Nuova versione del sito di [darthome.it](https://www.darthome.it): mobili restaurati e quadri dipinti a mano, Trieste.

È un sito statico: niente database e niente plugin da aggiornare. Si apre in fretta anche da telefono.

## Com’è fatto

| Cartella | Cosa contiene |
|---|---|
| `docs/` | Il sito pronto da pubblicare: pagine, foto in WebP, caratteri, `stile.css`, `sito.js` |
| `data/pezzi.json` | Tutti i pezzi: nome, prezzo, misure, foto, disponibile o venduto |
| `data/descrizioni.json` | Le descrizioni dei pezzi riscritte per il nuovo sito (hanno la precedenza su quelle importate) |
| `data/negozio.json` | Indirizzo, orari, telefono, WhatsApp, social, link alle pagine legali |
| `strumenti/importa.py` | Copia pezzi e foto dal vecchio sito WordPress |
| `strumenti/costruisci.py` | Genera le pagine HTML in `docs/` partendo da `data/` |

## Modificare i contenuti

1. Modifica `data/pezzi.json`. Per segnare un pezzo come venduto, metti `"disponibile": false`.
   Le descrizioni si cambiano in `data/descrizioni.json`.
2. Rigenera le pagine:

   ```
   python3 strumenti/costruisci.py
   ```

3. Per vedere il sito sul computer:

   ```
   cd docs && python3 -m http.server 8000
   ```

   poi apri http://localhost:8000.

Per riallineare pezzi e foto al vecchio sito: `pip install pillow` e poi `python3 strumenti/importa.py`.

## Acquisti

Il pulsante **Acquista ora** porta al carrello del sito WordPress attuale, così pagamenti con Stripe, conferme d’ordine e modulo di recesso continuano a funzionare. L’indirizzo si cambia in `data/negozio.json` (`acquisto_online`). Se lo lasci vuoto, al posto di «Acquista ora» compare «Chiedi su WhatsApp».

Spedizione con BRT o Poste Italiane, consegna al piano strada. I testi da aggiornare anche su WordPress sono in `DA-AGGIORNARE-SU-WORDPRESS.md`.

## Pubblicare un’anteprima

Su GitHub vai in **Settings → Pages**, scegli il ramo e la cartella `/docs`.
