"""Summer content supplied by the owner; repeated pasted prices/copy deduplicated."""
from html import escape as esc
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TITLE='2025 Summer Schedule'
DATES='Classes meet Tuesdays, Wednesdays and Thursdays from June 17th–July 31st.'
DATE_EXCEPTION='No class the week of July 4th.'
INTENSIVE=[
    ('Contemporary/Jazz','2:00-3:30','$225.00',''),
    ('Inter/Adv Ballet','3:30-5:00','$225.00','(This is for both Pointe and non-Pointe Ballet dancers.)'),
]
BOTH='$400.00 for both courses. Your dancer will have 54 hours of training this summer with our intensive. Our Intensive is perfect for dancers 11 and older that are looking to not only maintain their dance over the summer but to grow and be challenged.'
FLEX='We understand there are vacations planned and students will miss some days here and there. This intensive is designed to accommodate busy schedules with an open curriculum and an extremely discounted price. As well as, no Monday or Friday classes.'
CAMP_INFO=[
 'Schedule is subject to change or cancellation. Sign-up early to get the week you want.',
 'Full-day camp is available by combining morning and afternoon camps. Early drop-off and Late pick-up are available for an additional charge of $10.00 per 30 minutes. Our Lunch Hour is Noon-1:00 PM.',
 'Campers in both the All-day and Half-day camps are welcome to join us for lunch.'
]
CAMPS=[
 {'title':'Camp AGES 4-6 years old - $225.00','dates':'June 16th – 20th or July 14th – July 18th','body':'9:30 AM - 12:00 PM This camp includes Tap, Ballet, Tumbling, Crafts, Snack.'},
 {'title':'Camp AGES 6-9 years old - $225.00','dates':'June 23rd – 27th or July 21st - July 25th','body':'9:30 AM - 12:00 PM This camp includes Tap, Ballet, Tumbling, Hip-Hop, Video, Snack.','note':'(Parents of 8 & 9-year-old students please see Miss Michele for placement)'},
 {'title':'Afternoon Art 6-9 years old - $225.00','discount':'(There’s a $25 discount when combined with morning Dance Camp)','dates':'June 23rd – 27th or July 21st - July 25th','body':'1:00 PM - 3:30 PM Make it an all-day camp for your dancer by adding art in the afternoons. Pack a lunch and spend the afternoon relaxing with our wonderful array of art projects. Each day is a different theme.'},
 {'title':'Camp AGES 8 – 13 (Beginner/Intermediate) - $250.00','discount':'(There’s a $25 discount when combined with Hip-Hop)','dates':'July 28th – Aug 1st','body':'1:00 PM - 4:30 PM This camp is designed to quickly elevate a student’s abilities. The focus will be on Technique, Showmanship, Strength, and Flexibility in Ballet, Lyrical, Tap, and Jazz. Snack included.','note':'(Parents of 8 &; 9-year-old students please see Miss Michele for placement)'},
 {'title':'Hip-Hop Camp Ages 6 and up - $195.00','dates':'July 28th – Aug 1st','body':'10:00 AM - Noon Students will receive training from Miss Irie and guest instructors. This camp is designed to give dancers the flavor of Hip-Hop, including breaking, freestyle, and choreography. Snack included.'},
 {'title':'Nutcracker Prep Week - $100.00','dates':'Aug 18th – Aug 22nd','time':'5:00 PM - 7:00 PM (Monday – Thursday)','body':'This week prepares dancers for their Nutcracker audition. Any dancer wanting to put extra focus into their ballet dancing before they audition is encouraged to come dance with us this week.'}
]

def render_summer(prefix='../'):
    courses=''.join(f'<article class="summer-course"><h3>{esc(name)}</h3><div class="summer-course-meta"><p class="summer-time">{esc(time)}</p><p class="summer-price">{esc(price)}</p></div>'+ (f'<p class="summer-course-note">{esc(note)}</p>' if note else '') +'</article>' for name,time,price,note in INTENSIVE)
    dates=f'<p class="summer-intensive-dates"><span>{esc(DATES)}</span><span class="summer-date-exception">{esc(DATE_EXCEPTION)}</span></p>'
    combined, description=BOTH.split('. ',1)
    combined_price, combined_label=combined.split(' ',1)
    combined=f'<div class="summer-combined"><p class="summer-both"><strong>{esc(combined_price)}</strong> {esc(combined_label)}.</p><p>{esc(description)}</p></div>'
    camps=''
    # Keep the shared July week in morning-to-afternoon order.
    for camp in [CAMPS[i] for i in (0,1,2,4,3,5)]:
        heading,price=camp['title'].rsplit(' - ',1)
        title=f'<span>{esc(heading)}</span><span class="summer-camp-price"><span class="summer-price-separator"> - </span>{esc(price)}</span>'
        if 'time' in camp:
            time, body=camp['time'],camp['body']
        else:
            match=re.fullmatch(r'(\d{1,2}:\d{2} [AP]M - (?:\d{1,2}:\d{2} [AP]M|Noon)) (.+)',camp['body'])
            if not match:
                raise ValueError(f"Missing camp time: {camp['title']}")
            time,body=match.groups()
        notes=''.join(f'<p class="summer-camp-{key}">{esc(camp[key])}</p>' for key in ['discount','note'] if key in camp)
        camps+=f'''<article class="summer-camp"><h3>{title}</h3><div class="summer-camp-details"><p class="summer-camp-dates">{esc(camp['dates'])}</p><p class="summer-camp-time">{esc(time)}</p><p class="summer-camp-body">{esc(body)}</p><div class="summer-camp-notes">{notes}</div></div></article>'''
    return f'''<div class="summer-page"><header class="page-intro section-shell"><h1 class="intro-title">{TITLE}</h1></header>
<section class="section-shell summer-intensive"><div class="summer-heading"><h2>Summer Intensive</h2>{dates}</div><div class="summer-courses">{courses}</div>{combined}<p class="summer-flexibility">{esc(FLEX)}</p></section>
<section class="section-shell summer-camps"><div class="summer-heading"><h2>Summer Camps</h2><p>{esc(CAMP_INFO[0])}</p></div><div class="summer-camp-list">{camps}</div><div class="summer-camp-info"><p>{esc(CAMP_INFO[1])}</p><p>{esc(CAMP_INFO[2])}</p></div></section>
<section class="section-shell summer-registration"><a class="button button-dark" href="{prefix}register/index.html">Register Now <span aria-hidden="true">↗</span></a></section><section class="section-shell summer-contact"><h2>Interested in Learning More?</h2><a class="text-link" href="{prefix}contact/index.html">Contact Us <span aria-hidden="true">↗</span></a></section></div>'''

def write_reference():
    blocks=[TITLE,'Summer Intensive',DATES,DATE_EXCEPTION]
    for name,time,price,note in INTENSIVE: blocks.append(f'{name} {time} {price}'+(f' {note}' if note else ''))
    blocks += [BOTH,FLEX,'Summer Camps',*CAMP_INFO]
    for camp in CAMPS: blocks += [camp[k] for k in ['title','discount','dates','time','body','note'] if k in camp]
    blocks += ['Register Now','Interested in Learning More?','Contact Us']
    (ROOT/'reference/summer-request.json').write_text(json.dumps({'summer-intensive/index.html':blocks},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': write_reference()
