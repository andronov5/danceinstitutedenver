"""Home features and registration using the owner's supplied wording."""
import json
from pathlib import Path
from html import escape as esc
ROOT = Path(__file__).resolve().parents[1]
HOME_ADDITIONS = json.loads((ROOT/'reference/home-about-additions.json').read_text())
TRIAL_TITLE = 'Take a trial class!'
TRIAL_COPY = 'Drop into any class for a free trial before registering.'
LERA_REVIEW = 'Dance Institute has helped me grow in so many ways, both as a dancer and as a person, and taught me lessons I’ll carry with me for the rest of my life. I have so much love for the teachers and dancers who make it such a special place. Everyone is so supportive, and DI really feels like my second family!'
FEATURES = [
('Parental Viewing', 'Dance Institute welcomes parents to view classes. We want you to see what your child is learning and growing from the instruction provided from our teachers. We also offer comfortable chairs in a designated viewing area.'),
('Affordable Classes', 'We offer combination classes so that students receive a well-rounded dance education without the expense of attending multiple classes. You can learn hip hop dance, ballet, tap dance and more at our Denver studio.'),
('Non-competitive Atmosphere', 'No student or group of students receives more performing focus than others. All our dance students are welcomed into our dance community. Our dance studio offers a supportive atmosphere and provide an educational dance platform to allow your dancer to grow to their fullest potential.'),
('Community Focused', 'We perform at many community events throughout Denver, and at retirement homes as well. We donate show proceeds to local schools as well as raise funds for local charities.'),
('Parental Involvement', 'The Dance Institute Parent Organization (DIPO) is designated to create community within our Denver dance school. Parent involvement is key to success in any education and we encourage all our parents to become involved in our parent community.'),
('Structured Curriculum', 'The Dance Institute school year runs September through June with a recital in June. Students will ""graduate"" in June into the classes starting the following September.')]
TUITION = [('45 minutes','$75/month'),('1 hour','$80/month'),('1.25 hour','$85/month'),('1.5 hour','$90/month'),('Trot’n Tots','$80/6 weeks'),('Unlimited Classes','$275/month'),('Workshops','$25/class or included with Unlimited Membership')]
DISCOUNTS = [('2 classes','5% discount'),('3 classes:','10% discount'),('4 classes:','15% discount'),('Unlimited classes:','$275')]
INSTRUCTIONS = 'Please click “Register Now!” then click “Learn More.” Once you have purchased your membership, you will be guided through the registration process. Ignore our waitlists. We have put those in place to ensure all the appropriate discounts are applied. If you have any questions or need any assistance please call 303-525-0011.'
SAWYER = 'https://www.hisawyer.com/dance-institute-denver/schedules/membership-plans'

def home_features():
    cards = ''.join(f'<article class="apart-card" style="--card-index:{i}"><h3>{esc(title)}</h3><p>{esc(body)}</p></article>' for i,(title,body) in enumerate(FEATURES))
    return f'''<section class="apart-section" aria-labelledby="apart-title"><img class="apart-photo" src="assets/images/ballet-feet.webp" alt="" loading="lazy"><div class="apart-shade"></div><div class="section-shell apart-content"><h2 id="apart-title">What sets us apart</h2><div class="apart-grid">{cards}</div></div></section>'''

def render_register(prefix='../'):
    tuition=''.join(f'<div class="tuition-item"><dt>{esc(label)}</dt><dd>{esc(price)}</dd></div>' for label,price in TUITION)
    discounts=''.join(f'<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>' for label,value in DISCOUNTS)
    instructions=esc(INSTRUCTIONS).replace('303-525-0011', '<a href="tel:+13035250011">303-525-0011</a>')
    return f'''<div class="registration-page"><header class="page-intro section-shell"><h1 class="intro-title">Register</h1></header>
<section class="section-shell registration-prices"><div class="tuition-panel"><h2>Monthly Tuition</h2><dl class="tuition-grid">{tuition}</dl></div><div class="registration-side"><div class="discount-panel"><h2>Discounts Given</h2><dl>{discounts}</dl></div><div class="membership-panel"><h2>Membership Fee</h2><p><strong>$25</strong> <span>per dancer anually</span></p></div></div></section>
<section class="section-shell registration-how"><h2>How to Register:</h2><p>{instructions}</p><a class="button button-dark" href="#sawyer-widget">Register Now! <span aria-hidden="true">↓</span></a></section>
<section class="section-shell registration-widget" id="sawyer-widget" aria-label="Sawyer registration"><p class="sawyer-link"><a href="{SAWYER}" target="_blank" rel="noopener">Click Here</a> to register</p><div class="sawyer-frame"><iframe src="{SAWYER}" title="Dance Institute Denver registration" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="payment"></iframe></div></section></div>'''

def write_reference():
    pages = json.loads((ROOT/'reference/wix-content.json').read_text())
    home = next(p for p in pages if p['name']=='Home')['data']['blocks']
    about = next(i for i,b in enumerate(home) if b['text']=='About Dance Institute')
    reviews = next(i for i,b in enumerate(home) if b['text']=='What Our Students Say')
    expected_home = ['Passion Moves Us', home[1]['text'], 'Discover More', 'About Dance Institute', home[about+1]['text'], 'What sets us apart']
    expected_home += [x for feature in FEATURES for x in feature]
    expected_home += [b['text'] for b in home[reviews:reviews+7]] + [LERA_REVIEW, 'Lera Andronova']
    expected_home += HOME_ADDITIONS + [TRIAL_TITLE, TRIAL_COPY, 'Schedule']
    expected_register = ['Register','Monthly Tuition'] + [x for row in TUITION for x in row] + ['Discounts Given'] + [x for row in DISCOUNTS for x in row] + ['Membership Fee','$25 per dancer anually','How to Register:',INSTRUCTIONS,'Register Now!','Click Here to register']
    (ROOT/'reference/content-request.json').write_text(json.dumps({'index.html':expected_home,'register/index.html':expected_register},ensure_ascii=False,indent=2)+'\n')
