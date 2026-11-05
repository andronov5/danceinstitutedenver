/* The weekly table always stays visible; JavaScript only opens the source image. */
(() => {
  'use strict';
  const schedule = document.querySelector('[data-schedule]');
  if (!schedule) return;
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
