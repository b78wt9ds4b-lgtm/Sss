# Aggiornare darthome.it (WordPress)

In questa cartella c’è tutto quello che serve per portare sul sito WordPress di adesso le migliorie del nuovo sito, senza rifare il tema.
Ci vogliono circa un’ora. Prezzi, ordini e pagamenti non cambiano.

| File | Cosa fa | Dove va |
|---|---|---|
| `1-css-aggiuntivo.css` | L’aspetto delle parti nuove, testi grigi più leggibili | Aspetto → Personalizza → CSS aggiuntivo |
| `2-snippet-wpcode.php` | Le parti nuove (elenco qui sotto) | Plugin WPCode |
| `3-descrizioni-woocommerce.csv` | Le 38 descrizioni riscritte | Prodotti → Importa |
| `foto/` | 14 foto ritoccate e l’elenco di cosa sostituire (`foto/ELENCO.md`) | Media |

Cosa cambia con lo snippet:

- **Scheda del pezzo**: il pulsante diventa «Acquista ora» e porta dritto al pagamento. Sotto compaiono «Chiedi altre foto o un video» su WhatsApp, le garanzie (pagamento sicuro, reso entro 14 giorni, garanzia, spedizione con BRT o Poste Italiane al piano strada), il disegno in scala accanto a una persona alta 1,70 m (mobili e quadri) e il link per condividerlo.
- **WhatsApp**: un pulsante tondo in basso a destra, in tutte le pagine tranne carrello e pagamento. Nelle schede il messaggio contiene già il nome del pezzo.
- **Spedizione**: i testi dicono BRT o Poste Italiane e consegna al piano strada, non più «ti contattiamo per concordare il giorno» e «segnala piano, ascensore o ZTL».
- **Home**: al posto di «In negozio a Trieste trovi tutti i pezzi dal vivo» c’è l’invito a chiedere foto o video su WhatsApp e a comprare online.
- **Google e WhatsApp**: ogni pagina ha la sua descrizione per Google; quando qualcuno condivide un link si vede l’anteprima con foto, nome e prezzo. Google riceve i dati dei pezzi (prezzo, disponibilità, reso) e del negozio (indirizzo, orari).
- **Pagamento**: il campo «Note sull’ordine» suggerisce di scrivere un telefono e il nome sul citofono, che servono al corriere.
- **Domande frequenti**: si possono mettere in una pagina scrivendo `[dart_domande]`.
- **Prodotti correlati**: in fondo alle schede compaiono solo pezzi ancora in vendita, non più quelli venduti.
- **Tastiera**: le foto della scheda si raggiungono con il tasto Tab e si scorrono con le frecce.

## Prima di cominciare

1. Fai un **backup completo** del sito, dal pannello dell’hosting o con il plugin UpdraftPlus. Se l’hosting offre un sito di prova (staging), conviene fare tutto prima lì.
2. Controlla nello snippet il numero WhatsApp (riga `DART_WHATSAPP`, ora `393662936810`, cioè 366 293 6810). Il pulsante promette «altre foto o un video»: se non vuoi mandare video, nello snippet cambia `Chiedi altre foto o un video` in `Chiedi altre foto`.
3. Per copiare un file da GitHub: aprilo e premi il pulsante **Copy raw file** (i due quadratini sopra il testo, a destra). Per scaricare una foto: aprila e premi **Download raw file**.

## 1. Il CSS (2 minuti)

**Aspetto → Personalizza → CSS aggiuntivo.** Vai in fondo a quello che c’è già, incolla tutto `1-css-aggiuntivo.css` e premi **Pubblica**.

## 2. Lo snippet (5 minuti)

1. **Plugin → Aggiungi nuovo plugin**, cerca «WPCode», installa e attiva «WPCode – Insert Headers and Footers + Custom Code Snippets».
2. Nel menu a sinistra: **Code Snippets → + Add Snippet → Add Your Custom Code (New Snippet)**.
3. Titolo: «DART migliorie». **Code Type: PHP Snippet**.
4. Incolla tutto `2-snippet-wpcode.php` nel riquadro del codice.
5. Sotto, in **Insertion**: **Auto Insert**, Location **Run Everywhere**.
6. In alto a destra metti l’interruttore su **Active** e premi **Save Snippet**.

