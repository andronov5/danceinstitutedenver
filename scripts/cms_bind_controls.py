"""Owner-editable shared controls, page sections, metadata and extra content."""
import re

from lxml import html

from cms_model import field, inner, outer, plain


def cls(name):
    return "contains(concat(' ', normalize-space(@class), ' '), ' " + name + " ')"


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def label_span(node):
    """Bind wording without removing icons or required-field markers."""
    span = html.Element('span', {'data-cms-control-label': ''})
    span.text = node.text or ''
    node.text = None
    node.insert(0, span)
    return span


def attribute(builder, node, key, label, page, name, value=None):
    builder.singleton(node, 'DiPageContent', key, {
        'title': label, 'page': page, 'text': node.get(name, '') if value is None else value,
    }, [field(':scope', 'text', 'attribute', attribute=name)])


def shared_controls(builder, route, doc):
    for node in doc.xpath('//*[ ' + cls('desktop-nav') + ' or ' + cls('mobile-menu') + ']//a[not(starts-with(@href,"tel:"))]'):
        label = plain(node)
        builder.link(node, 'navigation-' + slug(label), 'Navigation: ' + label, 'All pages')
    for node in doc.xpath('//*[' + cls('nav-dropdown-toggle') + '] | //*[' + cls('mobile-menu-group') + ']/summary'):
        label = (node.text or '').strip()
        builder.text(label_span(node), 'navigation-group-' + slug(label), 'Navigation group: ' + label, 'All pages')
    builder.link(doc.xpath('//*[' + cls('header-contact') + ']')[0], 'header-register', 'Header registration button', 'All pages')
    for node in doc.xpath('//footer//*[' + cls('footer-bottom') + ']//a'):
        label = plain(node)
        builder.link(node, 'footer-' + slug(label), 'Footer: ' + label, 'All pages')
    logo = doc.xpath('//*[' + cls('wordmark') + ']')[0]
    builder.link(logo, 'logo-home-link', 'Home links', 'All pages', keep_label=True)
    builder.link(doc.xpath('//*[' + cls('footer-brand') + ']')[0], 'logo-home-link', 'Home links', 'All pages', keep_label=True)
    attribute(builder, logo, 'logo-home-label', 'Logo link accessible label', 'All pages', 'aria-label')
    button = doc.xpath('//*[' + cls('menu-toggle') + ']')[0]
    for attr, value in [('data-open-label', 'Open menu'), ('data-close-label', 'Close menu')]:
        button.set(attr, value)
        attribute(builder, button, 'navigation-' + attr, 'Navigation: ' + value, 'All pages', attr)
    for class_name, key in [('back-top', 'back-to-top'), ('skip-link', 'skip-link')]:
        node = doc.xpath('//*[' + cls(class_name) + ']')[0]
        if class_name == 'back-top':
            attribute(builder, node, key, 'Back to top accessible label', 'All pages', 'aria-label')
        else:
            builder.text(node, key, 'Skip to content label', 'All pages')


def contact_controls(builder, doc):
    for form in doc.xpath('//form[@data-contact-form]'):
        for node in form.xpath('.//label'):
            name = node.get('for').removeprefix('contact-')
            builder.text(label_span(node), 'contact-field-' + name, 'Contact form: ' + name, 'Contact')
        submit = form.xpath('.//button[@type="submit"]')[0]
        builder.text(label_span(submit), 'contact-submit-label', 'Contact submit button', 'Contact')
        defaults = {
            'data-feedback-message': 'Your email draft is ready. Send it from your email app to deliver your message. You can also email {email} directly.',
            'data-subject': 'Dance Institute inquiry',
        }
        for name, value in defaults.items():
            form.set(name, value)
            attribute(builder, form, 'contact-' + name, 'Contact form: ' + name.removeprefix('data-'), 'Contact', name)


def legal_controls(builder, route, doc):
    if route not in ('privacy-policy', 'accessibility-statement'):
        return
    title = doc.xpath('//main//h1')[0]
    builder.text(title, route + '-title', plain(title), route)
    for index, p in enumerate(doc.xpath('//*[' + cls('page-intro') + ']/p')):
        builder.text(p, route + '-introduction-' + str(index + 1), 'Introduction ' + str(index + 1), route, rich=True)
    container = doc.xpath('//*[' + cls('legal-copy') + ']')[0]
    for index, p in enumerate(container.xpath('./p')):
        builder.text(p, route + '-opening-' + str(index + 1), 'Opening paragraph ' + str(index + 1), route, rich=True)
    sections = container.xpath('./section')
    listing = html.Element('div', {'class': 'cms-legal-sections'})
    container.append(listing)
    rows = []
    for index, section in enumerate(sections):
        heading = section.xpath('./h2')[0]
        rows.append({'key': route + '-' + str(index + 1), 'page': route, 'title': plain(heading),
                     'body': ''.join(outer(child) for child in section if child is not heading), 'sortOrder': index})
        container.remove(section)
        listing.append(section)
    template = '<section><h2></h2><div data-cms-legal-body></div></section>'
    builder.listing(listing, 'DiLegalSections', rows, template,
                    [field('h2', 'title'), field('[data-cms-legal-body]', 'body', 'rich')], filter={'page': route})


