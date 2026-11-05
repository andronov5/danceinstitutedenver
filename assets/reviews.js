Promise.resolve(window.siteContentReady).then(() => {
  'use strict';

  document.querySelectorAll('[data-review-gallery]').forEach(section => {
    const originals = [...section.querySelectorAll('[data-review-slide]')];
    const dotContainer = section.querySelector('.review-dots');
    dotContainer.replaceChildren(...originals.map((slide, index) => {
      slide.id = 'gallery-review-' + index;
      const dot = document.createElement('button');
      dot.className = 'review-dot'; dot.type = 'button';
      dot.dataset.reviewDot = index;
      dot.setAttribute('aria-controls', slide.id);
      dot.setAttribute('aria-label', 'Show review by ' + slide.querySelector('figcaption').textContent);
      dot.setAttribute('aria-pressed', String(index === 0));
      return dot;
    }));
    section.querySelector('.review-navigation').hidden = originals.length < 2;
    if (!originals.length) section.hidden = true;
    if (originals.length < 2) return;
    const viewport = section.querySelector('.review-viewport');
    const rail = section.querySelector('.review-rail');
    const dots = [...section.querySelectorAll('[data-review-dot]')];
    const status = section.querySelector('.review-status');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const count = originals.length;
    const cloneCount = Math.min(2, count);
    const clone = slide => {
      const copy = slide.cloneNode(true);
      copy.removeAttribute('id');
      copy.removeAttribute('data-review-slide');
      copy.setAttribute('aria-hidden', 'true');
      copy.inert = true;
      return copy;
    };
    rail.prepend(...originals.slice(-cloneCount).map(clone));
    rail.append(...originals.slice(0, cloneCount).map(clone));
    const panels = [...rail.children];
    let active = 0;
    let position = cloneCount;
    let width = 0;
    let step = 0;
    let offset = 0;
    let moving = false;
    let drag = null;
    let hovered = false;
    let focused = false;
    let visible = false;
    let timer = 0;
    let finishTimer = 0;
    let resizeFrame = 0;
    let holdUntil = 0;
    const wrap = value => (value + count) % count;
    const clearTimer = () => { window.clearTimeout(timer); timer = 0; };
    const readTime = () => Math.max(10000, originals[active].querySelector('blockquote').textContent.trim().split(/\s+/).length * 320 + 2500);

    const schedule = () => {
      clearTimer();
      if (reduced.matches || hovered || focused || !visible || drag || moving || document.hidden) return;
      timer = window.setTimeout(() => move(1, false), Math.max(readTime(), holdUntil - performance.now()));
    };

    const update = manual => {
      originals.forEach((slide, index) => {
        slide.setAttribute('aria-hidden', String(index !== active));
        slide.inert = index !== active;
        slide.setAttribute('role', 'group');
        slide.setAttribute('aria-roledescription', 'slide');
        slide.setAttribute('aria-label', `Review ${index + 1} of ${count}`);
      });
      panels.forEach((panel, index) => panel.classList.toggle('is-current', index === position));
      dots.forEach((dot, index) => dot.setAttribute('aria-pressed', String(index === active)));
      if (manual) {
        const quote = originals[active].querySelector('blockquote').textContent.trim();
        const author = originals[active].querySelector('figcaption').textContent.trim();
        status.textContent = `${quote} — ${author}`;
      }
    };

    const translate = (extra = 0, animate = false) => {
      rail.style.transition = animate && !reduced.matches ? '' : 'none';
      offset = (viewport.clientWidth - width) / 2 - position * step;
      rail.style.transform = `translate3d(${offset + extra}px,0,0)`;
    };

    const finish = () => {
      window.clearTimeout(finishTimer);
      if (!moving) return;
      moving = false;
      const wrapped = position !== active + cloneCount;
      if (wrapped) section.classList.add('is-resetting');
      position = active + cloneCount;
      translate();
      update(false);
      if (wrapped) {
        rail.getBoundingClientRect();
        window.requestAnimationFrame(() => section.classList.remove('is-resetting'));
      }
      schedule();
    };

    const start = (nextPosition, nextActive, manual) => {
      if (moving) return;
      clearTimer();
      if (manual) holdUntil = performance.now() + 20000;
      active = nextActive;
      position = nextPosition;
      moving = true;
      update(manual);
      // Commit any drag or loop-reset transform before applying the transition.
      rail.getBoundingClientRect();
      translate(0, true);
      if (reduced.matches) finish();
      else finishTimer = window.setTimeout(finish, 750);
    };

    function move(direction, manual = true) {
      start(position + direction, wrap(active + direction), manual);
    }

    const choose = index => {
      if (moving || index === active) return;
      if (index === wrap(active + 1)) move(1);
      else if (index === wrap(active - 1)) move(-1);
      else start(index + cloneCount, index, true);
    };

    const measure = () => {
      window.clearTimeout(finishTimer);
      moving = false;
      position = active + cloneCount;
      width = parseFloat(getComputedStyle(originals[0]).width);
      step = width + parseFloat(getComputedStyle(rail).columnGap || 0);
      translate();
      update(false);
      schedule();
    };

    section.classList.add('reviews-ready');
    section.setAttribute('aria-roledescription', 'carousel');
    viewport.tabIndex = 0;
    viewport.setAttribute('role', 'group');
    viewport.setAttribute('aria-label', 'Student reviews. Use the arrow keys to browse.');
    measure();
    rail.addEventListener('transitionend', event => {
      if (event.target === rail && event.propertyName === 'transform') finish();
    });
    section.querySelector('[data-review-prev]').addEventListener('click', () => move(-1));
    section.querySelector('[data-review-next]').addEventListener('click', () => move(1));
    dots.forEach((dot, index) => dot.addEventListener('click', () => choose(index)));
    section.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      if (event.key === 'Home') choose(0);
      else if (event.key === 'End') choose(count - 1);
      else move(event.key === 'ArrowRight' ? 1 : -1);
    });

    section.addEventListener('pointerenter', event => {
      if (event.pointerType === 'mouse') { hovered = true; clearTimer(); }
    });
    section.addEventListener('pointerleave', event => {
      if (event.pointerType === 'mouse') { hovered = false; schedule(); }
    });
    section.addEventListener('focusin', () => { focused = true; clearTimer(); });
    section.addEventListener('focusout', () => {
      window.setTimeout(() => { focused = section.contains(document.activeElement); schedule(); }, 0);
    });

    viewport.addEventListener('pointerdown', event => {
      if (moving || !event.isPrimary || event.button !== 0) return;
      drag = { id: event.pointerId, x: event.clientX, y: event.clientY, dx: 0, axis: null, time: performance.now() };
      clearTimer();
      viewport.setPointerCapture(event.pointerId);
    });
    viewport.addEventListener('pointermove', event => {
      if (!drag || event.pointerId !== drag.id) return;
      const dx = event.clientX - drag.x;
      const dy = event.clientY - drag.y;
      if (!drag.axis && Math.max(Math.abs(dx), Math.abs(dy)) > 7) drag.axis = Math.abs(dx) > Math.abs(dy) * 1.15 ? 'x' : 'y';
      if (drag.axis !== 'x') return;
      event.preventDefault();
      drag.dx = Math.max(-width * .9, Math.min(width * .9, dx));
      viewport.classList.add('is-dragging');
      translate(drag.dx);
    });
    const endDrag = (event, cancelled = false) => {
      if (!drag || event.pointerId !== drag.id) return;
      const gesture = drag;
      drag = null;
      viewport.classList.remove('is-dragging');
      if (viewport.hasPointerCapture(event.pointerId)) viewport.releasePointerCapture(event.pointerId);
      const speed = Math.abs(gesture.dx) / Math.max(1, performance.now() - gesture.time);
      if (!cancelled && gesture.axis === 'x' && (Math.abs(gesture.dx) > Math.min(80, width * .18) || (speed > .45 && Math.abs(gesture.dx) > 22))) {
        move(gesture.dx < 0 ? 1 : -1);
      } else if (gesture.axis === 'x') {
        start(position, active, false);
      } else schedule();
    };
    viewport.addEventListener('pointerup', event => endDrag(event));
    viewport.addEventListener('pointercancel', event => endDrag(event, true));
    viewport.addEventListener('lostpointercapture', event => endDrag(event, true));

    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      schedule();
    }, { threshold: .35 });
    observer.observe(viewport);
    const resizer = new ResizeObserver(() => {
      window.cancelAnimationFrame(resizeFrame);
      resizeFrame = window.requestAnimationFrame(measure);
    });
    resizer.observe(viewport);
    document.addEventListener('visibilitychange', schedule);
    reduced.addEventListener('change', () => { if (moving && reduced.matches) finish(); schedule(); });
    document.fonts?.ready.then(measure);
  });
});
