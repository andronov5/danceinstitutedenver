/* Small, progressive enhancements. All page copy is delivered in HTML. */
Promise.resolve(window.siteContentReady).then(() => {
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
  window.matchMedia('(min-width: 1321px)').addEventListener('change', event => { if (event.matches) setMenu(false); });

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

  document.querySelectorAll('[data-contact-form]').forEach(form => {
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const name = [data.get('firstName'), data.get('lastName')].filter(Boolean).join(' ');
      const body = `Name: ${name}\nEmail: ${data.get('email')}\nPhone: ${data.get('phone') || ''}\n\n${data.get('message') || ''}`;
      const status = form.querySelector('.form-status');
      const recipient = form.getAttribute('action').replace(/^mailto:/, '').split('?')[0];
      if (status) status.textContent = `Your email draft is ready. Send it from your email app to deliver your message. You can also email ${recipient} directly.`;
      window.location.href = `mailto:${recipient}?subject=${encodeURIComponent('Dance Institute inquiry')}&body=${encodeURIComponent(body)}`;
    });
  });

  if ('IntersectionObserver' in window && !reducedMotion.matches) {
    // Reveal small content groups once, without delaying heroes or content that
    // is already on screen. The gallery rails retain their own movement.
    const selector = [
      '.home-about .about-collage', '.home-about .about-copy > *', '.home-about-more > p',
      '.trial-strip > .section-shell', '.apart-content > h2', '.apart-card',
      '.review-heading', '.review-viewport',
      '.classes-summary', '.policy-section > h2', '.policy-copy > p', '.policy-rules',
      '.teacher-portrait', '.teacher-biography > h2', '.teacher-biography > p',
      '.show-detail-row > h2', '.show-detail-copy', '.nutcracker-audition-card',
      '.show-coming-soon', '.competition-introduction .section-shell',
      '.competition-information > h2', '.competition-info-row', '.show-contact',
      '.tuition-panel', '.discount-panel', '.membership-panel',
      '.registration-how > h2', '.registration-how > p', '.sawyer-link',
      '.summer-heading', '.summer-course', '.summer-combined', '.summer-flexibility',
      '.summer-camp', '.summer-camp-info', '.summer-contact', '.summer-registration',
      '.contact-details', '.contact-form-panel'
    ].join(',');
    const pending = new Set();
    const reveal = element => {
      if (!pending.delete(element)) return;
      element.classList.add('is-visible');
      observer.unobserve(element);
      // Restore each component's own hover transitions after the entrance.
      const finish = event => {
        if (event.target !== element || event.propertyName !== 'opacity') return;
        element.classList.remove('scroll-reveal');
        element.removeEventListener('transitionend', finish);
      };
      element.addEventListener('transitionend', finish);
    };
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) reveal(entry.target);
      });
    }, { threshold: 0.01, rootMargin: '0px 0px -24px 0px' });
    document.querySelectorAll(selector).forEach(element => {
      const bounds = element.getBoundingClientRect();
      // Avoid hidden CMS rows, nested effects, and concealing a whole long section.
      if (bounds.top < window.innerHeight || !bounds.width || !bounds.height ||
          bounds.height > window.innerHeight * .85 || element.parentElement.closest('.scroll-reveal')) return;
      element.classList.add('scroll-reveal');
      pending.add(element);
      observer.observe(element);
    });
    document.documentElement.classList.add('motion-ready');
    // Keyboard navigation must never land inside visually concealed content.
    document.addEventListener('focusin', event => {
      const element = event.target.closest('.scroll-reveal');
      if (element) reveal(element);
    });
    reducedMotion.addEventListener('change', event => {
      if (event.matches) {
        observer.disconnect();
        pending.clear();
        document.documentElement.classList.remove('motion-ready');
      }
    });
  }
});
