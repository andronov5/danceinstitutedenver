#!/usr/bin/env python3
"""Generate the presentation from the captured Wix copy; no runtime dependencies."""
import json
import re
from pathlib import Path
from urllib.parse import unquote
from render_inner import render_page_content, esc
from render_content import home_features, render_register, HOME_ADDITIONS, TRIAL_TITLE, TRIAL_COPY, LERA_REVIEW
from render_about import render_teachers, render_policies
from render_classes import render_classes
from render_schedule import render_schedule
from render_summer import render_summer
from render_contact import render_contact
from render_reviews import render_reviews
from render_shows import render_nutcracker, render_competition, render_recital

ROOT = Path(__file__).resolve().parents[1]
PAGES = json.loads((ROOT / 'reference/wix-content.json').read_text())
ASSETS = json.loads((ROOT / 'reference/assets.json').read_text())
NAV = [('Home',''), ('About','about/'), ('Schedule','schedule/'), ('Shows & Competition','shows-and-competition/'), ('Summer Intensive','summer-intensive/'), ('Contact','contact/')]
ARROW = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'

def contact_form(prefix, key='contact'):
    return f'''<form class="contact-form" data-contact-form action="mailto:dance@danceinstitutedenver.com" method="post" enctype="text/plain">
      <div class="field-pair"><div class="field"><label for="{key}-first">First name<span aria-hidden="true">*</span></label><input id="{key}-first" name="firstName" autocomplete="given-name" required></div><div class="field"><label for="{key}-last">Last name<span aria-hidden="true">*</span></label><input id="{key}-last" name="lastName" autocomplete="family-name" required></div></div>
      <div class="field-pair"><div class="field"><label for="{key}-email">Email<span aria-hidden="true">*</span></label><input id="{key}-email" name="email" type="email" autocomplete="email" required></div><div class="field"><label for="{key}-phone">Phone</label><input id="{key}-phone" name="phone" type="tel" autocomplete="tel"></div></div>
      <div class="field"><label for="{key}-message">Message</label><textarea id="{key}-message" name="message" rows="3"></textarea></div>
      <div class="form-bottom"><button class="button button-dark" type="submit">Submit {ARROW}</button></div><p class="form-status" role="status" aria-live="polite"></p>
    </form>'''

def shell(title, name, content, prefix='', home=False):
    groups={'About':[('Dance Classes','dance-classes/'),('Studio Policies','about/studio-policies/'),('Teachers','about/teachers/')], 'Shows & Competition':[('Nutcracker','shows-and-competition/nutcracker/'),('Competition','shows-and-competition/competition/'),('Recital','shows-and-competition/recital/')]}
    nav_items=[]
    mobile_items=[]
    for label,route in NAV:
        if label in groups:
            identifier='about-menu' if label=='About' else 'shows-menu'
            child_links=''.join(f'<a href="{prefix}{child_route}index.html"'+(' aria-current="page"' if child_name==name else '')+f'>{esc(child_name)}</a>' for child_name,child_route in groups[label])
            active=' is-current' if any(child_name==name for child_name,_ in groups[label]) else ''
            nav_items.append(f'<div class="nav-dropdown"><button class="nav-dropdown-toggle{active}" type="button" data-dropdown-toggle aria-expanded="false" aria-controls="{identifier}">{esc(label)}<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></button><div class="nav-dropdown-menu" id="{identifier}" hidden>{child_links}</div></div>')
            mobile_items.append(f'<details class="mobile-menu-group"><summary>{esc(label)}</summary><div class="mobile-submenu">{child_links}</div></details>')
        else:
            current=' aria-current="page"' if label==name else ''
            link=f'<a href="{prefix}{route}index.html"{current}>{esc(label)}</a>'
            nav_items.append(link)
            mobile_items.append(link)
    nav=''.join(nav_items)
    mobile_nav=''.join(mobile_items)
    register_current=' aria-current="page"' if name=='Register' else ''
    class_script = f'<script src="{prefix}assets/classes.js" defer></script>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f8f5ee"><meta name="robots" content="noindex,nofollow"><title>{esc(title)} | Dance Institute</title><meta name="description" content="Dance Institute in Denver. Ballet, Tap, Lyrical, Contemporary, Pointe, Hip-Hop, Poms, Acro, Tumbling, and Jazz."><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/fonts.css"><link rel="stylesheet" href="{prefix}assets/site.css"><link rel="stylesheet" href="{prefix}assets/readability.css"><link rel="stylesheet" href="{prefix}assets/photo-layouts.css"><link rel="stylesheet" href="{prefix}assets/reviews.css"><link rel="stylesheet" href="{prefix}assets/inner-pages.css"><link rel="stylesheet" href="{prefix}assets/content-pages.css"><link rel="stylesheet" href="{prefix}assets/about-pages.css"><link rel="stylesheet" href="{prefix}assets/classes.css"><link rel="stylesheet" href="{prefix}assets/schedule.css"><link rel="stylesheet" href="{prefix}assets/summer.css"><link rel="stylesheet" href="{prefix}assets/contact-page.css"><link rel="stylesheet" href="{prefix}assets/shows.css"><link rel="stylesheet" href="{prefix}assets/pink-accents.css"><script src="{prefix}assets/site.js" defer></script><script src="{prefix}assets/content-pages.js" defer></script><script src="{prefix}assets/schedule.js" defer></script><script src="{prefix}assets/reviews.js" defer></script><script src="{prefix}assets/shows.js" defer></script></head>
