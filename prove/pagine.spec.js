// Ogni pagina del sito, aperta direttamente dal suo indirizzo: risponde 200, ha un solo titolo h1,
// nessun errore di JavaScript o di rete, e tutte le foto arrivano (anche quelle in fondo alla pagina).
const { test, expect } = require('@playwright/test');
const { tutteLePagine, sorveglia, fotoTutteArrivate } = require('./aiuti');

for (const url of tutteLePagine()) {
  test(`/${url}`, async ({ page }, info) => {
    test.skip(!info.project.name.endsWith('-telefono'), 'una larghezza per motore basta: le altre sono in dimensioni.spec.js');
    const errori = sorveglia(page);
    const r = await page.goto(url);
    expect(r.status()).toBe(200);
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page).toHaveTitle(/DART/);
    await fotoTutteArrivate(page);
    expect(errori).toEqual([]);
  });
}

test('sitemap.xml, robots.txt e catalogo prodotti: rispondono e indicano le pagine giuste', async ({ request }, info) => {
  test.skip(info.project.name !== 'chromium-telefono', 'file statici: basta un browser');
  const sitemap = await (await request.get('sitemap.xml')).text();
  const indirizzi = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
  expect(indirizzi.length).toBe(tutteLePagine().length);
  const robots = await (await request.get('robots.txt')).text();
  expect(robots).toMatch(/Sitemap: https?:\/\/\S+\/sitemap\.xml/);
  const feed = await request.get('feed-prodotti.xml');
  expect(feed.status()).toBe(200);
  expect(await feed.text()).toContain('<g:availability>in_stock</g:availability>');
});