Se nel codice ci fosse un errore, WPCode non attiva lo snippet e lo segnala: il sito non si rompe.

## 3. Controlla (10 minuti)

Se il sito usa una cache (un plugin di cache o quella dell’hosting), svuotala. Poi, da una finestra in incognito:

- [ ] Nella scheda di un pezzo disponibile il pulsante dice «Acquista ora»; sotto ci sono WhatsApp, le garanzie e il disegno in scala.
- [ ] Nella scheda, «Spedizione e consegna» parla di BRT o Poste Italiane e di consegna al piano strada.
- [ ] Premendo «Acquista ora» si apre subito la pagina Pagamento con il pezzo. Non serve completare l’ordine: torna indietro e svuota il carrello.
- [ ] In basso a destra c’è il pulsante WhatsApp tondo; toccandolo si apre WhatsApp con il nome del pezzo.
- [ ] Nella home, «Consegna e ritiro» parla di BRT o Poste Italiane.
- [ ] Manda a te stesso su WhatsApp il link di un pezzo: l’anteprima mostra foto, nome e prezzo. WhatsApp ricorda le anteprime già viste: se vedi quella vecchia, prova con un altro pezzo.
- [ ] In fondo alla scheda di un pezzo, tra i «Prodotti correlati», non ci sono pezzi venduti.
- [ ] Incolla il link di un pezzo in [search.google.com/test/rich-results](https://search.google.com/test/rich-results): deve riconoscere il prodotto, senza errori in rosso.

## 4. Le descrizioni (10 minuti)

1. Prima salva quelle di adesso: **Prodotti → Tutti i prodotti → Esporta → Genera CSV**. Tieni il file: serve per tornare indietro.
2. **Prodotti → Tutti i prodotti → Importa.**
3. Scegli `3-descrizioni-woocommerce.csv` e spunta **Aggiorna i prodotti esistenti**. Continua.
4. Nella schermata delle colonne: «ID» → **ID**, «Description» → **Descrizione**, «Pezzo (solo promemoria, non importare)» → **Non importare**. Esegui l’importazione.
5. Apri due o tre pezzi e rileggi il testo.

Cambia solo la descrizione: prezzi, foto, misure e disponibilità restano come sono. Se nel frattempo un pezzo è stato cancellato, viene saltato.

## 5. Le foto (20 minuti)

In `foto/ELENCO.md` c’è l’elenco: 9 foto da sostituire (più luminose, raddrizzate, senza muro intorno) e 5 quadri con una foto nuova, dritta, da mettere come immagine principale.

**Foto da sostituire.** Il modo più veloce è il plugin gratuito «Enable Media Replace»:

1. **Plugin → Aggiungi nuovo plugin**, cerca «Enable Media Replace», installa e attiva.
2. **Media → Libreria**, cerca il nome scritto nella colonna «Foto sul negozio» (per esempio `IMG_6505`) e apri la foto.
3. Premi **Sostituisci media**, scegli il file nuovo, lascia **Sostituisci solo il file** e carica.

La foto cambia in tutte le pagine e resta nella stessa posizione.

**Foto nuove** (le righe «Caricarla come immagine principale»):

1. **Prodotti**, apri il pezzo.
2. Nel riquadro **Immagine prodotto** premi «Rimuovi immagine prodotto», poi «Imposta immagine prodotto» e carica il file nuovo.
3. Nel riquadro **Galleria prodotto** aggiungi la foto che prima era la principale e trascinala al primo posto, così non si perde.
4. Premi **Aggiorna**.

## 6. I testi delle pagine (15 minuti)

Le pagine «Spedizioni e consegna» e «Condizioni generali di vendita» (punto 6) vanno riscritte a mano. I testi pronti sono in [`DA-AGGIORNARE-SU-WORDPRESS.md`](../DA-AGGIORNARE-SU-WORDPRESS.md), nella cartella principale, insieme a cosa controllare nel carrello e nelle email.

## 7. Domande frequenti (facoltativo, 3 minuti)

**Pagine → Aggiungi pagina**, titolo «Domande frequenti». Aggiungi un blocco **Shortcode**, scrivi `[dart_domande]` e pubblica. Poi aggiungi la pagina al menu o al piè di pagina (**Aspetto → Menu**).

## Misure da controllare

Il disegno in scala usa le misure del pannello (Altezza, Larghezza, Lunghezza = profondità). Queste sembrano sbagliate rispetto alle foto:

- **Azzurro e Oro**: è scritto H 70 · L 100, ma il quadro è verticale. Forse H 100 · L 70.
- **Bouquet Mediterraneo**: H 40 · L 50, ma nella foto il quadro è più largo in proporzione.
- **Fiori di mezzanotte**: profondità 18 cm. Forse 1,8.

## Se qualcosa non va

- **Tutto lo snippet**: WPCode → Code Snippets → interruttore su Inactive. Il sito torna subito com’era.
- **Una parte sola**: nello snippet cambia `true` in `false` sulla riga di quella parte (per esempio `DART_WHATSAPP_FLOTTANTE` per il pulsante tondo) e premi Update.
- **Il CSS**: cancella il pezzo incollato e premi Pubblica.
- **Le descrizioni**: reimporta il file esportato al punto 4, sempre con «Aggiorna i prodotti esistenti».
- **Le foto**: si recuperano dal backup.

## Per i ragazzi

- Lo snippet è autonomo: non tocca il tema e non crea tabelle. Va bene anche in fondo al `functions.php` di dart-child (senza `<?php`, che c’è già).
- Ganci: `wp_head` (meta description, Open Graph, JSON-LD), `woocommerce_structured_data_product` (svuotato, per non avere due blocchi Product), `woocommerce_after_add_to_cart_form` priorità 20 (la scheda, dopo i pulsanti Stripe: compare solo per i pezzi disponibili), `woocommerce_product_single_add_to_cart_text`, `woocommerce_add_to_cart_redirect` (al pagamento, anche dai link `?add-to-cart=` del sito nuovo; non con le aggiunte AJAX), `wp_footer` (WhatsApp tondo), `template_redirect` con `ob_start` (testi), `woocommerce_checkout_fields` (note dell’ordine: vale per il pagamento classico, quello di adesso), `woocommerce_related_products` (tiene solo i pezzi disponibili e acquistabili), `wp_footer` priorità 30 (solo nelle schede: `tabindex`, `role` e `aria-label` su `#galleria`; la soluzione giusta è metterli nel template di dart-child e spegnere `DART_GALLERIA_TASTIERA`), shortcode `[dart_domande]`.
- `DART_TESTI_SPEDIZIONE` è una toppa: sostituisce frasi esatte dell’HTML con un output buffer. La soluzione giusta è cambiarle nei template di dart-child (home: «Consegna e ritiro» e «Il negozio»; scheda: «Spedizione e consegna»; il testo delle categorie vuote) e poi mettere la costante a `false`. Le frasi sono tutte in `dart_sostituisci()`.
- La parte SEO si spegne da sola se c’è Yoast, Rank Math, All in One SEO o SEOPress. Nell’Offer manca `shippingDetails`: la tariffa per pezzo la calcola il tema («Spedizione in Italia», «Sicilia e Sardegna»); se la rendete disponibile, si può aggiungere.
- Misure: altezza → H, larghezza → L, lunghezza → P. Garanzia: 24 mesi per `quadri-e-ritratti`, 12 per il resto, come nelle specifiche del tema.
- Il CSS usa le variabili del tema (`--linea`, `--salvia`, `--crema`…). `--tenue` passa da #8C8175 a #6E6358: il testo grigio su `--sabbia` era a 3,4:1 e ora è a 5,2:1 (le linee guida WCAG chiedono 4,5:1). Il pulsante tondo ha `z-index: 70`, sopra la pagina e sotto `.velo` e `.pannello`.
- Le foto in `foto/` si rigenerano con `python3 strumenti/ritocca.py --per-wordpress` (regole in `data/ritocchi.json`).