def page_settings(builder, route, doc):
    key = route or 'home'
    title = doc.xpath('//head/title')[0]
    description = doc.xpath('//head/meta[@name="description"]')[0]
    values = {'title': plain(title), 'page': key, 'description': description.get('content', '')}
    builder.singleton(title, 'DiPages', key, values, [field(':scope', 'title')])
    builder.singleton(description, 'DiPages', key, values, [field(':scope', 'description', 'attribute', attribute='content')])


def section_controls(builder, route, doc):
    """Hide whole existing sections without leaving their decorative wrappers."""
    selectors = {
        '': ['hero', 'home-address-bar', 'home-about', 'trial-strip', 'apart-section', 'testimonials'],
        'dance-classes': ['classes-accordion'],
        'about/teachers': ['teacher-rows'],
        'about/studio-policies': ['policies-content'],
        'schedule': ['schedule-page'],
        'shows-and-competition/nutcracker': ['nutcracker-hero', 'nutcracker-shows', 'nutcracker-prep', 'nutcracker-auditions', 'nutcracker-rehearsals', 'nutcracker-merch', 'nutcracker-gallery', 'show-contact'],
        'shows-and-competition/competition': ['competition-opening', 'competition-introduction', 'competition-information'],
        'shows-and-competition/recital': ['recital-opening', 'recital-shows', 'recital-gala', 'recital-volunteering'],
        'summer-intensive': ['summer-intensive', 'summer-camps', 'summer-registration', 'summer-contact'],
        'contact': ['contact-introduction', 'contact-intro', 'contact-form-panel'],
        'register': ['tuition-panel', 'discount-panel', 'membership-panel', 'registration-how', 'sawyer-link', 'sawyer-frame'],
    }
    for name in selectors.get(route, []):
        nodes = doc.xpath('//*[' + cls(name) + ']')
        if not nodes:
            raise ValueError('Missing section visibility target: ' + route + '/' + name)
        builder.singleton(nodes[0], 'DiSections', (route or 'home') + '-' + name,
                          {'title': name.replace('-', ' ').capitalize(), 'page': route or 'home'}, [])


def extra_content(builder, route, doc):
    """Additional text/photo blocks use existing page routes and stay empty by default."""
    container = html.Element('div', {'class': 'section-shell cms-extra-sections'})
    doc.xpath('//main')[0].append(container)
    template = '''<section class="cms-content-block"><img class="cms-block-photo" alt="" loading="lazy" hidden><div class="cms-block-copy"><h2 hidden></h2><div class="cms-block-body" hidden></div><a class="text-link" hidden></a></div></section>'''
    # One hidden starter item exposes all field types without public placeholder copy.
    rows = [{'key': 'extra-content-template', 'page': 'home', 'title': '', 'body': '', 'image': '', 'alt': '',
             'focalX': None, 'focalY': None, 'label': '', 'url': '', 'isVisible': False, 'sortOrder': 10}]
    builder.listing(container, 'DiContentBlocks', rows, template, [
        field('h2', 'title', hideIfEmpty=True), field('.cms-block-body', 'body', 'rich', hideIfEmpty=True),
        field('img', 'image', 'image', altField='alt', xField='focalX', yField='focalY', hideIfEmpty=True),
        field('a', 'url', 'link', hideIfEmpty=True), field('a', 'label'),
    ], filter={'page': route or 'home'})


def bind_controls(builder, route, doc):
    shared_controls(builder, route, doc)
    contact_controls(builder, doc)
    legal_controls(builder, route, doc)
    page_settings(builder, route, doc)
    section_controls(builder, route, doc)
    extra_content(builder, route, doc)
    if route == 'register':
        link = doc.xpath('//*[' + cls('sawyer-link') + ']/a')[0]
        builder.text(label_span(link), 'sawyer-link-label', 'Sawyer link label', 'Register')
        tail = html.Element('span'); tail.text = link.tail or ''; link.tail = ' '
        link.addnext(tail)
        builder.text(tail, 'sawyer-link-suffix', 'Sawyer link trailing text', 'Register')
