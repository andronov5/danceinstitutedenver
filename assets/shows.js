/* Simple looping galleries, with arrows, swipes and keyboard navigation. */
Promise.resolve(window.siteContentReady).then(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const swipe = (element, navigate) => {
    let gesture = null;
    element.addEventListener('dragstart', event => event.preventDefault());
    element.addEventListener('pointerdown', event => {
      if (!event.isPrimary || event.button !== 0) return;
      gesture = { id: event.pointerId, x: event.clientX, y: event.clientY, dx: 0, dy: 0 };
      element.setPointerCapture(event.pointerId);
    });
    element.addEventListener('pointermove', event => {
      if (!gesture || gesture.id !== event.pointerId) return;
      gesture.dx = event.clientX - gesture.x;
      gesture.dy = event.clientY - gesture.y;
      if (Math.abs(gesture.dx) > Math.abs(gesture.dy) * 1.2 && Math.abs(gesture.dx) > 8) event.preventDefault();
    });
    const end = (event, cancel = false) => {
      if (!gesture || gesture.id !== event.pointerId) return;
      const { dx, dy } = gesture;
      gesture = null;
      if (element.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId);
      if (cancel || Math.abs(dx) <= Math.abs(dy) * 1.2) return;
      if (Math.abs(dx) >= 45) navigate(dx < 0 ? 1 : -1);
    };
    element.addEventListener('pointerup', event => end(event));
    element.addEventListener('pointercancel', event => end(event, true));
    element.addEventListener('lostpointercapture', event => end(event, true));
  };

  document.querySelectorAll('[data-show-gallery]').forEach(gallery => {
    const items = JSON.parse(gallery.querySelector('[data-gallery-items]').textContent);
    if (!items.length) return;
    const stage = gallery.querySelector('[data-show-stage]');
    const image = gallery.querySelector('[data-show-stage-image]');
    const status = gallery.querySelector('[data-gallery-status]');
    let current = 0;
    let visible = false;
    let timer;
    const select = (index, announce = true) => {
      current = (index + items.length) % items.length;
      const selected = items[current];
      image.src = selected.src;
      image.alt = selected.alt;
      image.style.objectPosition = selected.position || '50% 50%';
      stage.setAttribute('aria-label', selected.alt);
      if (announce) status.textContent = selected.alt;
      const nextImage = new Image();
      nextImage.src = items[(current + 1) % items.length].src;
    };
    image.addEventListener('load', () => {
      if (!reduced.matches) image.animate([{opacity: .35, transform: 'scale(1.012)'}, {opacity: 1, transform: 'scale(1)'}], {duration: 480, easing: 'ease-out'});
    });
    const restart = () => {
      clearInterval(timer);
      if (items.length < 2 || reduced.matches) return;
      timer = setInterval(() => {
        if (visible && !document.hidden && !gallery.matches(':hover, :focus-within')) select(current + 1, false);
      }, 5500);
    };
    const move = direction => { select(current + direction); restart(); };
    swipe(stage, move);
    gallery.querySelector('[data-gallery-prev]').addEventListener('click', () => move(-1));
    gallery.querySelector('[data-gallery-next]').addEventListener('click', () => move(1));
    gallery.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      select(event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : current + (event.key === 'ArrowRight' ? 1 : -1));
      restart();
    });
    gallery.classList.add('is-enhanced');
    select(0, false);
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; }, {threshold: .15});
    observer.observe(gallery);
    reduced.addEventListener('change', restart);
    restart();
  });

});
