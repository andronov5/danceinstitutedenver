/* Disclosure controls use the final CMS-backed class content. */
Promise.resolve(window.siteContentReady).then(() => {
  const page = document.querySelector('.classes-page');
  if (!page) return;
  const tools = page.querySelector('[data-classes-tools]');
  const toggle = page.querySelector('[data-classes-toggle]');
  if (!tools || !toggle) return;

  const groups = [...page.querySelectorAll('.classes-group')];

  const syncToggle = () => {
    const visible = groups.filter(group => !group.hidden);
    toggle.disabled = !visible.length;
    toggle.textContent = visible.some(group => group.open) ? 'Collapse all' : 'Expand all';
  };
  toggle.addEventListener('click', () => {
    const visible = groups.filter(group => !group.hidden);
    const open = !visible.some(group => group.open);
    visible.forEach(group => { group.open = open; });
    syncToggle();
  });
  groups.forEach(group => group.addEventListener('toggle', syncToggle));
  syncToggle();
  tools.hidden = false;
});
