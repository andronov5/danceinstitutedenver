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
  let activeQuote = 0;
  const showQuote = direction => {
    if (!quotes.length) return;
    activeQuote = (activeQuote + direction + quotes.length) % quotes.length;
    quotes.forEach((quote, index) => { quote.hidden = index !== activeQuote; });
    const count = document.querySelector('[data-quote-current]');
    if (count) count.textContent = String(activeQuote + 1).padStart(2, '0');
  };
  document.querySelector('[data-quote-prev]')?.addEventListener('click', () => showQuote(-1));
  document.querySelector('[data-quote-next]')?.addEventListener('click', () => showQuote(1));

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
