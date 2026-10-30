// Le pagine principali a tutte le larghezze, in verticale e in orizzontale: niente scorrimento di
// lato, niente contenuti fuori schermo, menu giusto per la larghezza, pulsanti grandi abbastanza
// per il dito (almeno 24×24 px, WCAG 2.2) e zoom del telefono non bloccato.
const { test, expect } = require('@playwright/test');
const { conPiuFoto, venduti, nienteFuoriSchermo } = require('./aiuti');

const SCHERMI = [
  [320, 568], [375, 667], [390, 844], [768, 1024], [1024, 768], [1440, 900], // verticale e computer
  [568, 320], [667, 375], [844, 390], [1024, 1366],                          // telefono in orizzontale, tablet grande
];
const PAGINE = ['', 'negozio/', 'categoria/quadri-e-ritratti/', `pezzo/${conPiuFoto[0].slug}/`, `pezzo/${venduti[0].slug}/`, 'contatti/', 'non-esiste/'];

for (const url of PAGINE) {
  test(`/${url} a ${SCHERMI.length} dimensioni`, async ({ browser, browserName }, info) => {
    test.skip(!info.project.name.endsWith('-telefono'), 'le dimensioni le cambia la prova: basta un progetto per motore');
    test.setTimeout(240_000); // dieci aperture della pagina con fotografia dello schermo
    for (const [w, h] of SCHERMI) {
      const telefono = w < 900 && browserName !== 'firefox'; // Firefox non emula i telefoni
      const ctx = await browser.newContext({ baseURL: info.project.use.baseURL, viewport: { width: w, height: h }, ...(telefono ? { isMobile: true, hasTouch: true } : {}) });
      const page = await ctx.newPage();
      await page.goto(url);
      await page.waitForLoadState('load');
      const dove = `/${url} a ${w}×${h}`;
      await nienteFuoriSchermo(page, dove);

      if (w >= 900) {
        await expect(page.locator('.menu'), dove).toBeVisible();
        await expect(page.locator('.apri-menu'), dove).toBeHidden();
      } else {
        await page.locator('.apri-menu').click();
        await expect(page.locator('#menu-mobile'), dove).toBeVisible();
        await nienteFuoriSchermo(page, `${dove}, menu aperto`);
        await page.locator('.apri-menu').click();
      }

      if (url.startsWith('pezzo/') && w > h && h <= 520) {
        // telefono in orizzontale: la foto della galleria sta tutta nello schermo
        const alta = await page.locator('.galleria-nastro button').first().evaluate(b => b.getBoundingClientRect().height);
        expect(alta, `${dove}: la foto è più alta dello schermo`).toBeLessThanOrEqual(h);
      }

      const piccoli = await page.$$eval('main button, main .btn, .chip, .icona-btn, .apri-menu, .miniature button', els => els
        .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden')
        .map(el => { const b = el.getBoundingClientRect(); return { t: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30), w: Math.round(b.width), h: Math.round(b.height) }; })
        .filter(b => b.w < 24 || b.h < 24));
      expect(piccoli, `${dove}: pulsanti troppo piccoli per il dito`).toEqual([]);

      await page.screenshot({ path: info.outputPath(`${url.replace(/\W+/g, '-') || 'home'}-${w}x${h}.png`) });
      await ctx.close();
    }
  });
}

test('lo zoom del telefono non è bloccato e il testo di base è leggibile', async ({ page }) => {
  await page.goto('');
  const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
  expect(viewport).not.toMatch(/user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b/);
  expect(parseFloat(await page.evaluate(() => getComputedStyle(document.body).fontSize))).toBeGreaterThanOrEqual(16);
});
