// I percorsi di chi visita il sito: dal menu al pezzo e al link d'acquisto, venduti, galleria,
// ingrandimento, barra d'acquisto, 404, contatti. Ogni prova controlla il risultato, non solo il clic.
const { test, expect } = require('@playwright/test');
const { pezzi, negozio, disponibili, venduti, conPiuFoto, acquisto, sorveglia } = require('./aiuti');

function euro(v) {
  const [intero, dec] = (Number.isInteger(v) ? v.toFixed(0) : v.toFixed(2)).split('.');
  return intero.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (dec ? ',' + dec : '') + ' €';
}
const largo = info => info.project.use.viewport.width >= 900; // da 900 px il menu è in alto, senza pulsante

test('dalla home al negozio, a una categoria e alla scheda, fino al link d’acquisto; indietro e aggiorna', async ({ page }, info) => {
  const errori = sorveglia(page);
  await page.goto('');
  await expect(page.locator('h1')).toBeVisible();

  if (largo(info)) {
    await page.locator('.menu a', { hasText: 'Tutti i pezzi' }).click();
  } else {
    const apri = page.locator('.apri-menu');
    await apri.click();
    await expect(page.locator('#menu-mobile')).toBeVisible();
    await expect(apri).toHaveAttribute('aria-expanded', 'true');
    await page.locator('#menu-mobile a', { hasText: 'Tutti i pezzi' }).click();
  }
  await expect(page).toHaveURL(/\/negozio\/$/);
  await expect(page.locator('.catalogo-corpo > .griglia article')).toHaveCount(disponibili.length);

  await page.locator('.filtri a.chip', { hasText: 'Mobili' }).click();
  await expect(page).toHaveURL(/\/categoria\/mobili\/$/);
  await expect(page.locator('.filtri a.chip[aria-current="page"]')).toContainText('Mobili');
  await expect(page.locator('.catalogo-corpo > .griglia article')).toHaveCount(disponibili.filter(p => p.categoria === 'mobili').length);

  const primo = page.locator('.catalogo-corpo > .griglia article a').first();
  const slug = (await primo.getAttribute('href')).split('/').filter(Boolean).pop();
  const p = pezzi.find(x => x.slug === slug);
  await primo.click();
  await expect(page).toHaveURL(new RegExp(`/pezzo/${slug}/$`));
  await expect(page.locator('h1')).toHaveText(p.nome);
  await expect(page.locator('.scheda-prezzo .prezzo')).toHaveText(euro(p.prezzo));
  await expect(page.locator('.scheda-azioni a', { hasText: 'Acquista ora' })).toHaveAttribute('href', acquisto(p.id));

  await page.goBack();
  await expect(page).toHaveURL(/\/categoria\/mobili\/$/);
  await expect(page.locator('.catalogo-corpo > .griglia article')).not.toHaveCount(0);
  await page.goForward();
  await page.reload();
  await expect(page.locator('h1')).toHaveText(p.nome);
  expect(errori).toEqual([]);
});

test('menu del telefono: si apre, si chiude e porta a ogni sezione', async ({ page }, info) => {
  test.skip(largo(info), 'sul computer il menu è sempre visibile');
  await page.goto('');
  const apri = page.locator('.apri-menu');
  const voci = await page.locator('#menu-mobile a').evaluateAll(as => as.map(a => a.getAttribute('href')));
  expect(voci.length).toBeGreaterThanOrEqual(5);
  await apri.click();
  await apri.click();
  await expect(page.locator('#menu-mobile')).toBeHidden();
  await expect(apri).toHaveAttribute('aria-expanded', 'false');
  for (const href of voci.filter(h => !h.includes('#'))) {
    const r = await page.request.get(new URL(href, page.url()).href);
    expect(r.status(), href).toBe(200);
  }
});

