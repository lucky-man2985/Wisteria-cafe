/* Desktop catalog disclosure; mobile navigation uses the existing menu toggle. */
(() => {
  const mobile = window.matchMedia('(max-width: 760px)');
  const revealCategory = () => {
    const sidebar = document.querySelector('.sidebar');
    const active = sidebar?.querySelector('a.active');
    if (!sidebar || !active) return;
    const frame = sidebar.getBoundingClientRect();
    const item = active.getBoundingClientRect();
    if (mobile.matches) {
      sidebar.scrollLeft += item.left - frame.left - 20;
    } else {
      const visibleHeight = Math.min(sidebar.clientHeight, Math.max(0, innerHeight - frame.top - 20));
      if (visibleHeight && (item.bottom > frame.top + visibleHeight || item.top < frame.top)) {
        sidebar.scrollTop += item.top - frame.top - Math.max(0, (visibleHeight - item.height) / 2);
      }
    }
  };
  (document.fonts?.ready || Promise.resolve()).then(() => requestAnimationFrame(revealCategory));
  const wrapper = document.querySelector('.menu-navigation');
  const toggle = wrapper?.querySelector('.catalog-toggle');
  const panel = document.getElementById('catalog-navigation');
  const header = wrapper?.closest('.header');
  if (!toggle || !panel || !header || !header.contains(panel)) return;

  const isOpen = () => !panel.hidden;
  const close = (restoreFocus = false) => {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Открыть категории меню');
    if (restoreFocus) toggle.focus();
  };

  close();
  toggle.addEventListener('click', () => {
    if (mobile.matches || isOpen()) {
      close();
      return;
    }
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Закрыть категории меню');
  });

  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || !isOpen()) return;
    event.preventDefault();
    close(true);
  });

  document.addEventListener('click', event => {
    if (isOpen() && !wrapper.contains(event.target) && !panel.contains(event.target)) close();
  });

  document.addEventListener('focusin', event => {
    if (isOpen() && !header.contains(event.target)) close();
  });

  const onViewportChange = event => {
    if (event.matches) close();
    requestAnimationFrame(revealCategory);
  };
  if (mobile.addEventListener) mobile.addEventListener('change', onViewportChange);
  else mobile.addListener(onViewportChange);
})();
