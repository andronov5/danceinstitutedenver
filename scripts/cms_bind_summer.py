"""Expose the existing summer page copy and cards through Wix CMS."""

from copy import deepcopy

from lxml import html

from cms_model import field, inner, outer, plain


def _class(name):
    return "contains(concat(' ', normalize-space(@class), ' '), ' " + name + " ')"


def _one(node, xpath):
    matches = node.xpath(xpath)
    if not matches:
        raise ValueError('Missing summer CMS target: ' + xpath)
    return matches[0]


def _optional_text(node, class_name):
    matches = node.xpath('.//*[' + _class(class_name) + ']')
    return plain(matches[0]) if matches else ''


def _ensure_paragraph(node, class_name):
    matches = node.xpath('./p[' + _class(class_name) + ']')
    if matches:
        return matches[0]
    paragraph = html.Element('p', {'class': class_name})
    node.append(paragraph)
    return paragraph


def bind_summer(builder, route, doc):
    """Bind summer content without changing its fallback text or layout."""
    pages = doc.xpath('//*[' + _class('summer-page') + ']')
    if not pages:
        return
    page = pages[0]
    label = 'Summer Intensive'

    def text(xpath, key, title, rich=False):
        builder.text(_one(page, xpath), 'summer-' + key, title, label, rich=rich)

    text('./header/h1', 'title', 'Summer page title')
    text('.//*[' + _class('summer-intensive') + ']/*[' + _class('summer-heading') + ']/h2',
         'intensive-heading', 'Summer Intensive heading')
    text('.//p[' + _class('summer-intensive-dates') + ']/span[1]',
         'intensive-dates', 'Summer Intensive dates and days')
    text('.//*[' + _class('summer-date-exception') + ']',
         'holiday-exception', 'Summer holiday exception')
    text('.//p[' + _class('summer-both') + ']',
         'combined-price', 'Summer combined course price', rich=True)
    text('.//*[' + _class('summer-combined') + ']/p[2]',
         'combined-description', 'Summer combined course description', rich=True)
    text('.//p[' + _class('summer-flexibility') + ']',
         'flexibility', 'Summer attendance and flexibility', rich=True)
    text('.//*[' + _class('summer-camps') + ']/*[' + _class('summer-heading') + ']/h2',
         'camps-heading', 'Summer Camps heading')
    text('.//*[' + _class('summer-camps') + ']/*[' + _class('summer-heading') + ']/p',
         'camps-notice', 'Summer camp schedule notice', rich=True)
    text('.//*[' + _class('summer-camp-info') + ']/p[1]',
         'camp-logistics', 'Summer camp full day and pickup information', rich=True)
    text('.//*[' + _class('summer-camp-info') + ']/p[2]',
         'camp-lunch', 'Summer camp lunch information', rich=True)
    text('.//*[' + _class('summer-contact') + ']/h2',
         'contact-heading', 'Summer contact heading')

    courses_container = _one(page, './/*[' + _class('summer-courses') + ']')
    courses = courses_container.xpath('./article[' + _class('summer-course') + ']')
    if not courses:
        raise ValueError('Missing summer course cards')
    course_records = []
    for index, course in enumerate(courses):
        course_records.append({
            'key': 'summer-course-' + str(index + 1),
            'title': plain(_one(course, './h3')),
            'time': _optional_text(course, 'summer-time'),
            'price': _optional_text(course, 'summer-price'),
            'note': _optional_text(course, 'summer-course-note'),
            'sortOrder': index,
            'isVisible': True,
        })
    course_template = deepcopy(courses[0])
    _ensure_paragraph(course_template, 'summer-course-note')
    builder.listing(courses_container, 'DiSummerCourses', course_records,
                    outer(course_template), [
                        field('h3', 'title'),
                        field('.summer-time', 'time'),
                        field('.summer-price', 'price'),
                        field('.summer-course-note', 'note', hideIfEmpty=True),
                    ])

    camps_container = _one(page, './/*[' + _class('summer-camp-list') + ']')
    camps = camps_container.xpath('./article[' + _class('summer-camp') + ']')
    if not camps:
        raise ValueError('Missing summer camp cards')
    camp_records = []
    for index, camp in enumerate(camps):
        price = _one(camp, './h3/span[' + _class('summer-camp-price') + ']')
        camp_records.append({
            'key': 'summer-camp-' + str(index + 1),
            'title': plain(_one(camp, './h3/span[1]')),
            # The price separator is presentation, not part of the editable price.
            'price': ''.join(price.xpath('./text()')).strip(),
            'dates': _optional_text(camp, 'summer-camp-dates'),
            'time': _optional_text(camp, 'summer-camp-time'),
            'body': inner(_one(camp, './/p[' + _class('summer-camp-body') + ']')),
            'discount': _optional_text(camp, 'summer-camp-discount'),
            'note': _optional_text(camp, 'summer-camp-note'),
            'sortOrder': index,
            'isVisible': True,
        })

    camp_template = deepcopy(camps[0])
    # Add targets only to the cloning template. The published fallback is intact.
    title = _one(camp_template, './h3/span[1]')
    title.set('data-cms-camp-title', '')
    price = _one(camp_template, './h3/span[' + _class('summer-camp-price') + ']')
    price_value = ''.join(price.xpath('./text()')).strip()
    price.text = None
    for child in price:
        child.tail = None
    value_node = html.Element('span', {'class': 'summer-camp-price-value'})
    value_node.text = price_value
    price.append(value_node)
    notes = _one(camp_template, './/*[' + _class('summer-camp-notes') + ']')
    _ensure_paragraph(notes, 'summer-camp-discount')
    _ensure_paragraph(notes, 'summer-camp-note')
    builder.listing(camps_container, 'DiSummerCamps', camp_records,
                    outer(camp_template), [
                        field('[data-cms-camp-title]', 'title'),
                        field('.summer-camp-price-value', 'price'),
                        field('.summer-camp-dates', 'dates'),
                        field('.summer-camp-time', 'time'),
                        field('.summer-camp-body', 'body', 'rich'),
                        field('.summer-camp-discount', 'discount', hideIfEmpty=True),
                        field('.summer-camp-note', 'note', hideIfEmpty=True),
                    ])

    builder.link(_one(page, './/*[' + _class('summer-registration') + ']/a'),
                 'summer-register', 'Summer registration button', label)
    builder.link(_one(page, './/*[' + _class('summer-contact') + ']/a'),
                 'summer-contact', 'Summer contact button', label)
