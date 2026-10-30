# Prove nel browser

Aprono il sito di `docs/` con Chromium, Firefox e WebKit (il motore di Safari), servito da
`strumenti/servi.py` come lo servirà l'hosting, e controllano che ogni funzione dia il risultato
giusto: non basta che un pulsante reagisca al clic. Sanno che cosa aspettarsi perché leggono
`data/pezzi.json` e `data/negozio.json`: rigenera il sito prima di lanciarle.

```
cd prove
npm ci                                            # una volta: Playwright e axe-core, versioni fissate
npx playwright install chromium firefox webkit    # una volta: i browser
npx playwright install-deps                       # solo su Linux, se mancano librerie di sistema
npx playwright test                               # tutto: 6 combinazioni di browser e schermo
npm run prove-chromium                            # più veloce: solo Chromium
```

Le combinazioni sono Chromium, Firefox e WebKit, ognuno con telefono (390×844) e computer
(1440×900). Sono browser emulati: non sostituiscono la prova su un iPhone o un Android veri.

## Che cosa deve funzionare e quale prova lo controlla

| Funzione | Comportamento atteso | Prova |
|---|---|---|
| Ogni pagina (45 + la 404) | Si apre dal suo indirizzo con codice 200, un solo titolo h1, nessun errore di JavaScript o di rete, tutte le foto arrivano (anche quelle in fondo e nella galleria) | `pagine.spec.js` |
| Menu | Sul telefono si apre e si chiude (`aria-expanded`), ogni voce porta a una pagina che esiste; da 900 px è sempre visibile | `percorsi`, `dimensioni` |
| Dalla home all'acquisto | Home → negozio (tutti i pezzi disponibili) → categoria (solo i suoi) → scheda (nome, prezzo, link al carrello con l'ID giusto); indietro, avanti e aggiorna funzionano | `percorsi` |
| Categorie | Ogni categoria mostra i suoi pezzi disponibili e il numero nel filtro è giusto; se non ce ne sono, un messaggio | `percorsi` |
| Venduti | «Mostra anche i venduti» li apre e li chiude; l'indirizzo `#venduti` li apre già | `percorsi` |
| Galleria | La prima foto parte subito, con priorità alta; le altre solo dopo il caricamento; miniature e contatore «3 di 7» | `percorsi` |
| Ingrandimento | Si apre toccando una foto, mostra la versione grande, frecce e pulsanti passano alle altre, Esc e ✕ chiudono, il focus torna alla galleria | `percorsi`, `accessibilita` |
| Barra d'acquisto (telefono) | Nascosta all'apertura; compare dopo i pulsanti, anche con un salto; sparisce tornando su | `percorsi` |
| Link d'acquisto | Ogni pezzo in vendita porta a `acquisto_online` con il suo ID; i venduti non ce l'hanno | `percorsi` |
| Pezzo venduto | Etichetta «Venduto», niente acquisto, avviso su WhatsApp con il nome del pezzo, pezzi simili tutti in vendita | `percorsi` |
| Etichetta «Nuovo» | Visibile nei 30 giorni dopo la messa in vendita, poi sparisce da sola (orologio simulato) | `percorsi` |
| Contatti | WhatsApp, telefono, email, mappa e orari; le domande frequenti si aprono | `percorsi` |
| Informative | In ogni pagina i link a spedizioni, resi, recesso, termini, privacy e cookie, e la partita IVA | `percorsi` |
| Pagina 404 | Codice 404 a qualsiasi indirizzo inesistente, anche in profondità, con stile e link al negozio funzionante | `percorsi` |
| Indirizzi senza barra | `/negozio` porta a `/negozio/` | `percorsi` |
| Privacy | Nessun cookie e nessuna richiesta a siti esterni mentre si naviga | `percorsi` |
| Senza JavaScript | La scheda mostra tutte le foto e il link d'acquisto; catalogo e home si leggono | `percorsi` |
| Schermi | 320, 375, 390, 768, 1024, 1440 px e telefono in orizzontale: niente scorrimento di lato, niente fuori schermo, menu giusto, pulsanti di almeno 24×24 px; zoom non bloccato | `dimensioni` |
| Accessibilità | Nessuna violazione WCAG 2.2 A/AA rilevata da axe in 7 pagine, con ingrandimento e menu aperti; tastiera: «Vai al contenuto» per primo, focus sempre visibile | `accessibilita` |
| Sitemap, robots, catalogo | Rispondono; la sitemap elenca tutte le pagine; il catalogo ha i pezzi in vendita | `pagine` |

Non sono qui, e restano da fare a mano: il pagamento (avviene su WordPress e Stripe, serve una
copia di prova di WordPress con Stripe in modalità test), i lettori di schermo veri, i dispositivi veri.
Le prove statiche (collegamenti, dati per Google, indicizzazione) sono in `strumenti/controlla.py`.
