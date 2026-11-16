(function () {
  var root = document.documentElement;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // language toggle (UI only; content stays in its own language)
  function applyLang(l) {
    root.setAttribute('data-ui', l);
    var q = document.getElementById('q');
    if (q) {
      if (!q.dataset.phTr) q.dataset.phTr = q.placeholder;
      q.placeholder = l === 'en' ? q.dataset.phEn : q.dataset.phTr;
    }
    updateCount();
  }
  var saved = get('ui-lang') || ((navigator.language || '').slice(0, 2) === 'tr' ? 'tr' : (navigator.language ? 'en' : 'tr'));
  var btn = document.querySelector('.lang');
  if (btn) btn.addEventListener('click', function () {
    var l = root.getAttribute('data-ui') === 'en' ? 'tr' : 'en';
    set('ui-lang', l); applyLang(l);
  });

  // filter + search on the home page
  var pubs = [].slice.call(document.querySelectorAll('.pub'));
  var tabs = [].slice.call(document.querySelectorAll('.tab'));
  var q = document.getElementById('q');
  var filter = 'all';
  function norm(s) { return (s || '').toLocaleLowerCase('tr').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ı/g, 'i'); }
  pubs.forEach(function (p) { p._q = norm(p.dataset.q); });
  function updateCount() {
    var c = document.getElementById('count');
    if (!c) return;
    var n = pubs.filter(function (p) { return !p.hidden; }).length;
    c.textContent = root.getAttribute('data-ui') === 'en' ? n + ' publications shown' : n + ' yayın gösteriliyor';
  }
  function run() {
    var term = norm(q ? q.value.trim() : '');
    pubs.forEach(function (p) {
      var ok = (filter === 'all' || p.dataset.g === filter) && (!term || p._q.indexOf(term) > -1);
      p.hidden = !ok;
    });
    [].slice.call(document.querySelectorAll('.year')).forEach(function (y) {
      y.hidden = !y.querySelector('.pub:not([hidden])');
    });
    var empty = document.getElementById('empty');
    if (empty) empty.hidden = pubs.some(function (p) { return !p.hidden; });
    updateCount();
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      filter = t.dataset.f;
      tabs.forEach(function (x) { x.setAttribute('aria-pressed', x === t ? 'true' : 'false'); });
      run();
    });
  });
  if (q) q.addEventListener('input', run);

  // copy citation
  [].slice.call(document.querySelectorAll('[data-copy]')).forEach(function (b) {
    b.addEventListener('click', function () {
      var el = document.getElementById(b.dataset.copy);
      var text = el ? el.innerText : '';
      var done = function () {
        b.setAttribute('data-done', '');
        var tr = b.querySelector('[data-tr]'), en = b.querySelector('[data-en]');
        if (tr) tr.textContent = 'Kopyalandı'; if (en) en.textContent = 'Copied';
      };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () {});
    });
  });

  applyLang(saved === 'en' ? 'en' : 'tr');
  run();
})();
