# DART — nuovo sito

Nuova versione del sito di [darthome.it](https://www.darthome.it): mobili restaurati e quadri dipinti a mano, Trieste.

È un sito statico: niente database e niente plugin da aggiornare. Si apre in fretta anche da telefono.

## Com’è fatto

| Cartella | Cosa contiene |
|---|---|
| `docs/` | Il sito pronto da pubblicare: pagine, foto, caratteri, `stile.css`, `sito.js`, `feed-prodotti.xml` |
| `data/pezzi.json` | Tutti i pezzi: nome, prezzo, misure, foto, data di messa in vendita, disponibile o venduto |
| `data/descrizioni.json` | Le descrizioni dei pezzi riscritte per il nuovo sito (hanno la precedenza su quelle importate) |
| `data/domande.json` | Le domande frequenti (home e pagina contatti) |
| `data/recensioni.json` | Le recensioni dei clienti: finché è vuoto, la sezione non compare |
| `data/negozio.json` | Indirizzo, orari, telefono, WhatsApp, social, link alle pagine legali |
| `data/ritocchi.json` | I ritocchi alle foto: quali togliere, schiarire, ritagliare, e i quadri da raddrizzare |
| `strumenti/importa.py` | Copia pezzi e foto dal vecchio sito WordPress |
| `strumenti/costruisci.py` | Genera le pagine HTML in `docs/` partendo da `data/` |
| `strumenti/immagini.py` | Converte le foto in WebP a 400, 800 e 1200 px, crea le anteprime per WhatsApp e i social e le foto JPEG per i cataloghi |
| `strumenti/ritocca.py` | Applica i ritocchi di `data/ritocchi.json` partendo dalle foto originali |

## Modificare i contenuti

1. Modifica `data/pezzi.json`. Per segnare un pezzo come venduto, metti `"disponibile": false`.
   Le descrizioni si cambiano in `data/descrizioni.json`.
2. Rigenera le pagine:

   ```
   pip install pillow          # una volta sola
   python3 strumenti/costruisci.py
   ```

   Senza Pillow le pagine si generano lo stesso, ma senza le anteprime per i social.
3. Per vedere il sito sul computer:

   ```
   cd docs && python3 -m http.server 8000
   ```

   poi apri http://localhost:8000.

Per riallineare pezzi e foto al vecchio sito: `python3 strumenti/importa.py`, poi `ritocca.py` e `costruisci.py` (vedi «Foto»). Le foto già presenti non vengono riscaricate, a meno che sul negozio non siano cambiate; con `--tutte-le-foto` vengono riconvertite tutte.

L’etichetta **Nuovo** compare da sola nei 30 giorni dopo la messa in vendita di un pezzo (campo `pubblicato`) e poi sparisce, anche senza rigenerare il sito.

## Foto

Alcune foto sono state ritoccate partendo dagli originali ad alta risoluzione: i quadri sono stati raddrizzati e ritagliati sulla sola tela, le foto scure schiarite, una foto sbagliata tolta. I ritocchi sono leggeri e non cambiano il pezzo. Sono tutti elencati, con il motivo, in `data/ritocchi.json`.

Per rifarli, ad esempio dopo aver rilanciato `importa.py`:

```
pip install pillow numpy     # una volta sola
python3 strumenti/ritocca.py
python3 strumenti/costruisci.py
```

Gli originali vengono scaricati una volta sola in `.originali/`, che non viene pubblicata. Ogni foto è salvata in tre larghezze (400, 800 e 1200 px): il browser scarica la più piccola che basta per lo schermo. Le regole di ritocco indicano la foto con il suo percorso su WordPress (`origine`), così restano giuste anche se sul negozio le foto vengono tolte o riordinate.

Sul sito i quadri orizzontali, o molto stretti, si vedono sempre interi, su uno sfondo neutro. Nelle schede di mobili e quadri c'è un disegno in scala con una persona alta 1,70 m, ricavato dalle misure: se le misure sono sbagliate, si vede subito.

## Recensioni

Quando hai recensioni vere di clienti, ad esempio copiate da Google o da messaggi ricevuti con il loro permesso, aggiungile in `data/recensioni.json` e rigenera il sito:

```json
[
  {"nome": "Nome del cliente", "citta": "Città", "testo": "Il testo della recensione, parola per parola.", "pezzo": "armadio-con-pesce"}
]
```

`pezzo` è facoltativo: è l’indirizzo del pezzo (la parte dopo `/pezzo/`).

## Acquisti

Il pulsante **Acquista ora** porta al carrello del sito WordPress attuale, così pagamenti con Stripe, conferme d’ordine e modulo di recesso continuano a funzionare. L’indirizzo si cambia in `data/negozio.json` (`acquisto_online`). Se lo lasci vuoto, al posto di «Acquista ora» compare «Chiedi su WhatsApp».

Spedizione con BRT o Poste Italiane, consegna al piano strada. I testi da aggiornare anche su WordPress sono in `DA-AGGIORNARE-SU-WORDPRESS.md`.

## Google Shopping e Instagram Shopping

`docs/feed-prodotti.xml` è il catalogo dei pezzi disponibili, nel formato che leggono Google e Meta. Si aggiorna ogni volta che rigeneri il sito. Quando il sito è online su darthome.it:

- **Google**: in [Merchant Center](https://merchants.google.com) aggiungi il feed `https://www.darthome.it/feed-prodotti.xml`. I pezzi possono comparire gratis nella scheda Shopping di Google.
- **Instagram e Facebook**: in Commerce Manager crea un catalogo con lo stesso indirizzo come origine dati. Poi puoi taggare i pezzi nei post di Instagram.

## Pubblicare un’anteprima

Su GitHub vai in **Settings → Pages**, scegli il ramo e la cartella `/docs`.
