# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import collections
import tempfile
import glob
import zipfile
import shutil

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
    c.iso_time = c.corpusversion.updated.strftime("%Y-%m-%d")
    
    # template_entries_seg
    mylookup = TemplateLookup(directories=config['pylons.paths']['templates'])
    template_header = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-header.hdr')).read()    
    template_entries = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-entries.txt')).read()    
    template_entries_seg = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-entries.xml')).read()
    template_annotations = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-annotations.xml')).read()
    #template_annotations_seg = open(os.path.join(config['pylons.paths']['templates'][0], 'base', 'graf-annotations-seg.xml')).read()        
         
    #http://www.cidles.eu/quanthistling/book/minor1987/hto/spa?format=xml
    for b in quanthistling.dictdata.books.list:
        #if b['bibtex_key'] != "leach1969":
        #    continue

        c.book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        
        if False:
        #if c.book:

            print "Exporting XML data for %s..." % b['bibtex_key']
            #temppath = tempfile.mkdtemp()
            temppath = os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', b['bibtex_key'])
            if not os.path.exists(temppath):
                os.mkdir(temppath)
            else:
                files = glob.glob(os.path.join(temppath, "*"))
                for f in files:
                    os.remove(f)

            for c.dictdata in c.book.dictdata:
                
                print "  header..."
    
                c.url_for = url_for
                c.base_url = "http://www.quanthistling.info/data"
                #c.relative_url = url_for(controller='book', action='dictdata', bibtexkey=c.book.bibtex_key, startpage=c.dictdata.startpage, endpage=c.dictdata.endpage, format='html')

                #c.heading = c.book.bookinfo()
                c.basename = "dict-%s-%i-%i" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)
                c.entries = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).order_by("startpage", "pos_on_page").all()

                annotations = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).order_by("startpage", "pos_on_page").all()
                c.annotations = collections.defaultdict(dict)
                for a in annotations:
                    if not c.annotations[a.entry_id]:
                        c.annotations[a.entry_id] = collections.defaultdict(list)
                    c.annotations[a.entry_id][(a.start, a.end)].append(a)

                c.count_heads = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"head").count()
                c.count_translations = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"translation").count()
                c.count_pos = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"pos").count()
                c.count_examples_src = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"example-src").count()
                c.count_examples_tgt = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"example-tgt").count()
                c.count_manually_corrected = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Entry.has_manual_annotations==True).count()

                #xml =  render('/derived/book/dictdata.xml')
                #xml = literal(template.render_unicode(c))

                # write header
                xml = Template(template_header, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(temppath, "%s.hdr" % c.basename),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close()

                print "  base data..."

                # write base data file
                xml = Template(template_entries, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(temppath, "%s.txt" % c.basename),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close()
    
                print "  entries..."

                # write entry file
                xml = Template(template_entries_seg, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(temppath, "%s-entries.xml" % c.basename),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close()

                print "  formatting annotations..."

                c.annotationtypes = [ "pagelayout", "formatting" ]
                c.annotationname = "formatting"
            
                xml = Template(template_annotations, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(temppath, "%s-formatting.xml" % c.basename),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close()          

                print "  dictinterpretation annotations..."
                c.annotationtypes = [ "dictinterpretation", "orthographicinterpretation", "errata" ]

                c.annotationname = "dictinterpretation"

                xml = Template(template_annotations, lookup=mylookup).render_unicode(c=c)
                oFile = open(os.path.join(temppath, "%s-dictinterpretation.xml" % c.basename),'wb')
                oFile.write(xml.encode("utf-8"))
                oFile.close()

            # create archive
            myzip = zipfile.ZipFile(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', '%s.zip' % b['bibtex_key']), 'w', zipfile.ZIP_DEFLATED)
            for file in glob.glob(os.path.join(temppath, "*.*")):
                myzip.write(file, os.path.basename(file))
            myzip.close()
            #shutil.rmtree(temppath)
        
    myzip = zipfile.ZipFile(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', 'data.zip'), 'w', zipfile.ZIP_DEFLATED)
    graf_dirs = [d for d in glob.glob(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "*")) if os.path.isdir(d)]
    for d in graf_dirs:
        bibtex_key = d[d.rfind(os.sep)+1:]
        for f in glob.glob(os.path.join(d, "*.*")):
            myzip.write(f, os.path.join(bibtex_key, os.path.basename(f)))
    myzip.close()


    pylons.tmpl_context._pop_object() 

if __name__ == "__main__":
    main(sys.argv)
