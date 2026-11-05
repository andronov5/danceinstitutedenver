"""Annotate generated pages and export the matching Wix content model."""
from copy import deepcopy
import json
from pathlib import Path
import re
import uuid
from lxml import html, etree
from cms_model import CMSBuilder, field, inner, outer, plain
from cms_bind_shows_about import bind_page
from cms_bind_summer import bind_summer
from cms_bind_classes_schedule import bind_classes_schedule

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ['', 'dance-classes', 'about/teachers', 'about/studio-policies', 'schedule',
          'shows-and-competition/nutcracker', 'shows-and-competition/competition',
          'shows-and-competition/recital', 'summer-intensive', 'contact', 'register',
          'privacy-policy', 'accessibility-statement']

def cls(name):
    return "contains(concat(' ',normalize-space(@class),' '),' "+name+" ')"

def select(doc, name):
    return doc.xpath('//*['+cls(name)+']')

def one(doc, name):
    return select(doc, name)[0]

def text(b, doc, name, key, page, rich=False):
    b.text(one(doc,name),key,name.replace('-',' ').capitalize(),page,rich)

def shared(b, route, doc):
    data = {'title':'Studio contact information', 'name':'Dance Institute',
            'phone':'303-525-0011','email':'dance@danceinstitutedenver.com',
            'address':'10515 E 40th Ave\n#114\nDenver, CO 80239'}
    def bind(node, fields): b.singleton(node,'DiStudio','studio',data,fields)
    bind(one(doc,'footer-brand'),[field(':scope','name')])
    for node in doc.xpath('//a[starts-with(@href,"tel:")]'):
        if node.xpath('ancestor::*['+cls('registration-how')+']'): continue
        suffix=' Call or Text' if 'Call or Text' in plain(node) else ''
        bind(node,[field(':scope','phone',suffix=suffix),field(':scope','phone','phoneHref')])
    for node in doc.xpath('//a[starts-with(@href,"mailto:")]'):
        bind(node,[field(':scope','email'),field(':scope','email','emailHref')])
    for node in doc.xpath('//form[@data-contact-form]'):
        bind(node,[field(':scope','email','formEmail')])
    footer=doc.xpath('//footer//address/a')[0]
    bind(footer,[field(':scope','address','addressLines'),field(':scope','address','mapHref')])
    for node in select(doc,'contact-address-link'):
        bind(node,[field('address','address','addressLines'),field(':scope','address','mapHref')])
    for node in select(doc,'home-address-bar'):
        bind(node,[field('a span','address','addressInline'),field('a','address','mapHref')])
    b.image(one(doc,'header-logo'),'studio-logo','Studio logo','All pages')

def homepage(b,doc):
    page='Home'
    # Keep the expressive title layout, with independently editable words.
    title=doc.xpath('//h1')[0]
    second=title[1]; tail=html.Element('span'); tail.text=(second[0].tail or '').strip()
    second[0].tail=' '; second.append(tail)
    for i,node in enumerate([title[0],second[0],tail]): b.text(node,'home-hero-word-'+str(i+1),'Hero title word '+str(i+1),page)
    for name,key,rich in [('hero-subtitle','home-hero-subtitle',False),('about-copy','unused',False)]:
        if name=='hero-subtitle':text(b,doc,name,key,page,rich)
    b.text(one(doc,'about-copy').xpath('./h2')[0],'home-about-title','About title',page,True)
    for i,node in enumerate(one(doc,'about-copy').xpath('./p')+one(doc,'home-about-more').xpath('./p')):
        b.text(node,'home-about-'+str(i+1),'About paragraph '+str(i+1),page)
    for name in ['hero-photo','about-main-photo','apart-photo']:
        b.image(one(doc,name),'home-'+name,name.replace('-',' '),page)
    b.image(one(doc,'about-small-photo')[0],'home-about-small-photo','About small photo',page)
    for node in one(doc,'trial-strip').xpath('.//h2|.//p'):
        b.text(node,'home-trial-'+node.tag,'Trial '+node.tag,page)
    for name,key in [('hero-copy','home-discover'),('trial-strip','home-schedule')]:
        b.link(one(doc,name).xpath('.//a')[0],key,key,page)
    b.text(doc.get_element_by_id('apart-title'),'home-apart-title','What sets us apart title',page)
    b.text(doc.get_element_by_id('testimonials-title'),'home-testimonials-title','Testimonials title',page,True)
    container=one(doc,'apart-grid'); rows=container.xpath('./article')
    records=[{'key':'feature-'+str(i+1),'title':plain(r.xpath('./h3')[0]),'body':plain(r.xpath('./p')[0]),'sortOrder':i} for i,r in enumerate(rows)]
    template=deepcopy(rows[0]);template.attrib.pop('style',None)
    b.listing(container,'DiFeatures',records,outer(template),[field('h3','title'),field('p','body')])
    container=one(doc,'review-rail'); rows=container.xpath('./figure')
    records=[{'key':'review-'+str(i+1),'title':plain(r.xpath('./figcaption')[0]),'quote':plain(r.xpath('./blockquote')[0]),'sortOrder':i} for i,r in enumerate(rows)]
    b.listing(container,'DiTestimonials',records,outer(rows[0]),[field('blockquote','quote'),field('figcaption','title')])

