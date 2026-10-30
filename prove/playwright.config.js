// Prove nel browser del sito in docs/, servito da strumenti/servi.py come lo servirà l'hosting
// (pagina 404 vera, cartelle con la barra, gzip).
//   cd prove && npm ci && npx playwright install chromium firefox webkit && npx playwright test
// Prima rigenera il sito: le prove leggono data/pezzi.json per sapere che cosa aspettarsi.
const { defineConfig, devices } = require('@playwright/test');

const PORTA = 8765;
const computer = { viewport: { width: 1440, height: 900 } };
const telefono = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true };

module.exports = defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: true,
  reporter: [['list']],
  use: { baseURL: `http://127.0.0.1:${PORTA}/`, locale: 'it-IT', trace: 'retain-on-failure' },
  webServer: {
    command: `python3 ../strumenti/servi.py ${PORTA}`,
    url: `http://127.0.0.1:${PORTA}/`,
    reuseExistingServer: false,
  },
  projects: [
    { name: 'chromium-telefono', use: { browserName: 'chromium', ...telefono } },
    { name: 'chromium-computer', use: { browserName: 'chromium', ...computer } },
    // Firefox non emula i telefoni (niente isMobile): solo la larghezza
    { name: 'firefox-telefono', use: { browserName: 'firefox', viewport: telefono.viewport } },
    { name: 'firefox-computer', use: { browserName: 'firefox', ...computer } },
    { name: 'webkit-telefono', use: { ...devices['iPhone 14'], browserName: 'webkit' } },
    { name: 'webkit-computer', use: { browserName: 'webkit', ...computer } },
  ],
});
