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

    toggle = _one(page, './/button[@data-classes-toggle]')
    toggle.set('data-expand-label', 'Expand all')
    toggle.set('data-collapse-label', plain(toggle))
    builder.singleton(toggle, 'DiPageContent', 'classes-disclosure-labels', {
        'title': 'Expand and collapse class groups', 'page': 'Dance Classes',
        'expandLabel': 'Expand all', 'collapseLabel': plain(toggle),
    }, [field(':scope', 'expandLabel', 'attribute', attribute='data-expand-label'),
        field(':scope', 'collapseLabel', 'attribute', attribute='data-collapse-label')])

    groups = page.xpath('.//details[' + _class('classes-group') + ']')
    if not groups:
        raise ValueError('Class catalogue has no category template')
    categories = []
    class_template = None
    for category_order, group in enumerate(groups):
        category = group.get('id')
        if not category:
            raise ValueError('Class category is missing its stable ID')
        title = _one(group, './summary/h2')
        categories.append({
            'key': category,
            'title': plain(title),
            'categoryOrder': category_order,
            'sortOrder': category_order,
            'isVisible': True,
        })

        container = _one(group, './div[' + _class('classes-rows') + ']')
        rows = container.xpath('./article[' + _class('classes-row') + ']')
        if not rows:
            raise ValueError('Class category has no cloning template: ' + category)
        for index, row in enumerate(rows):
            paragraphs = row.xpath('./p')
            builder.record('DiClasses', category + '-' + str(index + 1), {
                'title': plain(_one(row, './h3')),
                'description': plain(paragraphs[0]) if paragraphs else '',
                'category': category,
                'categoryOrder': category_order,
                'sortOrder': index,
                'isVisible': True,
            })
        if class_template is None:
            class_template = deepcopy(rows[0])
            if not class_template.xpath('./p'):
                class_template.append(html.Element('p'))

    # The category list owns its nested class rows, so added categories work
    # without another hard-coded page section or a developer-created selector.
    group_template = deepcopy(groups[0])
    group_template.attrib.pop('id', None)
    _one(group_template, './div[' + _class('classes-rows') + ']').clear()
    _one(group_template, './div').set('class', 'classes-rows')
    listing = builder.listing(
        _one(page, './/div[' + _class('classes-accordion') + ']'),
        'DiClassCategories', categories, outer(group_template),
        [field('.classes-summary h2', 'title')],
    )
    listing['children'] = [{
        'selector': '.classes-rows', 'collection': 'DiClasses',
        'match': {'field': 'category', 'parentField': 'key'},
        'template': outer(class_template),
        'fields': [field('h3', 'title'), field('p', 'description', hideIfEmpty=True)],
    }]


def _bind_schedule(builder, doc, page):
    intro = _one(doc, '//*[' + _class('schedule-intro') + ']')
    builder.text(_one(intro, './h1'), 'schedule-title', 'Class Schedule title', 'Schedule')
    builder.text(_one(page, './/p[' + _class('schedule-footnote') + ']'),
                 'schedule-footnote', 'Class Schedule placement note', 'Schedule')
    builder.link(_one(intro, './/*[' + _class('schedule-actions') + ']/a'),
                 'schedule-register', 'Schedule registration button', 'Schedule')

    table = _one(page, './/table[' + _class('schedule-table') + ']')
    heading = _one(intro, './h1')
    # Reuse the visible title record so its accessible name changes with the year.
    builder.singleton(table, 'DiPageContent', 'schedule-title',
                      {'title': 'Class Schedule title', 'page': 'Schedule', 'text': plain(heading)},
                      [field(':scope', 'text', 'attribute', attribute='aria-label')])
    for key, node in zip(('class', 'details', *DAYS), table.xpath('./thead/tr/th')):
        builder.text(node, 'schedule-column-' + key,
                     'Schedule column: ' + plain(node), 'Schedule')
    region = _one(page, './/*[' + _class('schedule-table-scroll') + ']')
    builder.singleton(region, 'DiPageContent', 'schedule-region-label',
                      {'title': 'Schedule accessible label', 'page': 'Schedule',
                       'text': region.get('aria-label', '')},
                      [field(':scope', 'text', 'attribute', attribute='aria-label')])

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