def registration(b,doc):
    page='Register'
    for i,node in enumerate(doc.xpath('//main//h1|//main//h2')):b.text(node,'register-heading-'+str(i+1),plain(node),page)
    for collection,container in [('DiTuition',one(doc,'tuition-grid')),('DiDiscounts',one(doc,'discount-panel').xpath('./dl')[0])]:
        rows=container.xpath('./div')
        records=[{'key':collection.lower()+'-'+str(i+1),'title':plain(r.xpath('./dt')[0]),'price':plain(r.xpath('./dd')[0]),'sortOrder':i} for i,r in enumerate(rows)]
        b.listing(container,collection,records,outer(rows[0]),[field('dt','title'),field('dd','price')])
    membership=one(doc,'membership-panel').xpath('./p')[0]
    b.singleton(membership,'DiRegistration','membership',{'title':'Membership fee','price':'$25','description':'per dancer anually'},[field('strong','price'),field('span','description')])
    b.text(one(doc,'registration-how').xpath('./p')[0],'register-instructions','Registration instructions',page,True)
    b.link(one(doc,'registration-how').xpath('./a')[0],'register-now','Register Now button',page)
    url=one(doc,'sawyer-link').xpath('./a')[0].get('href')
    for node,kind in [(one(doc,'sawyer-link').xpath('./a')[0],'link'),(one(doc,'sawyer-frame')[0],'sawyer')]:
        b.singleton(node,'DiRegistration','sawyer',{'title':'Sawyer membership link','url':url},[field(':scope','url',kind)])

NAMES={'DiStudio':'Studio contact information','DiPageContent':'Page text','DiImages':'Page photos and logo','DiLinks':'Buttons and links',
 'DiFeatures':'What sets us apart','DiTestimonials':'Testimonials','DiTuition':'Monthly tuition','DiDiscounts':'Tuition discounts',
 'DiRegistration':'Registration settings','DiTeachers':'Teachers','DiPolicies':'Studio policies','DiShowDates':'Nutcracker show dates',
 'DiCompetitionInfo':'Competition information','DiGalleryPhotos':'Photo galleries','DiSummerCourses':'Summer intensive courses',
 'DiSummerCamps':'Summer camps','DiClassCategories':'Class categories','DiClasses':'Dance classes','DiSchedule':'Weekly schedule'}

def field_type(key,values,collection=''):
    if key=='isVisible':return 'BOOLEAN'
    if key in {'sortOrder','categoryOrder','focalX','focalY'}:return 'NUMBER'
    if key=='image':return 'IMAGE'
    if key in {'body','bio'} and collection!='DiFeatures':return 'RICH_TEXT'
    return 'TEXT'

def export(b):
    seed=b.export();schemas=[];allow={}
    media_path=ROOT/'cms/media.json'
    media=json.loads(media_path.read_text()) if media_path.exists() else {}
    for collection,rows in seed['collections'].items():
        keys=list(dict.fromkeys(key for row in rows for key in row))
        allow[collection]=keys
        fields=[]
        for key in keys:
            label={'key':'Content key — keep unchanged','isVisible':'Show on website','sortOrder':'Display order','category':'Category key','focalX':'Photo horizontal focus (0–100)','focalY':'Photo vertical focus (0–100)'}.get(key,re.sub(r'([a-z])([A-Z])',r'\1 \2',key).capitalize())
            fields.append({'key':key,'displayName':label,'type':field_type(key,[r.get(key) for r in rows],collection)})
        schemas.append({'id':collection,'displayName':NAMES.get(collection,collection),'fields':fields,
          'permissions':{k:'ADMIN' for k in ['insert','update','remove','read']},
          'description':'Dance Institute website content. Edit copy and photos; keep Content key unchanged. Display order controls list order; Show on website controls visibility. Site connection must be activated before edits appear.'})
        for row in rows:
            if 'image' in row and row['image'] in media: row['image']=media[row['image']]
            row['_id']=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://danceinstitutedenver.com/cms/'+collection+'/'+row['key']))
    (ROOT/'cms/seed.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'cms/collections.json').write_text(json.dumps({'version':1,'siteId':'f3c88b1a-e358-495d-bcfd-78c490531ee8','collections':schemas},ensure_ascii=False,indent=2)+'\n')
    (ROOT/'wix/backend/content-schema.js').write_text('// Generated by scripts/cms_bind.py; only these website fields may leave Wix.\nexport const PUBLIC_COLLECTIONS = '+json.dumps(allow,indent=2)+';\n')
    print('CMS: '+str(len(schemas))+' collections, '+str(sum(len(r) for r in seed['collections'].values()))+' initial records.')

def main():
    b=CMSBuilder()
    for route in ROUTES:
        path=ROOT/route/'index.html';doc=html.document_fromstring(path.read_text());b.page(route,doc)
        # Route keys supplied to agents include /index.html as their contracts require.
        page_route=(route+'/' if route else '')+'index.html'
        shared(b,route,doc)
        if not route:homepage(b,doc)
        if route=='register':registration(b,doc)
        if route=='contact':
            b.text(doc.xpath('//main//h1')[0],'contact-title','Contact page title','Contact')
            text(b,doc,'contact-introduction','contact-introduction','Contact')
            b.image(one(doc,'contact-photo'),'contact-photo','Contact photo','Contact')
        bind_page(b,page_route,doc);bind_summer(b,page_route,doc);bind_classes_schedule(b,page_route,doc)
        payload=html.Element('script',type='application/json',id='dance-cms-bindings')
        payload.text=json.dumps(b.current,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
        doc.xpath('//body')[0].append(payload)
        prefix='../'*len(route.split('/')) if route else ''
        head=doc.xpath('//head')[0];first=head.xpath('./script')[0];index=head.index(first)
        for i,name in enumerate(['cms-wix.js','cms.js']):head.insert(index+i,html.Element('script',src=prefix+'assets/'+name,defer='defer'))
        path.write_text('<!doctype html>\n'+etree.tostring(doc,encoding='unicode',method='html')+'\n')
    export(b)

if __name__=='__main__':main()
