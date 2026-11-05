"""CMS build contract: seed public copy and bind it to the existing HTML layout."""
from copy import deepcopy
from html import escape
import json
import re
from lxml import html, etree


def inner(node):
    return (node.text or '') + ''.join(etree.tostring(c, encoding='unicode', method='html') for c in node)


def plain(node):
    return ''.join(node.itertext()).strip()


class CMSBuilder:
    def __init__(self):
        self.collections = {}
        self.pages = {}
        self.current = None
        self.counter = 0

    def page(self, route, document):
        self.current = {'route': route, 'records': [], 'lists': [], 'galleries': []}
        self.pages[route] = self.current
        return self.current

    def target(self, node):
        if node.get('data-cms-target'):
            return '[data-cms-target="' + node.get('data-cms-target') + '"]'
        self.counter += 1
        value = 'cms-' + str(self.counter)
        node.set('data-cms-target', value)
        return '[data-cms-target="' + value + '"]'

    def record(self, collection, key, values):
        rows = self.collections.setdefault(collection, {})
        record = {'key':key, 'isVisible':True, 'sortOrder':len(rows), **values}
        if key in rows:
            if rows[key] != record and any(rows[key].get(k) != v for k,v in values.items()):
                raise ValueError('Conflicting CMS record: ' + collection + '/' + key)
            return rows[key]
        rows[key] = record
        return record

    def singleton(self, node, collection, key, values, fields):
        self.record(collection, key, values)
        self.current['records'].append({'selector':self.target(node), 'collection':collection, 'key':key, 'fields':fields})

    def text(self, node, key, label, page, rich=False):
        if node is None:
            raise ValueError('Missing CMS text target: '+key)
        field = 'body' if rich else 'text'
        self.singleton(node, 'DiPageContent', key, {'title':label, 'page':page, field:inner(node) if rich else plain(node)}, [{'selector':':scope','field':field,'kind':'rich' if rich else 'text'}])

    def image(self, node, key, label, page, prefix=''):
        source=node.get('src','')
        while source.startswith('../'): source=source[3:]
        self.singleton(node,'DiImages',key,{'title':label,'page':page,'image':source,'alt':node.get('alt',''),'focalX':None,'focalY':None},[{'selector':':scope','field':'image','kind':'image','altField':'alt','xField':'focalX','yField':'focalY'}])

    def link(self, node, key, label, page, keep_label=False):
        source=node.get('href','')
        if not re.match(r'^(?:[a-z]+:|#|/)',source):
            while source.startswith('../'): source=source[3:]
            source='@/'+source
        fields=[{'selector':':scope','field':'url','kind':'link'}]
        data={'title':label,'page':page,'url':source}
        if not keep_label:
            # Bind the text node in a span so arrows and location icons survive.
            text=node.text or ''
            if text.strip():
                span=html.Element('span');span.text=text;node.text=None;node.insert(0,span)
                span.set('data-cms-label','')
                fields.append({'selector':'[data-cms-label]','field':'label','kind':'text'})
                data['label']=text.strip()
        self.singleton(node,'DiLinks',key,data,fields)

    def listing(self, container, collection, records, template, fields, filter=None):
        for record in records:
            self.record(collection,record['key'],record)
        entry={'selector':self.target(container),'collection':collection,'template':template,'fields':fields}
        if filter: entry['filter']=filter
        self.current['lists'].append(entry)
        return entry

    def gallery(self, node, group, photos):
        for i,p in enumerate(photos):
            self.record('DiGalleryPhotos',group+'-'+str(i+1),{'title':group+' photo '+str(i+1),'gallery':group,'sortOrder':i,**p})
        self.current['galleries'].append({'selector':self.target(node),'collection':'DiGalleryPhotos','group':group})

    def export(self):
        return {'version':1,'collections':{k:list(v.values()) for k,v in self.collections.items()}}


def outer(node):
    return etree.tostring(node,encoding='unicode',method='html',with_tail=False)


def field(selector, name, kind='text', **kwargs):
    return {'selector':selector,'field':name,'kind':kind,**kwargs}
