(() => {
  'use strict';
  const qs = (s, scope = document) => scope.querySelector(s);
  const qsa = (s, scope = document) => [...scope.querySelectorAll(s)];

  const navToggle = qs('.nav-toggle');
  const mainNav = qs('.main-nav');
  navToggle?.addEventListener('click', () => {
    const open = mainNav?.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(Boolean(open)));
  });

  const userButton = qs('[data-user-menu]');
  const userDropdown = qs('.user-dropdown');
  userButton?.addEventListener('click', (event) => {
    event.stopPropagation();
    if (userDropdown) userDropdown.hidden = !userDropdown.hidden;
  });
  document.addEventListener('click', () => { if (userDropdown) userDropdown.hidden = true; });

  qsa('.flash button').forEach(button => button.addEventListener('click', () => button.closest('.flash')?.remove()));
  setTimeout(() => qsa('.flash').forEach(el => el.remove()), 5200);

  qsa('[data-favorite]').forEach(button => {
    const key = 'tiendaGemerFavorites';
    let favorites = [];
    try { favorites = JSON.parse(localStorage.getItem(key)) || []; } catch { favorites = []; }
    const id = button.dataset.favorite;
    if (favorites.includes(id)) { button.classList.add('active'); button.textContent = '♥'; }
    button.addEventListener('click', () => {
      let current = [];
      try { current = JSON.parse(localStorage.getItem(key)) || []; } catch { current = []; }
      if (current.includes(id)) current = current.filter(item => item !== id);
      else current.push(id);
      localStorage.setItem(key, JSON.stringify(current));
      button.classList.toggle('active');
      button.textContent = button.classList.contains('active') ? '♥' : '♡';
    });
  });

  const quantity = qs('.quantity-control input');
  qsa('[data-qty]').forEach(button => button.addEventListener('click', () => {
    if (!quantity) return;
    const min = Number(quantity.min || 1);
    const max = Number(quantity.max || 99);
    const next = Number(quantity.value || 1) + (button.dataset.qty === 'plus' ? 1 : -1);
    quantity.value = String(Math.min(max, Math.max(min, next)));
  }));

  const filterToggle = qs('.filter-toggle');
  const filterPanel = qs('.filter-panel');
  filterToggle?.addEventListener('click', () => filterPanel?.classList.toggle('open'));
})();
