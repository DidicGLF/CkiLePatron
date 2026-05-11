// CkiLePatron — interactions UI minimales
(function () {
  // ---- Filtres : panneau dépliable ----
  const toggle = document.querySelector('[data-filter-toggle]');
  const filters = document.querySelector('[data-filters]');
  if (toggle && filters) {
    toggle.addEventListener('click', () => {
      const open = filters.classList.toggle('is-open');
      toggle.classList.toggle('is-on', open);
    });
  }

  // ---- Recherche : submit auto au input (debounce) ----
  const search = document.getElementById('search-input');
  if (search) {
    let t;
    search.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(() => search.form && search.form.submit(), 350);
    });
  }

  // ---- Vue grille / liste (localStorage) ----
  const grid = document.getElementById('grid');
  const bGrid = document.getElementById('view-grid');
  const bList = document.getElementById('view-list');
  if (grid && bGrid && bList) {
    const apply = (v) => {
      grid.classList.toggle('grid--magazine', v === 'grid');
      grid.classList.toggle('grid--list', v === 'list');
      bGrid.classList.toggle('is-on', v === 'grid');
      bList.classList.toggle('is-on', v === 'list');
      localStorage.setItem('ckp-view', v);
    };
    apply(localStorage.getItem('ckp-view') || 'grid');
    bGrid.addEventListener('click', () => apply('grid'));
    bList.addEventListener('click', () => apply('list'));
  }

  // ---- Sélecteur de difficulté (5 bobines) ----
  document.querySelectorAll('[data-difficulty]').forEach((el) => {
    const input = el.querySelector('input[type=hidden]');
    const btns  = el.querySelectorAll('.diff-btn');
    const set = (lvl) => {
      input.value = lvl;
      btns.forEach((b, i) => b.classList.toggle('is-on', i < lvl));
    };
    btns.forEach((b, i) => {
      b.addEventListener('click', () => {
        const lvl = i + 1;
        set(parseInt(input.value, 10) === lvl ? 0 : lvl);
      });
    });
  });
})();
