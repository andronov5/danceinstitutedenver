"""The 2026–2027 schedule transcribed from the owner's supplied image.

Keep the original spelling, class labels, ages and time notation. This timetable
is the owner-selected source of truth for class ages, levels and durations.
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


def render_schedule(prefix='../'):
    headings = ''.join(f'<th scope="col">{day}</th>' for day in DAYS)
    rows = []
    for name, description, times in ROWS:
        label = f'<span class="schedule-class-name">{escape(name)}</span>'
        if description:
            label += f'<span class="schedule-mobile-detail">{escape(description)}</span>'
        detail = f'<td class="schedule-class-detail">{escape(description)}</td>'
        cells = ''.join(
            f'<td class="schedule-meeting"><span>{escape(times[day])}</span></td>' if day in times
            else '<td></td>'
            for day in DAYS
        )
        rows.append(f'<tr><th scope="row">{label}</th>{detail}{cells}</tr>')
    return f'''<header class="page-intro section-shell schedule-intro"><h1 class="intro-title">{TITLE}</h1>
      <div class="schedule-actions"><a class="button button-dark" href="{prefix}register/index.html">Register Now</a></div>
    </header>
    <div class="section-shell schedule-page" data-schedule>
      <div class="schedule-table-scroll" role="region" aria-label="Weekly class schedule. Scroll to browse classes and days." tabindex="0">
        <table class="schedule-table" aria-label="2026-2027 class schedule" aria-describedby="schedule-footnote">
          <colgroup><col class="schedule-class-column"><col class="schedule-detail-column"><col span="6"></colgroup>
          <thead><tr><th scope="col">Class</th><th class="schedule-detail-heading" scope="col" aria-label="Class details"></th>{headings}</tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
      <p class="schedule-footnote" id="schedule-footnote">{FOOTNOTE}</p>
    </div>'''


def expected_copy():
    """Only words supplied by the owner; deduplicate repeated timetable labels."""
    values = [TITLE, 'Register Now', 'Class', *DAYS, FOOTNOTE]
    for name, description, times in ROWS:
        values.extend([name, description, *times.values()])
    return list(dict.fromkeys(value for value in values if value))
