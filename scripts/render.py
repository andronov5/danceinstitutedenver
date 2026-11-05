#!/usr/bin/env python3
"""Generate the presentation from the captured Wix copy; no runtime dependencies."""
import json
import re
from pathlib import Path
from urllib.parse import unquote
from render_inner import render_page_content, render_course_detail, esc

ROOT = Path(__file__).resolve().parents[1]
PAGES = json.loads((ROOT / 'reference/wix-content.json').read_text())
ASSETS = json.loads((ROOT / 'reference/assets.json').read_text())
NAV = [('Home',''), ('Performances','performances/'), ('About','about-1/'), ('Class Schedule','class-schedule/'), ('Competition','competition/'), ('Courses','courses/')]
ARROW = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'

def contact_form(prefix, key='contact'):
    return f'''<form class="contact-form" data-contact-form action="mailto:dance@danceinstitutedenver.com" method="post" enctype="text/plain">
      <div class="field-pair"><div class="field"><label for="{key}-first">First name<span aria-hidden="true">*</span></label><input id="{key}-first" name="firstName" autocomplete="given-name" required></div><div class="field"><label for="{key}-last">Last name<span aria-hidden="true">*</span></label><input id="{key}-last" name="lastName" autocomplete="family-name" required></div></div>
      <div class="field-pair"><div class="field"><label for="{key}-email">Email<span aria-hidden="true">*</span></label><input id="{key}-email" name="email" type="email" autocomplete="email" required></div><div class="field"><label for="{key}-phone">Phone</label><input id="{key}-phone" name="phone" type="tel" autocomplete="tel"></div></div>
      <div class="field"><label for="{key}-message">Message</label><textarea id="{key}-message" name="message" rows="3"></textarea></div>
      <div class="form-bottom"><button class="button button-dark" type="submit">Submit {ARROW}</button><p class="form-note">Opens your email app.<br>Send the draft to deliver your message.</p></div><p class="form-status" role="status" aria-live="polite"></p>
    </form>'''

def shell(title, name, content, prefix='', home=False):
    nav=''.join(f'<a href="{prefix}{route}index.html"'+(' aria-current="page"' if label==name else '')+f'>{label}</a>' for label,route in NAV)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f8f5ee"><meta name="robots" content="noindex,nofollow"><title>{esc(title)} | Dance Institute</title><meta name="description" content="Dance Institute in Denver. Ballet, Tap, Lyrical, Contemporary, Pointe, Hip-Hop, Poms, Acro, Tumbling, and Jazz."><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/fonts.css"><link rel="stylesheet" href="{prefix}assets/site.css"><link rel="stylesheet" href="{prefix}assets/readability.css"><link rel="stylesheet" href="{prefix}assets/photo-layouts.css"><link rel="stylesheet" href="{prefix}assets/editorial-inner.css"><script src="{prefix}assets/site.js" defer></script></head>
<body class="{'home-page' if home else 'inner-page'}"><a class="skip-link" href="#main">Skip to Main Content</a>
<header class="site-header"><a class="wordmark" href="{prefix}index.html" aria-label="Dance Institute home"><span>Dance<br>Institute</span></a><nav class="desktop-nav" aria-label="Main navigation">{nav}</nav><a class="header-contact" href="{prefix}contact/index.html">Contact Us {ARROW}</a><button class="menu-toggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu"><span></span><span></span></button></header>
<nav class="mobile-menu" id="mobile-menu" aria-label="Mobile navigation" hidden>{nav}<a href="{prefix}contact/index.html">Contact Us</a><a class="mobile-phone" href="tel:+13035250011">303-525-0011</a></nav>
<main id="main">{content}</main>
<footer class="site-footer"><div class="footer-top"><a class="footer-brand" href="{prefix}index.html">Dance Institute</a><a class="back-top" href="#main" aria-label="Back to top">↑</a></div><div class="footer-grid"><div><a href="tel:+13035250011">303-525-0011 Call or Text</a><a href="mailto:dance@danceinstitutedenver.com">dance@danceinstitutedenver.com</a></div><address>10515 E 40th Ave<br>#114<br>Denver, CO 80239</address></div><div class="footer-bottom"><p>© 2035 by K. Larsen. Powered and secured by <a href="https://www.wix.com/">Wix</a></p><div><a href="{prefix}privacy-policy/index.html">Privacy Policy</a><a href="{prefix}accessibility-statement/index.html">Accessibility Statement</a></div></div></footer>
</body></html>'''

def home_content(page):
    b=page['data']['blocks']
    txt=lambda i:esc(b[i]['text'])
    # Locate quotes by heading, avoiding assumptions if source spacing changes.
    qi=next(i for i,x in enumerate(b) if x['text']=='What Our Students Say')
    quotes=[(b[qi+1+2*i]['text'],b[qi+2+2*i]['text']) for i in range(3)]
    find=lambda text:next(i for i,x in enumerate(b) if x['text']==text)
    advantage=find('The Dance Institute Advantage')
    about=find('About Dance Institute')
    touch=find('Get in Touch')
    quote_html=''.join(f'<figure class="quote-slide" data-quote-slide {"" if i==0 else "hidden"}><blockquote>{esc(q)}</blockquote><figcaption><span class="quote-rule"></span>{esc(author)}</figcaption></figure>' for i,(q,author) in enumerate(quotes))
    return f'''
<section class="hero" aria-labelledby="hero-title"><img class="hero-photo" src="assets/images/dance-hero.webp" alt="Dance Institute dancers performing together on stage" width="1235" height="806" fetchpriority="high"><div class="hero-content section-shell"><div class="hero-copy"><h1 id="hero-title"><span>Passion</span> <span><em>Moves</em> Us</span></h1><p class="hero-subtitle">{txt(1)}</p><a class="button button-cream" href="performances/index.html">Discover More {ARROW}</a></div></div></section>

