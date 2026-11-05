/* Search and disclosure controls use the final CMS-backed class content. */
Promise.resolve(window.siteContentReady).then(() => {
  const page = document.querySelector('.classes-page');
  if (!page) return;
  const tools = page.querySelector('[data-classes-tools]');
  const search = page.querySelector('[data-classes-search]');
  const clear = page.querySelector('[data-classes-clear]');
  const toggle = page.querySelector('[data-classes-toggle]');
  const empty = page.querySelector('[data-classes-empty]');
  const reset = page.querySelector('[data-classes-reset]');
  const status = page.querySelector('[data-classes-status]');
  if (!tools || !search || !clear || !toggle || !empty || !reset || !status) return;

  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const groups = [...page.querySelectorAll('.classes-group')].map(element => {
    const heading = element.querySelector('.classes-summary h2').textContent;
    return {
      element,
      hidden: element.hidden,
      rows: [...element.querySelectorAll('.classes-row')].map(row => ({
        element: row,
        hidden: row.hidden,
        text: normalize(heading + ' ' + row.textContent)
      }))
    };
  });
  let beforeSearch = null;

  const syncToggle = () => {
    const visible = groups.filter(group => !group.element.hidden);
    toggle.disabled = !visible.length;
    toggle.textContent = visible.some(group => group.element.open) ? 'Collapse all' : 'Expand all';
  };
  const filter = (announce = true) => {
    const terms = search.value.trim().split(/\s+/).map(normalize).filter(Boolean);
    if (terms.length && !beforeSearch) beforeSearch = new Map(groups.map(group => [group.element, group.element.open]));
    let count = 0;
    groups.forEach(group => {
      let matches = 0;
      group.rows.forEach(row => {
        const show = !group.hidden && !row.hidden && terms.every(term => row.text.includes(term));
        row.element.hidden = !show;
        if (show) matches++;
      });
      group.element.hidden = group.hidden || matches === 0;
      if (terms.length && matches) group.element.open = true;
      else if (!terms.length && beforeSearch) group.element.open = beforeSearch.get(group.element);
      count += matches;
    });
    if (!terms.length) beforeSearch = null;
    clear.hidden = !search.value;
    empty.hidden = count > 0;
    if (announce) status.textContent = count === 0 ? 'No classes found.' : `${count} ${count === 1 ? 'class' : 'classes'} found.`;
    syncToggle();
  };
  const clearSearch = () => {
    search.value = '';
    filter();
    search.focus();
  };
  search.addEventListener('input', () => filter());
  search.addEventListener('search', () => filter());
  search.addEventListener('keydown', event => {
    if (event.key === 'Escape' && search.value) {
      event.preventDefault();
      clearSearch();
    }
  });
  clear.addEventListener('click', clearSearch);
  reset.addEventListener('click', clearSearch);
  toggle.addEventListener('click', () => {
    const visible = groups.filter(group => !group.element.hidden);
    const open = !visible.some(group => group.element.open);
    visible.forEach(group => { group.element.open = open; });
    syncToggle();
  });
  groups.forEach(group => group.element.addEventListener('toggle', syncToggle));
  filter(false);
  tools.hidden = false;
});