<body class="{'home-page' if home else 'inner-page'}">{class_script}<a class="skip-link" href="#main">Skip to Main Content</a>
<header class="site-header"><a class="wordmark" href="{prefix}index.html" aria-label="Dance Institute home"><img class="header-logo" src="{prefix}assets/images/dance-institute-logo.png" alt="Dance Institute" width="206" height="100"></a><nav class="desktop-nav" aria-label="Main navigation">{nav}</nav><a class="header-contact" href="{prefix}register/index.html"{register_current}>Register Now {ARROW}</a><button class="menu-toggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu"><span></span><span></span></button></header>
<nav class="mobile-menu" id="mobile-menu" aria-label="Mobile navigation" hidden>{mobile_nav}<a href="{prefix}register/index.html"{register_current}>Register</a><a class="mobile-phone" href="tel:+13035250011">303-525-0011</a></nav>
<main id="main">{content}</main>
<footer class="site-footer"><div class="footer-top"><a class="footer-brand" href="{prefix}index.html">Dance Institute</a><a class="back-top" href="#main" aria-label="Back to top">↑</a></div><div class="footer-grid"><div><a href="tel:+13035250011">303-525-0011 Call or Text</a><a href="mailto:dance@danceinstitutedenver.com">dance@danceinstitutedenver.com</a></div><address><a href="https://www.google.com/maps/search/?api=1&amp;query=10515+E+40th+Ave+%23114+Denver+CO+80239" target="_blank" rel="noopener">10515 E 40th Ave<br>#114<br>Denver, CO 80239</a></address></div><div class="footer-bottom"><div><a href="{prefix}privacy-policy/index.html">Privacy Policy</a><a href="{prefix}accessibility-statement/index.html">Accessibility Statement</a></div></div></footer>
</body></html>'''

def home_content(page):
    b=page['data']['blocks']
    txt=lambda i:esc(b[i]['text'])
    # Locate quotes by heading, avoiding assumptions if source spacing changes.
    qi=next(i for i,x in enumerate(b) if x['text']=='What Our Students Say')
    quotes=[(b[qi+1+2*i]['text'],b[qi+2+2*i]['text']) for i in range(3)]
    quotes.append((LERA_REVIEW, 'Lera Andronova'))
    find=lambda text:next(i for i,x in enumerate(b) if x['text']==text)
    advantage=find('The Dance Institute Advantage')
    about=find('About Dance Institute')
    touch=find('Get in Touch')
    return f'''
