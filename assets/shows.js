/* Native-dialog gallery enhancement; without JavaScript, each photo remains a link. */
(() => {
  'use strict';
  const dialog = document.querySelector('[data-show-lightbox]');
  const links = [...document.querySelectorAll('[data-show-image]')];
  if (!dialog || !links.length || typeof dialog.showModal !== 'function') return;
  const image = dialog.querySelector('[data-show-full-image]');
  const close = dialog.querySelector('[data-show-close]');
  const previous = dialog.querySelector('[data-show-previous]');
  const next = dialog.querySelector('[data-show-next]');
  let current = 0;
  let returnFocus = null;
  const show = index => {
    current = (index + links.length) % links.length;
    const link = links[current];
    image.src = link.href;
    image.alt = link.querySelector('img').alt;
  };
  if (links.length < 2) {
    previous.hidden = true;
    next.hidden = true;
  }
  links.forEach((link, index) => link.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    returnFocus = link;
    show(index);
    dialog.showModal();
    close.focus();
  }));
  close.addEventListener('click', () => dialog.close());
  previous.addEventListener('click', () => show(current - 1));
  next.addEventListener('click', () => show(current + 1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(current - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(current + 1); }
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => returnFocus?.focus());
})();
