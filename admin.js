(() => {
  'use strict';
  const sidebar = document.getElementById('adminSidebar');
  document.querySelector('.dash-menu')?.addEventListener('click', () => sidebar?.classList.toggle('open'));
  document.querySelectorAll('.admin-sidebar nav a').forEach(link => link.addEventListener('click', () => {
    document.querySelectorAll('.admin-sidebar nav a').forEach(item => item.classList.remove('active'));
    link.classList.add('active');
    sidebar?.classList.remove('open');
  }));
})();