test('catalogo: «Mostra anche i venduti» apre e chiude i venduti; l’indirizzo #venduti li apre già', async ({ page }) => {
  await page.goto('negozio/');
  const bottone = page.locator('[data-solo-disponibili]');
  await expect(page.locator('.venduti')).toBeHidden();
  await bottone.click();
  await expect(bottone).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.venduti article')).toHaveCount(venduti.length);
  await expect(page.locator('.venduti')).toBeVisible();
  await bottone.click();
  await expect(page.locator('.venduti')).toBeHidden();
  await page.goto('');
  await page.goto('negozio/#venduti');
  await expect(page.locator('.venduti')).toBeVisible();
  await expect(page.locator('[data-solo-disponibili]')).toHaveAttribute('aria-pressed', 'true');
});

test('categoria vuota o piena: ogni categoria mostra i suoi pezzi disponibili, con il numero giusto', async ({ page }) => {
  const categorie = { mobili: 'categoria/mobili/', quadri: 'categoria/quadri-e-ritratti/', sculture: 'categoria/altro-arredamento/' };
  for (const [cat, url] of Object.entries(categorie)) {
    await page.goto(url);
    const attesi = disponibili.filter(p => p.categoria === cat).length;
    if (attesi) await expect(page.locator('.catalogo-corpo > .griglia article')).toHaveCount(attesi);
    else await expect(page.locator('.catalogo-corpo .vuoto')).toBeVisible();
    await expect(page.locator('.filtri a.chip[aria-current="page"] small')).toHaveText(String(attesi));
  }
});

test('scheda: la prima foto parte subito, le altre a pagina caricata; miniature, contatore e ingrandimento', async ({ page }) => {
  const p = conPiuFoto[0];
  const n = p.foto.length;
  await page.goto(`pezzo/${p.slug}/`);
  const prima = page.locator('.galleria-nastro img').first();
  await expect(prima).toHaveAttribute('fetchpriority', 'high');
  await expect(prima).not.toHaveAttribute('loading', 'lazy');
  // le foto dopo la prima partono solo dopo l'evento load (così non tolgono banda alla prima)
  const prima_di_load = await page.evaluate(() => {
    const load = performance.getEntriesByType('navigation')[0].loadEventStart;
    return performance.getEntriesByType('resource')
      .filter(r => /-(400|800|1200)\.webp$/.test(r.name) && r.startTime < load)
      .map(r => r.name.split('/').pop());
  });
  expect(prima_di_load.filter(f => f.startsWith(`${p.slug}-`) && !f.startsWith(`${p.slug}-1-`))).toEqual([]);
  await expect.poll(() => page.$$eval('.galleria-nastro img', ims => ims.filter(i => !i.getAttribute('src')).length)).toBe(0);

  await expect(page.locator('.miniature button')).toHaveCount(n);
  await expect(page.locator('.galleria-conta')).toHaveText(`1 di ${n}`);
  await page.locator('.miniature button').nth(2).click();
  await expect(page.locator('.galleria-conta')).toHaveText(`3 di ${n}`);
  await expect(page.locator('.miniature button').nth(2)).toHaveAttribute('aria-current', 'true');

  const visore = page.locator('.visore');
  await page.locator('.galleria-nastro button').nth(2).click();
  await expect(visore).toBeVisible();
  const img = visore.locator('img');
  await expect(img).toHaveAttribute('src', /-1200\.webp$/);
  await expect.poll(() => img.evaluate(i => i.complete && i.naturalWidth > 0)).toBe(true);
  const src = await img.getAttribute('src');
  await page.keyboard.press('ArrowRight');
  await expect(img).not.toHaveAttribute('src', src);
  await visore.locator('.prec').click();
  await expect(img).toHaveAttribute('src', src);
  await page.keyboard.press('Escape');
  await expect(visore).toBeHidden();
  await page.locator('.galleria-nastro button').first().click();
  await expect(visore).toBeVisible();
  await visore.locator('.chiudi').click();
  await expect(visore).toBeHidden();
});

