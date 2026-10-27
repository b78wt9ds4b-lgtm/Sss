/* DART — piccoli comportamenti della pagina. Nessuna dipendenza. */
(function () {
  'use strict';

  /* Menu su mobile */
  var apri = document.querySelector('.apri-menu');
  var menu = document.getElementById('menu-mobile');
  if (apri && menu) {
    apri.addEventListener('click', function () {
      var aperto = apri.getAttribute('aria-expanded') === 'true';
      apri.setAttribute('aria-expanded', String(!aperto));
      menu.hidden = aperto;
    });
  }

  /* Etichetta «Nuovo»: solo nei 30 giorni dopo la messa in vendita,
     così sparisce da sola anche senza ricostruire il sito */
  var oggi = Date.now();
  Array.prototype.forEach.call(document.querySelectorAll('[data-nuovo]'), function (el) {
    var dal = Date.parse(el.getAttribute('data-nuovo'));
    if (!isNaN(dal) && oggi - dal < 30 * 864e5) el.hidden = false;
  });

  /* Filtro "solo disponibili" nel catalogo; con #venduti nell'indirizzo parte già aperto */
  var interruttore = document.querySelector('[data-solo-disponibili]');
  if (interruttore) {
    var venduti = document.querySelector('.venduti');
    var mostraVenduti = function (si) {
      interruttore.setAttribute('aria-pressed', String(si));
      if (venduti) venduti.hidden = !si;
    };
    interruttore.addEventListener('click', function () {
      mostraVenduti(interruttore.getAttribute('aria-pressed') !== 'true');
    });
    if (location.hash === '#venduti' && venduti) {
      mostraVenduti(true);
      venduti.scrollIntoView();
    }
  }

  /* Condividi: sul telefono apre il menu di condivisione, altrimenti WhatsApp */
  Array.prototype.forEach.call(document.querySelectorAll('[data-condividi]'), function (link) {
    if (!navigator.share) return;
    link.addEventListener('click', function (e) {
      e.preventDefault();
      navigator.share({ title: link.getAttribute('data-titolo'), url: link.getAttribute('data-url') })
        .catch(function () { /* condivisione annullata */ });
    });
  });

  /* Galleria della scheda pezzo */
  var nastro = document.querySelector('.galleria-nastro');
  if (nastro) {
    var slide = Array.prototype.slice.call(nastro.children);
    var mini = Array.prototype.slice.call(document.querySelectorAll('.miniature button'));
    var conta = document.querySelector('.galleria-conta');
    var corrente = 0;

    var segna = function (i) {
      corrente = i;
      mini.forEach(function (b, j) { b.setAttribute('aria-current', String(i === j)); });
      if (conta) conta.textContent = (i + 1) + ' di ' + slide.length;
    };
    var vai = function (i) {
      nastro.scrollTo({ left: slide[i].offsetLeft - nastro.offsetLeft, behavior: 'smooth' });
      segna(i);
    };
    mini.forEach(function (b, i) { b.addEventListener('click', function () { vai(i); }); });

    if ('IntersectionObserver' in window) {
      var oss = new IntersectionObserver(function (voci) {
        voci.forEach(function (v) { if (v.isIntersecting) segna(slide.indexOf(v.target)); });
      }, { root: nastro, threshold: 0.6 });
      slide.forEach(function (s) { oss.observe(s); });
    }

    /* Visore a schermo intero */
    var visore = document.querySelector('.visore');
    if (visore && visore.showModal) {
      var img = visore.querySelector('img');
      var mostra = function (i) {
        corrente = (i + slide.length) % slide.length;
        img.src = slide[corrente].getAttribute('data-grande');
        img.alt = slide[corrente].querySelector('img').alt;
      };
      slide.forEach(function (s, i) {
        s.addEventListener('click', function () { mostra(i); visore.showModal(); });
      });
      visore.querySelector('.chiudi').addEventListener('click', function () { visore.close(); });
      visore.querySelector('.prec').addEventListener('click', function () { mostra(corrente - 1); });
      visore.querySelector('.succ').addEventListener('click', function () { mostra(corrente + 1); });
      visore.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') mostra(corrente - 1);
        if (e.key === 'ArrowRight') mostra(corrente + 1);
      });
      visore.addEventListener('close', function () { vai(corrente); });
    }
  }

  /* Barra d'acquisto fissa (solo telefono): resta visibile finché i pulsanti
     principali non sono sullo schermo, così prezzo e «Acquista» sono sempre a portata */
  var barra = document.querySelector('.barra-acquisto');
  var azioni = document.querySelector('.scheda-azioni');
  if (barra && azioni && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (voci) {
      barra.classList.toggle('visibile', !voci[0].isIntersecting);
    }).observe(azioni);
  }
})();
