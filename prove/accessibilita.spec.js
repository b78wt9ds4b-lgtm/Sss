// Accessibilità: le regole WCAG 2.2 A e AA che axe-core sa verificare da solo, e le prove di tastiera
// che axe non fa (salto al contenuto, focus visibile, galleria, ingrandimento). axe non trova tutto:
// lettori di schermo veri e giudizi sui testi restano da fare a mano.
const fs = require('fs');
const { test, expect } = require('@playwright/test');
const { conPiuFoto, venduti } = require('./aiuti');

const axe = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const PAGINE = ['', 'negozio/', 'categoria/mobili/', `pezzo/${conPiuFoto[0].slug}/`, `pezzo/${venduti[0].slug}/`, 'contatti/', 'non-esiste/'];

for (const url of PAGINE) {
  test(`axe /${url}`, async ({ page }) => {
    await page.goto(url);
    await page.waitForLoadState('load');
    await page.addScriptTag({ content: axe });
    const problemi = await page.evaluate(async () => (await window.axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
    })).violations.map(v => `${v.id}: ${v.nodes.slice(0, 3).map(n => n.target.join(' ')).join(' | ')}`));
    expect(problemi).toEqual([]);
  });
}

test('axe con l’ingrandimento aperto e con il menu del telefono aperto', async ({ page }, info) => {
  await page.goto(`pezzo/${conPiuFoto[0].slug}/`);
  await page.waitForLoadState('load');
  await page.addScriptTag({ content: axe });
  if (info.project.use.viewport.width < 900) {
    await page.locator('.apri-menu').click();
    expect(await page.evaluate(async () => (await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] } })).violations.map(v => v.id))).toEqual([]);
    await page.locator('.apri-menu').click();
  }
  await page.locator('.galleria-nastro button').first().click();
  await expect(page.locator('.visore')).toBeVisible();
  expect(await page.evaluate(async () => (await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] } })).violations.map(v => v.id))).toEqual([]);
});

test('tastiera: «Vai al contenuto» per primo e visibile, focus sempre visibile, galleria e ingrandimento', async ({ page, browserName }, info) => {
  test.skip(info.project.use.isMobile === true, 'la tastiera fisica si prova sulle dimensioni da computer');
  // In Safari, Tab passa ai link solo se l'utente lo attiva nelle preferenze: WebKit fa lo stesso
  test.skip(browserName === 'webkit', 'WebKit: Tab salta i link come Safari con le impostazioni predefinite');
  await page.goto(`pezzo/${conPiuFoto[0].slug}/`);
  await page.keyboard.press('Tab');
  const salta = page.locator('a.salta');
  await expect(salta).toBeFocused();
  await expect(salta).toBeInViewport();
  // avanti con Tab fino alla galleria: ogni elemento che riceve il focus deve mostrarlo
  let passi = 0;
  for (; passi < 40; passi++) {
    const stato = await page.evaluate(() => {
      const el = document.activeElement;
      const s = getComputedStyle(el);
      // Firefox si ferma anche sulla striscia della galleria (scorre di lato): si va avanti fino a una foto
      return { galleria: el.tagName === 'BUTTON' && !!el.closest('.galleria-nastro'), senzaBordo: s.outlineStyle === 'none' && s.boxShadow === 'none' ? `${el.tagName}.${el.className}` : null };
    });
    expect(stato.senzaBordo, 'elemento con il focus ma senza bordo visibile').toBeNull();
    if (stato.galleria) break;
    await page.keyboard.press('Tab');
  }
  expect(passi, 'con Tab si arriva alle foto della galleria').toBeLessThan(40);
  await page.keyboard.press('Enter');
  await expect(page.locator('.visore')).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('Escape');
  await expect(page.locator('.visore')).toBeHidden();
  expect(await page.evaluate(() => !!document.activeElement.closest('.galleria-nastro')), 'il focus torna alla galleria').toBe(true);
});