test('scheda (telefono): la barra d’acquisto non copre la pagina all’apertura e compare dopo i pulsanti', async ({ page }, info) => {
  test.skip(largo(info), 'la barra d’acquisto c’è solo sotto i 900 px');
  const p = disponibili[0];
  await page.goto(`pezzo/${p.slug}/`);
  const barra = page.locator('.barra-acquisto');
  await page.waitForTimeout(300);
  await expect(barra).not.toHaveClass(/visibile/);
  await page.locator('.scheda-azioni').evaluate(el => window.scrollTo(0, el.getBoundingClientRect().bottom + window.scrollY + 80));
  await expect(barra).toHaveClass(/visibile/);
  await expect(barra.locator('a')).toHaveAttribute('href', acquisto(p.id));
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(barra).not.toHaveClass(/visibile/);
  // con un salto che non passa sopra i pulsanti (un link, il tasto Home): era un errore vero
  await page.locator('.scheda-azioni').evaluate(el => window.scrollTo({ top: el.getBoundingClientRect().bottom + window.scrollY + 80, behavior: 'instant' }));
  await expect(barra).toHaveClass(/visibile/);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await expect(barra).not.toHaveClass(/visibile/);
});

test('pezzo venduto: niente acquisto, avviso su WhatsApp e pezzi simili in vendita', async ({ page }) => {
  const p = venduti[0];
  await page.goto(`pezzo/${p.slug}/`);
  await expect(page.locator('h1')).toHaveText(p.nome);
  await expect(page.locator('.scheda-prezzo .etichetta-venduto')).toHaveText('Venduto');
  await expect(page.locator('a[href*="add-to-cart"]')).toHaveCount(0);
  const avviso = page.locator('.scheda-azioni a.btn-whatsapp');
  await expect(avviso).toHaveAttribute('href', new RegExp(`^https://wa\\.me/${negozio.whatsapp}\\?text=`));
  expect(decodeURIComponent((await avviso.getAttribute('href')).split('text=')[1])).toContain(p.nome);
  const simili = await page.locator('.griglia-4 article a').evaluateAll(as => as.map(a => a.getAttribute('href').split('/').filter(Boolean).pop()));
  expect(simili.length).toBeGreaterThan(0);
  for (const s of simili) expect(disponibili.map(x => x.slug), `${s} è in vendita`).toContain(s);
});

test('ogni pezzo in vendita ha il link d’acquisto giusto, ogni venduto nessuno', async ({ page }, info) => {
  test.skip(info.project.name !== 'chromium-telefono', 'controllo dei dati: basta un browser');
  for (const p of pezzi) {
    await page.goto(`pezzo/${p.slug}/`);
    const link = page.locator('.scheda-azioni a', { hasText: 'Acquista ora' });
    if (p.disponibile && p.prezzo) await expect(link, p.slug).toHaveAttribute('href', acquisto(p.id));
    else await expect(link, p.slug).toHaveCount(0);
  }
});

test('etichetta «Nuovo»: c’è nei 30 giorni dopo la messa in vendita, poi sparisce da sola', async ({ page }) => {
  const p = [...disponibili].sort((a, b) => b.pubblicato.localeCompare(a.pubblicato))[0];
  const dal = new Date(`${p.pubblicato}T12:00:00`);
  await page.clock.setFixedTime(new Date(dal.getTime() + 5 * 864e5));
  await page.goto(`pezzo/${p.slug}/`);
  await expect(page.locator('.scheda-prezzo .etichetta-nuovo')).toBeVisible();
  await page.clock.setFixedTime(new Date(dal.getTime() + 31 * 864e5));
  await page.reload();
  await expect(page.locator('.scheda-prezzo .etichetta-nuovo')).toBeHidden();
});

