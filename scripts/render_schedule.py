"""The 2026–2027 schedule transcribed from the owner's supplied image.

Keep the original spelling, class labels, ages and time notation. In particular,
do not harmonize these ages with the separately supplied Dance Classes copy.
"""

from html import escape


DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
ROWS = [
    ("Trot'n Tots", '45 min Creative Movement', {'Saturday': '8:15AM'}),
    ('3-4 Year Old 1 Hr', '1 Hr Ballet, Tap, Tumbling', {'Thursday': '4:30PM', 'Saturday': '9:00AM'}),
    ('4-5 Year Old 1 Hr', '1 Hr Ballet, Tap, Tumbling', {'Tuesday': '4:00PM', 'Saturday': '10:00AM'}),
    ('5-7 Year Old 1 Hr', '1 Hr Ballet, Tap, Tumbling', {'Tuesday': '5:00PM', 'Saturday': '11:00AM'}),
    ('6-9 Year Old 1.25 Hr', '1.25 Hr Ballet, Tap, Jazz', {'Monday': '4:15PM', 'Saturday': '9:00AM'}),
    ('8-11 Year Old 1.5 Hr', '1.5 Hr Ballet, Tap, Jazz', {'Wednesday': '4:00PM', 'Saturday': '10:15AM'}),
    ('Musical Theater', '1 Hr Broadway Style Jazz & Tap', {'Wednesday': '5:30PM'}),
    ('Ballet/Pre-Pointe', '1.5 Hr 9-up', {'Monday': '5:00PM', 'Thursday': '4:30PM'}),
    ('Intro to Pointe/Pointe 1', '1Hr ages 12-up*', {'Monday': '6:00PM', 'Thursday': '5:30PM'}),
    ('Pointe 2', '1Hr ages 12-up*', {'Thursday': '6:30PM'}),
    ('Pointe 3', '1Hr ages 12-up*', {'Thursday': '7:30PM'}),
    ('Pointe Adv Tech', '1.5 Hr Levels 2 & 3 Only', {'Monday': '7:00PM'}),
    ('Jazz 1', '1 Hr ages 9-up*', {'Wednesday': '7:30PM'}),
    ('Jazz 2', '1 Hr ages 11-up*', {'Wednesday': '6:30PM'}),
    ('Jazz 3', '1 Hr ages 12-up*', {'Tuesday': '6:30PM'}),
    ('Jazz 4', '1 Hr ages 12-up*', {'Tuesday': '7:30PM'}),
    ('Contemp/Lyrical 1', '1 Hr ages 9-up*', {'Wednesday': '6:30PM'}),
    ('Contemp/Lyrical 2', '1 Hr ages 11-up*', {'Wednesday': '7:30PM'}),
    ('Contemp/Lyrical 3', '1 Hr ages 12-up*', {'Tuesday': '7:30PM'}),
    ('Contemp/Lyrical 4', '1 Hr ages 12-up*', {'Tuesday': '6:30PM'}),
    ('Hip-Hop Intro', '45 Min ages 5-8', {'Wednesday': '4:45PM'}),
    ('Hip-Hop 1', '1 Hr ages 8-11', {'Wednesday': '5:30PM'}),
    ('Hip-Hop 2', '1.25 Hr 11-Up*', {'Monday': '7:00PM'}),
    ('Hip-Hop 3', '1.25 Hr 11-Up*', {'Monday': '5:30PM'}),
    ('Leaps, Turns, Tricks Adv 1/2', '', {'Thursday': '6:30PM'}),
    ('Leaps, Turns, Tricks Adv 3/4', '', {'Tuesday': '5:30PM'}),
    ('Intro to Poms', '1 Hr Ages 9-Up', {'Thursday': '5:30PM'}),
    ('Rehearsals', 'Nutcracker & Competition', {'Friday': '4:00-7:00', 'Saturday': '12:00-5:00'}),
]
TITLE = '2026-2027 Classes Schedule'
FOOTNOTE = '*Class placement is determined by Dance Institute Instructors'
GRID_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="3" width="18" height="18"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/></svg>'


def time_key(value):
    start = value.split('-')[0].replace('AM', '').replace('PM', '')
    hour, minute = [int(part) for part in start.split(':')]
    if value.endswith('PM') and hour != 12:
        hour += 12
    return hour * 60 + minute


def render_schedule(prefix='../'):
    tabs = ''.join(
        f'<button type="button" id="day-tab-{i}" role="tab" aria-selected="{str(i == 0).lower()}" '
        f'aria-controls="day-panel-{i}" tabindex="{0 if i == 0 else -1}" data-schedule-tab="{i}">{day}</button>'
        for i, day in enumerate(DAYS)
    )
    panels = []
    for i, day in enumerate(DAYS):
        day_rows = sorted((row for row in ROWS if day in row[2]), key=lambda row: time_key(row[2][day]))
        cards = ''.join(
            '<li class="schedule-class">'
            f'<span class="schedule-time">{escape(times[day])}</span>'
            f'<div><h2>{escape(name)}</h2>'
            + (f'<p>{escape(description)}</p>' if description else '') + '</div></li>'
            for name, description, times in day_rows
        )
        panels.append(
            f'<section class="schedule-day" id="day-panel-{i}" data-schedule-panel="{i}" aria-labelledby="day-heading-{i}">'
            f'<h2 class="schedule-day-heading" id="day-heading-{i}">{day}</h2>'
            f'<ul class="schedule-class-list">{cards}</ul></section>'
        )
    source = f'{prefix}assets/images/class-schedule.png'
    return f'''<header class="page-intro section-shell schedule-intro"><h1 class="intro-title">{TITLE}</h1>
      <div class="schedule-actions"><a class="button button-dark" href="{prefix}register/index.html">Register Now</a>
      <a class="schedule-image-link" href="{source}" target="_blank" rel="noopener" data-schedule-image aria-label="View the full class schedule">{GRID_ICON}</a></div>
    </header>
    <div class="section-shell schedule-page" data-schedule>
      <div class="schedule-day-tabs" role="tablist" aria-label="Class schedule by day" hidden>{tabs}</div>
      <div class="schedule-days">{''.join(panels)}</div>
      <p class="schedule-footnote">{FOOTNOTE}</p>
    </div>
    <dialog class="schedule-dialog" aria-label="Full 2026-2027 class schedule" data-schedule-dialog>
      <button class="schedule-dialog-close" type="button" aria-label="Close full schedule" data-schedule-close>×</button>
      <img src="{source}" width="962" height="772" alt="The original class schedule for 2026-2027. All class details are available in the weekday schedule on this page." loading="lazy">
    </dialog>'''


def expected_copy():
    """Only words supplied by the owner; deduplicate repeated timetable labels."""
    values = [TITLE, 'Register Now', *DAYS, FOOTNOTE]
    for name, description, times in ROWS:
        values.extend([name, description, *times.values()])
    return list(dict.fromkeys(value for value in values if value))
