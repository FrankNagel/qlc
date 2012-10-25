# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import urllib

import logging

import pylons.test

from pylons.util import ContextObj, PylonsContext

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
#from pylons import tmpl_context as c

from paste.deploy import appconfig
from mako.template import Template
from mako.lookup import TemplateLookup

import quanthistling.dictdata.books
from sqlalchemy import and_
from routes import url_for

def main(argv):
    log = logging.getLogger()
    logging.basicConfig(level=logging.INFO)
    
    conf = appconfig('config:development.ini', relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    #metadata.create_all(bind=Session.bind)

    c = ContextObj() 
    py_obj = PylonsContext() 
    py_obj.tmpl_context = c
    pylons.tmpl_context._push_object(c)
    c.corpushistory = model.meta.Session.query(model.Corpusversion).all()
    c.corpusversion = model.meta.Session.query(model.Corpusversion).order_by(model.Corpusversion.updated).first()
    c.iso_time = c.corpusversion.updated.strftime("%Y-%m-%dT%H:%M:%S")
    
    # template_entries_seg
    mylookup = TemplateLookup(directories=config['pylons.paths']['templates'])
    template_entries = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-entries.txt')).read()    
    template_entries_seg = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-entries.xml')).read()
    template_annotations = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-annotations.xml')).read()
    #template_annotations_seg = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-annotations-seg.xml')).read()        
         
    #http://www.cidles.eu/quanthistling/book/minor1987/hto/spa?format=xml
    for b in quanthistling.dictdata.books.list:
        c.book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        
        if c.book:

            print "Exporting XML data for %s..." % b['bibtex_key']
            
            #c = pylons.tmpl_context
            

            for c.dictdata in c.book.dictdata:
    
                c.heading = c.book.bookinfo()
                c.entries = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).order_by("startpage", "pos_on_page").all()
                #xml =  render('/derived/book/dictdata.xml')
                #xml = literal(template.render_unicode(c))

                # write base data file
                xml = Template(template_entries, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i.txt" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close
    
                # write entry file
                xml = Template(template_entries_seg, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-entries.xml" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close

                # export annotation data
                #c.heading = c.book.bookinfo() + ", Annotations"
                #c.ces_doc_url = 'http://www.cidles.eu/quanthistling' + url_for(controller='book', action='create_xml_dictdata', bibtexkey=b['bibtex_key'], startpage=c.dictdata.startpage, endpage=c.dictdata.endpage, format='xml')
                #print c.ces_doc_url
                
                print "  formatting annotations..."
                c.annotationtypes = [ "pagelayout", "formatting" ]
                c.annotationname = "formatting"

                #xml = Template(template_annotations_seg, lookup=mylookup).render_unicode(c=c)
                #oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-segformatting.xml" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)),'wb')
                #oFile.write(xml.encode("utf-8"))
                #oFile.close            
            
                xml = Template(template_annotations, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-formatting.xml" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close            

                print "  dictinterpretation annotations..."
                c.annotationtypes = [ "dictinterpretation", "orthographicinterpretation", "errata" ]
                c.annotationname = "dictinterpretation"

                #xml = Template(template_annotations_seg, lookup=mylookup).render_unicode(c=c)
                #oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-segdictinterpretation.xml" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)),'wb')
                #oFile.write(xml.encode("utf-8"))
                #oFile.close            

                xml = Template(template_annotations, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-dictinterpretation.xml" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)),'wb')
                oFile.write(xml.encode("utf-8"))
            
#            mysock = urllib.urlopen("http://localhost:5000/source/%s/create_xml_dictdata/dictionary-%i-%i.xml" % (b['bibtex_key'], data["startpage"], data["endpage"]))
#            fileToSave = mysock.read()
#            oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i.xml" % (b['bibtex_key'], data["startpage"], data["endpage"])),'wb')
#            oFile.write(fileToSave)
#            oFile.close            
#            mysock = urllib.urlopen("http://localhost:5000/source/%s/create_xml_annotations_for_dictdata/dictionary-%i-%i-formatting-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"]))
#            fileToSave = mysock.read()
#            oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-formatting-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"])),'wb')
#            oFile.write(fileToSave)
#            oFile.close            
#            mysock = urllib.urlopen("http://localhost:5000/source/%s/create_xml_annotations_for_dictdata/dictionary-%i-%i-dictinterpretation-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"]))
#            fileToSave = mysock.read()
#            oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-dictinterpretation-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"])),'wb')
#            oFile.write(fileToSave)
#            oFile.close

    pylons.tmpl_context._pop_object() 

if __name__ == "__main__":
    main(sys.argv)