test('indirizzo inesistente: pagina 404 con stile e link al negozio funzionante, anche in profondità', async ({ page }) => {
  for (const url of ['non-esiste/', 'pezzo/pezzo-che-non-ce/']) {
    const r = await page.goto(url);
    expect(r.status()).toBe(404);
    await expect(page.locator('h1')).toHaveText('Questa pagina non c’è');
    expect(await page.evaluate(() => getComputedStyle(document.body).backgroundColor)).not.toBe('rgba(0, 0, 0, 0)');
    await page.locator('main a', { hasText: 'Guarda i pezzi disponibili' }).click();
    await expect(page).toHaveURL(/\/negozio\/$/);
    await expect(page.locator('.catalogo-corpo > .griglia article')).toHaveCount(disponibili.length);
  }
});

test('indirizzo senza barra finale: porta alla pagina giusta', async ({ page }) => {
  await page.goto('negozio');
  await expect(page).toHaveURL(/\/negozio\/$/);
  await page.goto(`pezzo/${disponibili[0].slug}`);
  await expect(page.locator('h1')).toHaveText(disponibili[0].nome);
});

test('contatti: WhatsApp, telefono, email, mappa e orari; domande frequenti che si aprono', async ({ page }) => {
  await page.goto('contatti/');
  await expect(page.locator('main a[href^="https://wa.me/' + negozio.whatsapp + '?text="]').first()).toBeVisible();
  await expect(page.locator(`main a[href="tel:+${negozio.whatsapp}"]`)).toBeVisible();
  await expect(page.locator(`main a[href="mailto:${negozio.email}"]`).first()).toBeVisible();
  await expect(page.locator('main a.mappa')).toHaveAttribute('href', negozio.mappa);
  await expect(page.locator('main')).toContainText(negozio.orari_testo);
  const domanda = page.locator('.fisarmonica details').first();
  await domanda.locator('summary').click();
  await expect(domanda).toHaveAttribute('open', '');
  await expect(domanda.locator('p')).toBeVisible();
});

test('piede di ogni pagina: tutte le informative legali e i dati dell’azienda', async ({ page }) => {
  for (const url of ['', `pezzo/${disponibili[0].slug}/`]) {
    await page.goto(url);
    for (const [titolo, href] of Object.entries(negozio.pagine_legali)) {
      await expect(page.locator(`footer a[href="${href}"]`).first(), titolo).toBeAttached();
    }
    await expect(page.locator('footer')).toContainText(negozio.piva);
  }
});

test('privacy: nessun cookie e nessuna richiesta a siti esterni durante la navigazione', async ({ page, context }) => {
  const esterne = [];
  page.on('request', r => { const u = r.url(); if (!u.startsWith('http://127.0.0.1') && !u.startsWith('data:')) esterne.push(u); });
  for (const url of ['', 'negozio/', `pezzo/${conPiuFoto[0].slug}/`, `pezzo/${venduti[0].slug}/`, 'contatti/']) {
    await page.goto(url);
    await page.waitForLoadState('networkidle');
  }
  expect(esterne).toEqual([]);
  expect(await context.cookies()).toEqual([]);
});

test.describe('senza JavaScript', () => {
  test.use({ javaScriptEnabled: false });
  test('la scheda mostra tutte le foto e il link d’acquisto; il catalogo e la home si leggono', async ({ page }) => {
    const p = conPiuFoto[0];
    await page.goto(`pezzo/${p.slug}/`);
    const visibili = await page.$$eval('.galleria-nastro img', ims => ims.filter(i => i.getAttribute('src') && i.getClientRects().length).length);
    expect(visibili).toBe(p.foto.length);
    await expect(page.locator('.scheda-azioni a', { hasText: 'Acquista ora' })).toHaveAttribute('href', acquisto(p.id));
    await page.goto('negozio/');
    await expect(page.locator('.catalogo-corpo > .griglia article')).toHaveCount(disponibili.length);
    await page.goto('');
    await expect(page.locator('h1')).toBeVisible();
  });
});
