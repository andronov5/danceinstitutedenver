/* Native page links and a complete no-JavaScript schedule remain available. */
(() => {
  'use strict';
  const schedule = document.querySelector('[data-schedule]');
  if (!schedule) return;
  const tabs = [...schedule.querySelectorAll('[data-schedule-tab]')];
  const panels = [...schedule.querySelectorAll('[data-schedule-panel]')];
  const selectDay = (index, focus = false) => {
    tabs.forEach((tab, position) => {
      const selected = index === position;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      panels[position].hidden = !selected;
    });
    if (focus) tabs[index].focus();
  };
  panels.forEach((panel, index) => {
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', tabs[index].id);
    panel.tabIndex = 0;
  });
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectDay(index));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); selectDay(next, true); }
    });
  });
  selectDay(0);
  schedule.classList.add('schedule-enhanced');
  schedule.querySelector('[role=tablist]').hidden = false;

  const imageLink = document.querySelector('[data-schedule-image]');
  const dialog = document.querySelector('[data-schedule-dialog]');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  imageLink?.addEventListener('click', event => {
    // Preserve browser-native open-in-new-tab behavior for modifier clicks.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    dialog.showModal();
  });
  dialog.querySelector('[data-schedule-close]')?.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => imageLink?.focus());
})();
