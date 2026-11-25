(() => {
  'use strict';
  function setup() {
    const body = document.body;
    if (!body.classList.contains('logged-in')) return;
    const header = document.querySelector('.main-header');
    const sidebar = document.querySelector('.main-sidebar');
    if (!header || !sidebar) return;
    const desktop = matchMedia('(min-width: 768px)');
    const sync = () => body.style.setProperty('--ps122-header-height', `${Math.ceil(header.getBoundingClientRect().height)}px`);
    sync();
    if ('ResizeObserver' in window) new ResizeObserver(sync).observe(header);
    window.addEventListener('resize', sync);
    for (const a of sidebar.querySelectorAll('.sidebar-menu > li > a')) {
      const label = a.querySelector('span:not(.pull-right-container):not(.pull-right)')?.textContent.trim();
      if (label && !a.hasAttribute('title')) a.title = label;
    }
    // A scrollable collapsed rail clips AdminLTE's old horizontal flyouts.
    // Expand it using the native control when a parent menu is selected.
    sidebar.addEventListener('click', e => {
      const a = e.target.closest('.sidebar-menu > li.treeview > a');
      if (!a || !desktop.matches || !body.classList.contains('sidebar-collapse')) return;
      const toggle = header.querySelector('[data-toggle="push-menu"]');
      if (toggle) toggle.click();
    }, true);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup, {once:true});
  else setup();
})();