<section class="hero" aria-labelledby="hero-title"><img class="hero-photo" src="assets/images/dance-hero.webp" alt="Dance Institute dancers performing together on stage" width="1235" height="806" fetchpriority="high"><div class="hero-content section-shell"><div class="hero-copy"><h1 id="hero-title"><span>Passion</span> <span><em>Moves</em> Us</span></h1><p class="hero-subtitle">{txt(1)}</p><a class="button button-cream" href="dance-classes/index.html">Discover More {ARROW}</a></div></div></section>
<aside class="home-address-bar" aria-label="Studio address"><a href="https://www.google.com/maps/search/?api=1&amp;query=10515+E+40th+Ave+%23114+Denver+CO+80239" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/></svg><span>10515 E 40th Ave, #114 · Denver, CO 80239</span></a></aside>

<section class="section-shell home-about" id="about"><div class="about-collage reveal"><img class="about-main-photo" src="assets/images/dance-community.webp" alt="Young Dance Institute dancers in pink tutus on stage" width="1100" height="1566" loading="lazy"><div class="about-small-photo"><img src="assets/images/dance-performance.webp" alt="Four young dancers in pale blue costumes on stage" loading="lazy"></div></div><div class="about-copy reveal"><h2>About<br><em>Dance Institute</em></h2><p>{txt(about+1)}</p><p>{esc(HOME_ADDITIONS[0])}</p></div><div class="home-about-more">{''.join('<p>'+esc(paragraph)+'</p>' for paragraph in HOME_ADDITIONS[1:])}</div></section>
<section class="trial-strip"><div class="section-shell"><h2>{TRIAL_TITLE}</h2><p>{TRIAL_COPY}</p><a class="button button-dark" href="schedule/index.html">Schedule {ARROW}</a></div></section>
{home_features()}
{render_reviews(quotes)}
'''

def write(path, text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')

def main():
    home=next(p for p in PAGES if p['name']=='Home')
    write(ROOT/'index.html',shell('Passion Moves Us','Home',home_content(home),home=True))
    routes=[('Dance Classes','dance-classes',render_classes('../')), ('Teachers','about/teachers',render_teachers('../../')), ('Studio Policies','about/studio-policies',render_policies('../../')), ('Schedule','schedule',render_schedule('../')), ('Nutcracker','shows-and-competition/nutcracker',render_nutcracker('../../')), ('Competition','shows-and-competition/competition',render_competition('../../')), ('Recital','shows-and-competition/recital',render_recital('../../')), ('Summer Intensive','summer-intensive',render_summer('../')), ('Contact','contact',render_contact('../').replace('<!--CONTACT_FORM-->',contact_form('../'))), ('Register','register',render_register('../'))]
    for name,route,body in routes:
        prefix='../'*len(route.split('/'))
        write(ROOT/route/'index.html',shell(name,name,body,prefix))
    for name,route in [('Privacy Policy','privacy-policy'),('Accessibility Statement','accessibility-statement')]:
        page=next(p for p in PAGES if p['name']==name)
        body=render_page_content(page,ASSETS,'../').replace('<!--CONTACT_FORM-->',contact_form('../'))
        write(ROOT/route/'index.html',shell(name,name,body,'../'))
    aliases={'about-1':'about/teachers','about':'about/teachers','shows-and-competition':'shows-and-competition/nutcracker','nutcracker':'shows-and-competition/nutcracker','class-schedule':'schedule','performances':'shows-and-competition/nutcracker','competition':'shows-and-competition/competition','registration':'register','adult-kids-dance-classes':'dance-classes','courses':'dance-classes'}
    for old,new in aliases.items():
        write(ROOT/old/'index.html',f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=../{new}/index.html"><title>Dance Institute</title></head><body><a href="../{new}/index.html">Dance Institute</a></body></html>')
    # Remove superseded example course pages from generated source/output.
    import shutil
    for directory in (ROOT/'courses').iterdir():
        if directory.is_dir(): shutil.rmtree(directory)
    print('Rendered requested pages and legacy URL redirects.')

if __name__=='__main__':main()
