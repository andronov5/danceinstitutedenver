/* Small, progressive enhancements. All page copy is delivered in HTML. */
(() => {
  'use strict';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const menuButton = document.querySelector('.menu-toggle');
  const menu = document.querySelector('#mobile-menu');
  const setMenu = (open, restoreFocus = false) => {
    if (!menu || !menuButton) return;
    menu.hidden = !open;
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.classList.toggle('menu-open', open);
    if (restoreFocus) menuButton.focus();
  };
  menuButton?.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
  menu?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', event => {
    if (!menu || menu.hidden) return;
    if (event.key === 'Escape') { setMenu(false, true); return; }
    if (event.key === 'Tab') {
      const links = [...menu.querySelectorAll('a')];
      const first = menuButton, last = links.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });
  window.matchMedia('(min-width: 1201px)').addEventListener('change', event => { if (event.matches) setMenu(false); });

  const tabs = [...document.querySelectorAll('[data-program-tab]')];
  const selectTab = (index, focus = false) => {
    tabs.forEach((tab, position) => {
      const selected = position === index;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      if (panel) panel.hidden = !selected;
    });
    if (focus) tabs[index]?.focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTab(index));
    tab.addEventListener('keydown', event => {
      let next;
      if (['ArrowRight', 'ArrowDown'].includes(event.key)) next = (index + 1) % tabs.length;
      if (['ArrowLeft', 'ArrowUp'].includes(event.key)) next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); selectTab(next, true); }
    });
  });

  const quotes = [...document.querySelectorAll('[data-quote-slide]')];
  if (quotes.length) {
    const section = document.querySelector('.testimonials');
    const content = section.querySelector('.quote-content');
    const stage = section.querySelector('.review-stage');
    const dots = [...section.querySelectorAll('[data-quote-index]')];
    const play = section.querySelector('[data-quote-play]');
    const progress = section.querySelector('.review-progress span');
    const status = section.querySelector('.review-status');
    let activeQuote = 0;
    let userPaused = reducedMotion.matches;
    let hovered = false, focused = false, inView = false;
    let elapsed = 0, lastFrame = 0, animationFrame = 0;
    const duration = () => Math.max(9000, quotes[activeQuote].querySelector('blockquote').textContent.trim().split(/\s+/).length * 340);
    const paintProgress = () => { progress.style.transform = `scaleX(${Math.min(1, elapsed / duration())})`; };
    const selectQuote = (index, manual = false) => {
      activeQuote = (index + quotes.length) % quotes.length;
      quotes.forEach((quote, position) => {
        const active = position === activeQuote;
        quote.classList.toggle('is-active', active);
        quote.classList.toggle('is-next', position === (activeQuote + 1) % quotes.length);
        quote.classList.toggle('is-previous', position === (activeQuote - 1 + quotes.length) % quotes.length);
        quote.classList.toggle('is-away', !active && position !== (activeQuote + 1) % quotes.length && position !== (activeQuote - 1 + quotes.length) % quotes.length);
        quote.hidden = false;
        quote.inert = !active;
        quote.setAttribute('aria-hidden', String(!active));
      });
      dots.forEach((dot, position) => dot.setAttribute('aria-pressed', String(position === activeQuote)));
      elapsed = 0;
      paintProgress();
      if (manual) {
        userPaused = true;
        status.textContent = `${quotes[activeQuote].querySelector('blockquote').textContent.trim()} — ${quotes[activeQuote].querySelector('figcaption').textContent.trim()}`;
        syncPlayback();
      }
    };
    const tick = timestamp => {
      if (lastFrame) elapsed += timestamp - lastFrame;
      lastFrame = timestamp;
      if (elapsed >= duration()) selectQuote(activeQuote + 1);
      paintProgress();
      animationFrame = requestAnimationFrame(tick);
    };
    const syncPlayback = () => {
      cancelAnimationFrame(animationFrame);
      animationFrame = 0;
      lastFrame = 0;
      const paused = userPaused || hovered || focused || !inView || document.hidden;
      section.classList.toggle('reviews-paused', paused);
      play.classList.toggle('is-paused', userPaused);
      play.setAttribute('aria-pressed', String(userPaused));
      play.setAttribute('aria-label', userPaused ? 'Play automatic reviews' : 'Pause automatic reviews');
      if (!paused) animationFrame = requestAnimationFrame(tick);
    };
    section.classList.add('reviews-ready');
    selectQuote(0);
    section.querySelector('[data-quote-prev]').addEventListener('click', () => selectQuote(activeQuote - 1, true));
    section.querySelector('[data-quote-next]').addEventListener('click', () => selectQuote(activeQuote + 1, true));
    dots.forEach(dot => dot.addEventListener('click', () => selectQuote(Number(dot.dataset.quoteIndex), true)));
    play.addEventListener('click', () => {
      userPaused = !userPaused;
      // An explicit Play action may resume while its own button keeps focus.
      if (!userPaused) focused = false;
      syncPlayback();
    });
    content.addEventListener('mouseenter', () => { hovered = true; syncPlayback(); });
    content.addEventListener('mouseleave', () => { hovered = false; syncPlayback(); });
    content.addEventListener('focusin', () => { focused = true; syncPlayback(); });
    content.addEventListener('focusout', () => queueMicrotask(() => { focused = content.contains(document.activeElement); syncPlayback(); }));
    content.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? quotes.length - 1 : activeQuote + (event.key === 'ArrowRight' ? 1 : -1);
      selectQuote(next, true);
    });
    document.addEventListener('visibilitychange', syncPlayback);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(entries => { inView = entries[0].isIntersecting && entries[0].intersectionRatio >= .2; syncPlayback(); }, { threshold: .2 }).observe(stage);
    } else { inView = true; }
    let swipeStart = null;
    stage.addEventListener('pointerdown', event => {
      if (event.pointerType !== 'mouse') swipeStart = { x: event.clientX, y: event.clientY };
    });
    stage.addEventListener('pointerup', event => {
      if (!swipeStart) return;
      const dx = event.clientX - swipeStart.x, dy = event.clientY - swipeStart.y;
      swipeStart = null;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.4) selectQuote(activeQuote + (dx < 0 ? 1 : -1), true);
    });
    stage.addEventListener('pointercancel', () => { swipeStart = null; });
    const resetTilt = () => { stage.style.setProperty('--review-tilt-x', '0deg'); stage.style.setProperty('--review-tilt-y', '0deg'); };
    stage.addEventListener('pointermove', event => {
      if (event.pointerType !== 'mouse' || reducedMotion.matches) return;
      const box = stage.getBoundingClientRect();
      stage.style.setProperty('--review-tilt-x', `${((event.clientY - box.top) / box.height - .5) * -3}deg`);
      stage.style.setProperty('--review-tilt-y', `${((event.clientX - box.left) / box.width - .5) * 3}deg`);
    });
    stage.addEventListener('pointerleave', resetTilt);
    reducedMotion.addEventListener('change', event => {
      if (event.matches) { userPaused = true; resetTilt(); syncPlayback(); }
    });
    syncPlayback();
  }

  document.querySelectorAll('[data-contact-form]').forEach(form => {
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const name = [data.get('firstName'), data.get('lastName')].filter(Boolean).join(' ');
      const body = `Name: ${name}\nEmail: ${data.get('email')}\nPhone: ${data.get('phone') || ''}\n\n${data.get('message') || ''}`;
      const status = form.querySelector('.form-status');
      if (status) status.textContent = 'Your email draft is ready. Send it from your email app to deliver your message. You can also email dance@danceinstitutedenver.com directly.';
      window.location.href = `mailto:dance@danceinstitutedenver.com?subject=${encodeURIComponent('Dance Institute inquiry')}&body=${encodeURIComponent(body)}`;
    });
  });

  if ('IntersectionObserver' in window && !reducedMotion.matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
      });
    }, { threshold: 0.06 });
    document.querySelectorAll('.reveal').forEach(element => observer.observe(element));
    document.documentElement.classList.add('motion-ready');
    reducedMotion.addEventListener('change', event => {
      if (event.matches) { observer.disconnect(); document.documentElement.classList.remove('motion-ready'); }
    });
  }
})();
