// Dati e funzioni comuni alle prove: che cosa deve esserci sul sito, letto dagli stessi file
// da cui lo genera strumenti/costruisci.py.
const fs = require('fs');
const path = require('path');
const { expect } = require('@playwright/test');

const RADICE = path.resolve(__dirname, '..');
const DOCS = path.join(RADICE, 'docs');
const pezzi = JSON.parse(fs.readFileSync(path.join(RADICE, 'data', 'pezzi.json'), 'utf8'));
const negozio = JSON.parse(fs.readFileSync(path.join(RADICE, 'data', 'negozio.json'), 'utf8'));

const disponibili = pezzi.filter(p => p.disponibile && p.prezzo);
const venduti = pezzi.filter(p => !p.disponibile);
const conPiuFoto = disponibili.filter(p => p.foto.length >= 3);
const acquisto = id => negozio.acquisto_online.replace('{id}', id);

/** Tutte le pagine del sito (gli indirizzi come li apre un visitatore), 404 esclusa. */
function tutteLePagine() {
  const pagine = [];
  (function giro(cartella) {
    for (const nome of fs.readdirSync(cartella)) {
      const p = path.join(cartella, nome);
      if (fs.statSync(p).isDirectory()) giro(p);
      else if (nome === 'index.html') pagine.push(path.relative(DOCS, cartella).split(path.sep).join('/') + '/');
    }
  })(DOCS);
  return pagine.map(p => (p === '/' ? '' : p)).sort();
}

/** Raccoglie errori di JavaScript, messaggi d'errore in console e risorse del sito che non arrivano. */
function sorveglia(page) {
  const errori = [];
  page.on('pageerror', e => errori.push(`errore JS: ${e.message}`));
  page.on('console', m => {
    // WebKit rifiuta il prefetch delle pagine successive se il sito non è in HTTPS: succede solo
    // con il server di prova (http://127.0.0.1); online il sito è in HTTPS
    if (m.type() === 'error' && !/^Prefetch request denied: URL must be secure/.test(m.text())) errori.push(`console: ${m.text()}`);
  });
  page.on('requestfailed', r => {
    // un'immagine rimandata può essere interrotta da una navigazione: non è un guasto del sito
    if (!/ERR_ABORTED|NS_BINDING_ABORTED|cancelled/i.test(r.failure()?.errorText || '')) errori.push(`richiesta fallita: ${r.url()} ${r.failure()?.errorText}`);
  });
  page.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('/non-esiste/')) errori.push(`${r.status()} ${r.url()}`); });
  return errori;
}

/** Niente scorrimento orizzontale e niente elementi fuori dallo schermo (tranne le righe che scorrono apposta). */
async function nienteFuoriSchermo(page, dove) {
  const r = await page.evaluate(() => {
    const w = document.documentElement.clientWidth;
    const fuori = [...document.querySelectorAll('body *')].filter(el => {
      // .salta: il link «Vai al contenuto» resta fuori schermo finché non riceve il focus;
      // galleria, miniature e categorie sono righe che scorrono di lato apposta
      if (el.closest('.galleria-nastro, .miniature, .filtri, .salta, [hidden], dialog:not([open])')) return false;
      const b = el.getBoundingClientRect();
      return b.width > 0 && b.height > 0 && (b.right > w + 1 || b.left < -1);
    }).slice(0, 3).map(el => `${el.tagName.toLowerCase()}.${el.className}`);
    return { scorre: document.documentElement.scrollWidth > w + 1, fuori };
  });
  expect(r.scorre, `${dove}: la pagina scorre di lato`).toBe(false);
  expect(r.fuori, `${dove}: elementi fuori dallo schermo`).toEqual([]);
}

/** Scorre fino in fondo, e la galleria fino all'ultima foto, così le foto con loading="lazy"
    partono; poi controlla che nessuna sia rotta. */
async function fotoTutteArrivate(page) {
  await page.evaluate(async () => {
    const pausa = () => new Promise(r => setTimeout(r, 40));
    for (const riga of document.querySelectorAll('.galleria-nastro, .miniature')) {
      for (let x = 0; x <= riga.scrollWidth; x += riga.clientWidth / 2) { riga.scrollLeft = x; await pausa(); }
    }
    for (let y = 0; y < document.body.scrollHeight; y += window.innerHeight / 2) {
      window.scrollTo(0, y);
      await pausa();
    }
  });
  const foto = stato => page.$$eval('img', (ims, stato) => ims
    .filter(i => i.getAttribute('src') && !i.closest('noscript, dialog') && i.offsetParent !== null)
    .filter(i => (stato === 'in arrivo' ? !i.complete : i.complete && i.naturalWidth === 0))
    .map(i => i.currentSrc || i.src), stato);
  await expect.poll(() => foto('in arrivo'), { message: 'foto ancora in arrivo', timeout: 20000 }).toEqual([]);
  expect(await foto('rotte'), 'foto che non arrivano').toEqual([]);
}

module.exports = { pezzi, negozio, disponibili, venduti, conPiuFoto, acquisto, tutteLePagine, sorveglia, nienteFuoriSchermo, fotoTutteArrivate };
