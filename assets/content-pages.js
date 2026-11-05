/* The two parent navigation items open only their requested child pages. */
(() => {
  const groups = [...document.querySelectorAll('.nav-dropdown')];
  const close = group => {
    group.querySelector('[data-dropdown-toggle]').setAttribute('aria-expanded', 'false');
    group.querySelector('.nav-dropdown-menu').hidden = true;
  };
  groups.forEach(group => {
    const toggle = group.querySelector('[data-dropdown-toggle]');
    const menu = group.querySelector('.nav-dropdown-menu');
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      groups.forEach(close);
      toggle.setAttribute('aria-expanded', String(open));
      menu.hidden = !open;
    });
    group.addEventListener('focusout', event => {
      if (!group.contains(event.relatedTarget)) close(group);
    });
    group.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !menu.hidden) { close(group); toggle.focus(); }
      if (event.key === 'ArrowDown' && event.target === toggle) {
        event.preventDefault(); groups.forEach(close);
        toggle.setAttribute('aria-expanded', 'true'); menu.hidden = false;
        menu.querySelector('a').focus();
      }
    });
  });
  document.addEventListener('click', event => {
    groups.forEach(group => { if (!group.contains(event.target)) close(group); });
  });
})();
