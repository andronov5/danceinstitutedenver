/* Native page navigation remains usable without JavaScript. */
(() => {
  const toggle = document.querySelector('.about-toggle');
  const menu = document.querySelector('.about-menu');
  if (!toggle || !menu) return;
  const close = () => { toggle.setAttribute('aria-expanded', 'false'); menu.hidden = true; };
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    menu.hidden = !open;
  });
  document.addEventListener('click', event => { if (!event.target.closest('.nav-about')) close(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !menu.hidden) { close(); toggle.focus(); }
  });
  document.querySelector('.nav-about').addEventListener('focusout', event => {
    if (!event.currentTarget.contains(event.relatedTarget)) close();
  });
})();
