"""Bind the class catalogue and weekly timetable to owner-editable CMS rows."""

from copy import deepcopy

from lxml import html

from cms_model import field, outer, plain


DAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday')


def _class(name):
    return "contains(concat(' ', normalize-space(@class), ' '), ' " + name + " ')"


def _one(node, xpath):
    matches = node.xpath(xpath)
    if not matches:
        raise ValueError('Missing classes or schedule CMS target: ' + xpath)
    return matches[0]


def _bind_classes(builder, page):
    builder.text(_one(page, './header/h1'), 'classes-title', 'Dance Classes title', 'Dance Classes')
    builder.text(_one(page, './/p[' + _class('classes-placement') + ']'),
                 'classes-placement', 'Class placement note', 'Dance Classes')

    groups = page.xpath('.//details[' + _class('classes-group') + ']')
    for category_order, group in enumerate(groups):
        category = group.get('id')
        if not category:
            raise ValueError('Class category is missing its stable ID')
        title = _one(group, './summary/h2')
        builder.singleton(group, 'DiClassCategories', category, {
            'title': plain(title),
            'categoryOrder': category_order,
            'sortOrder': category_order,
            'isVisible': True,
        }, [field('.classes-summary h2', 'title')])

        container = _one(group, './div[' + _class('classes-rows') + ']')
        rows = container.xpath('./article[' + _class('classes-row') + ']')
        if not rows:
            raise ValueError('Class category has no cloning template: ' + category)
        records = []
        for index, row in enumerate(rows):
            paragraphs = row.xpath('./p')
            records.append({
                'key': category + '-' + str(index + 1),
                'title': plain(_one(row, './h3')),
                'description': plain(paragraphs[0]) if paragraphs else '',
                'category': category,
                'categoryOrder': category_order,
                'sortOrder': index,
                'isVisible': True,
            })
        template = deepcopy(rows[0])
        if not template.xpath('./p'):
            template.append(html.Element('p'))
        builder.listing(container, 'DiClasses', records, outer(template), [
            field('h3', 'title'),
            field('p', 'description', hideIfEmpty=True),
        ], filter={'category': category})


def _bind_schedule(builder, doc, page):
    intro = _one(doc, '//*[' + _class('schedule-intro') + ']')
    builder.text(_one(intro, './h1'), 'schedule-title', 'Class Schedule title', 'Schedule')
    builder.text(_one(page, './/p[' + _class('schedule-footnote') + ']'),
                 'schedule-footnote', 'Class Schedule placement note', 'Schedule')
    builder.link(_one(intro, './/*[' + _class('schedule-actions') + ']/a'),
                 'schedule-register', 'Schedule registration button', 'Schedule')

    container = _one(page, './/table[' + _class('schedule-table') + ']/tbody')
    rows = container.xpath('./tr')
    if not rows:
        raise ValueError('Schedule has no cloning template')
    records = []
    for index, row in enumerate(rows):
        cells = row.xpath('./td')
        if len(cells) != len(DAYS) + 1:
            raise ValueError('Schedule row does not contain six weekday cells')
        record = {
            'key': 'schedule-row-' + str(index + 1),
            'title': plain(_one(row, './th/span[' + _class('schedule-class-name') + ']')),
            'description': plain(cells[0]),
            'sortOrder': index,
            'isVisible': True,
        }
        record.update({day: plain(cell) for day, cell in zip(DAYS, cells[1:])})
        records.append(record)

    template = deepcopy(rows[0])
    header = _one(template, './th')
    if not header.xpath('./span[' + _class('schedule-mobile-detail') + ']'):
        header.append(html.Element('span', {'class': 'schedule-mobile-detail'}))
    fields = [
        field('.schedule-class-name', 'title'),
        field('.schedule-mobile-detail', 'description', hideIfEmpty=True),
        field('.schedule-class-detail', 'description'),
    ]
    for day, cell in zip(DAYS, template.xpath('./td')[1:]):
        # Every day needs a target even when the first source row has no class.
        # Cloned rows retain the original badge style only for nonempty times.
        cell.set('data-cms-day', day)
        for child in list(cell):
            cell.remove(child)
        cell.text = None
        cell.append(html.Element('span'))
        selector = '[data-cms-day="' + day + '"]'
        fields.append(field(selector + ' span', day, hideIfEmpty=True,
                            toggleClass='schedule-meeting', toggleTarget=selector))
    builder.listing(container, 'DiSchedule', records, outer(template), fields)


def bind_classes_schedule(builder, route, doc):
    """Preserve fallback HTML while supplying catalogue and schedule bindings."""
    classes = doc.xpath('//*[' + _class('classes-page') + ']')
    if classes:
        _bind_classes(builder, classes[0])
    schedules = doc.xpath('//*[' + _class('schedule-page') + ']')
    if schedules:
        _bind_schedule(builder, doc, schedules[0])