<section class="section-shell home-about" id="about"><figure class="about-primary reveal"><img class="about-main-photo" src="assets/images/dance-community.webp" alt="Young Dance Institute dancers in pink tutus on stage" width="1100" height="1566" loading="lazy"></figure><div class="about-copy reveal"><h2>About<br><em>Dance Institute</em></h2><p>{txt(about+1)}</p></div><figure class="about-secondary reveal"><img src="assets/images/dance-performance.webp" alt="Four young dancers in pale blue costumes" width="1400" height="1025" loading="lazy"></figure></section>
<section class="programs-section" id="programs"><div class="section-shell"><div class="section-topline reveal"><div><h2>Our Dance<br><em>Programs</em></h2><p class="section-subtitle">Program Highlights</p></div></div><div class="program-browser"><div class="program-tabs reveal" role="tablist" aria-label="Dance programs"><button id="program-tab-0" role="tab" aria-selected="true" aria-controls="program-panel-0" data-program-tab="0">Ballet &amp; Contemporary<span class="tab-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg></span></button><button id="program-tab-1" role="tab" aria-selected="false" aria-controls="program-panel-1" tabindex="-1" data-program-tab="1">Hip-Hop &amp; Jazz<span class="tab-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg></span></button><button id="program-tab-2" role="tab" aria-selected="false" aria-controls="program-panel-2" tabindex="-1" data-program-tab="2">Acro &amp; Tumbling<span class="tab-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg></span></button></div><div class="program-panels reveal"><div id="program-panel-0" class="program-tab-panel" role="tabpanel" tabindex="0" aria-labelledby="program-tab-0"><img class="program-photo" src="assets/images/ballet-barre.webp" alt="Ballet dancer practicing at the barre" loading="lazy" decoding="async"><p>Grace and Expression</p></div><div id="program-panel-1" class="program-tab-panel" role="tabpanel" tabindex="0" aria-labelledby="program-tab-1" hidden><img class="program-photo" src="assets/images/dance-community.webp" alt="Young dancers performing on stage" loading="lazy" decoding="async"><p>Rhythm and Style</p></div><div id="program-panel-2" class="program-tab-panel" role="tabpanel" tabindex="0" aria-labelledby="program-tab-2" hidden><img class="program-photo" src="assets/images/dance-hero.webp" alt="Dance Institute ensemble performing on stage" loading="lazy" decoding="async"><p>Unlock your potential through our diverse offerings, designed to inspire creativity and artistic expression.</p></div></div></div><div class="performance-grid"><a class="performance-card reveal" href="performances/index.html"><h3>Nutcracker</h3><p>Annual Nutcracker in Decmber</p><span class="card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg></span></a><a class="performance-card reveal" href="competition/index.html"><h3>Competition Teams</h3><p>Competitions in April and May</p><span class="card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg></span></a><a class="performance-card reveal" href="performances/index.html"><h3>Spring Recital Showcase</h3><p>Annual Recital in early June</p><span class="card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg></span></a></div><div class="growth-note reveal"><h3>Personal Growth Through Dance</h3><p>Our students gain valuable experiences through performances, building confidence and stage presence in a supportive setting.</p></div></div></section>
<section class="testimonials section-shell reveal" aria-labelledby="testimonials-title"><div class="quote-label"><h2 id="testimonials-title">What Our <em>Students Say</em></h2></div><div class="quote-content"><div class="quote-slides" aria-live="polite">{quote_html}</div><div class="quote-controls"><div><button class="round-button" type="button" data-quote-prev aria-label="Previous testimonial">←</button><button class="round-button" type="button" data-quote-next aria-label="Next testimonial">→</button></div></div></div></section>
<section class="advantage-section"><div class="section-shell advantage-inner"><div class="advantage-title reveal"><h2>Why Dance<br><em>Institute?</em></h2><p class="section-subtitle">{txt(advantage)}</p></div><div class="advantage-copy reveal"><p>{txt(advantage+1)}</p><p>{txt(advantage+2)}</p><a class="button button-cream" href="competition/index.html">Join Us Today {ARROW}</a></div></div></section>
<section class="section-shell home-contact" id="contact"><div class="home-contact-intro reveal"><h2>Get in<br><em>Touch</em></h2><p>{txt(touch+1)}</p><a class="text-link" href="mailto:dance@danceinstitutedenver.com">dance@danceinstitutedenver.com {ARROW}</a></div><div class="home-contact-form reveal">{contact_form('', 'home')}</div></section>'''

def write(path, text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')

def main():
    home=next(p for p in PAGES if p['name']=='Home')
    write(ROOT/'index.html',shell('Passion Moves Us','Home',home_content(home),home=True))
    names={'Performances':'performances','About':'about-1','Class Schedule':'class-schedule','Competition':'competition','Contact':'contact','Privacy Policy':'privacy-policy','Accessibility Statement':'accessibility-statement','Courses':'courses'}
    for page in PAGES[1:]:
        route=names[page['name']]
        body=render_page_content(page,ASSETS,'../').replace('<!--CONTACT_FORM-->',contact_form('../'))
        write(ROOT/route/'index.html',shell(page['name'],page['name'],body,'../'))
        if route=='about-1':write(ROOT/'about/index.html',shell(page['name'],page['name'],body,'../'))
    details=json.loads((ROOT/'reference/wix-course-details.json').read_text())
    for page in details:
        slug=page['name'].lower().replace(' ','-')
        body=render_course_detail(page,ASSETS,'../../')
        write(ROOT/'courses'/slug/'index.html',shell(page['name'],'Courses',body,'../../'))
    print('Rendered 9 original navigation pages, About alias, and 6 course details.')

if __name__=='__main__':main()
