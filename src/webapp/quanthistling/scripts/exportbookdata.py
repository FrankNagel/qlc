# -*- coding: utf8 -*-

# import Python system modules to write files
import sys, os, glob
import re
import tempfile
import shutil

import socket
socket.setdefaulttimeout(1000000)

from zipfile import ZipFile

# add path to script
sys.path.append(os.path.abspath('.'))

# import pylons and web application modules
import pylons.test
from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig

import quanthistling.dictdata.books
import quanthistling.dictdata.wordlistbooks
import quanthistling.dictdata.toolboxfiles

from routes import url_for

def main(argv):

    if len(argv) < 2:
        print "call: exportbookdata.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    bibtex_key_param = None
    if len(argv) >= 3:
        bibtex_key_param = argv[2]

    # load web application config
    conf = appconfig('config:' + ini_file, relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)

    # Create database session
    metadata.create_all(bind=Session.bind)
    

    #for b in []:
    for b in quanthistling.dictdata.books.list + quanthistling.dictdata.toolboxfiles.list:
        if bibtex_key_param != None and bibtex_key_param != b['bibtex_key']:
            continue
        
        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        
        if book:
            # create tmp-directory for files
            temppath = tempfile.mkdtemp()
            
            print "Exporting data for %s..." % b['bibtex_key']
            for dictdata in book.dictdata:

                # database queries for heads
                heads = model.meta.Session.query(model.Annotation).join(
                        (model.Entry, model.Annotation.entry_id==model.Entry.id),
                        (model.Dictdata, model.Entry.dictdata_id==model.Dictdata.id)
                    ).filter(model.Dictdata.id==dictdata.id).filter(model.Annotation.value==u"head").all()
                
                # write heads to file
                if len(heads) > 0:
                    file_heads = open(os.path.join(temppath, "heads_%s_%s_%s.txt" % ( b['bibtex_key'], dictdata.startpage, dictdata.endpage ) ), "w")
                    for i in range(0,len(heads)):
                        head = heads[i].string
                        if heads[i].entry.is_subentry:
                            mainentry = heads[i].entry.mainentry()
                            if mainentry:
                                url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=mainentry.startpage, pos_on_page=mainentry.pos_on_page, format='html')
                            else:
                                print "nio main entry found for sub entry on page %i pos on page %i." % (heads[i].entry.startpage, heads[i].entry.pos_on_page)
                        else:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=heads[i].entry.startpage, pos_on_page=heads[i].entry.pos_on_page, format='html')
                        file_heads.write(head.strip().encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")
                    file_heads.close()

                # database queries for examples
                examples_src = model.meta.Session.query(model.Annotation).join(
                        (model.Entry, model.Annotation.entry_id==model.Entry.id),
                        (model.Dictdata, model.Entry.dictdata_id==model.Dictdata.id)
                    ).filter(model.Dictdata.id==dictdata.id).filter(model.Annotation.value==u"example-src").all()
                examples_tgt = model.meta.Session.query(model.Annotation).join(
                        (model.Entry, model.Annotation.entry_id==model.Entry.id),
                        (model.Dictdata, model.Entry.dictdata_id==model.Dictdata.id)
                    ).filter(model.Dictdata.id==dictdata.id).filter(model.Annotation.value==u"example-tgt").all()
                
                # print error if mismatch
                if len(examples_src) != len(examples_tgt):
                    print "example translation count error"
                    print "  src examples: %i" % len(examples_src)
                    print "  tgt examples: %i" % len(examples_tgt)
                    #sys.exit(1)
                
                # write examples to two files
                if len(examples_src) > 0:
                    file_src = open(os.path.join(temppath, "examples-src_%s_%s_%s.txt" % ( b['bibtex_key'], dictdata.startpage, dictdata.endpage )), "w")
                    file_tgt = open(os.path.join(temppath, "examples-tgt_%s_%s_%s.txt" % ( b['bibtex_key'], dictdata.startpage, dictdata.endpage )), "w")
                    for i in range(0,len(examples_src)):
                        if len(examples_tgt) > i:
                            break

                        src = examples_src[i].string.strip()
                        tgt = examples_tgt[i].string.strip()
                        if examples_src[i].entry.is_subentry:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=examples_src[i].entry.mainentry().startpage, pos_on_page=examples_src[i].entry.mainentry().pos_on_page, format='html')
                        else:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=examples_src[i].entry.startpage, pos_on_page=examples_src[i].entry.pos_on_page, format='html')
                        #print tgt.encode('utf-8')
                        if (len(src) > 0 and len(tgt) > 0):
                            file_src.write(src.encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")
                            file_tgt.write(tgt.encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")
                    file_src.close()
                    file_tgt.close()

                # database queries for pos
                pos = model.meta.Session.query(model.Annotation).join(
                        (model.Entry, model.Annotation.entry_id==model.Entry.id),
                        (model.Dictdata, model.Entry.dictdata_id==model.Dictdata.id)
                    ).filter(model.Dictdata.id==dictdata.id).filter(model.Annotation.value==u"pos").all()
                
                # write heads to file
                if len(pos) > 0:
                    file_heads = open(os.path.join(temppath, "pos_%s_%s_%s.txt" % ( b['bibtex_key'], dictdata.startpage, dictdata.endpage )), "w")
                    for i in range(0,len(pos)):
                        p = pos[i].string
                        if pos[i].entry.is_subentry:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=pos[i].entry.mainentry().startpage, pos_on_page=pos[i].entry.mainentry().pos_on_page, format='html')
                        else:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=pos[i].entry.startpage, pos_on_page=pos[i].entry.pos_on_page, format='html')
                        file_heads.write(p.strip().encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")
                    file_heads.close()

                # database queries for translations
                translations = model.meta.Session.query(model.Annotation).join(
                        (model.Entry, model.Annotation.entry_id==model.Entry.id),
                        (model.Dictdata, model.Entry.dictdata_id==model.Dictdata.id)
                    ).filter(model.Dictdata.id==dictdata.id).filter(model.Annotation.value==u"translation").all()
                
                # write translations to file
                if len(translations) > 0:
                    file_translations = open(os.path.join(temppath, "translations_%s_%s_%s.txt" % ( b['bibtex_key'], dictdata.startpage, dictdata.endpage )), "w")
                    for i in range(0,len(translations)):
                        t = translations[i].string
                        if translations[i].entry.is_subentry:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=translations[i].entry.mainentry().startpage, pos_on_page=translations[i].entry.mainentry().pos_on_page, format='html')
                        else:
                            url = url_for(controller='book', action='entryid', bibtexkey=b['bibtex_key'], pagenr=translations[i].entry.startpage, pos_on_page=translations[i].entry.pos_on_page, format='html')
                        file_translations.write(t.strip().encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")
                    file_translations.close()

            # create archive
            myzip = ZipFile(os.path.join(config['pylons.paths']['static_files'], 'downloads', '%s.zip' % b['bibtex_key']), 'w')
            for file in glob.glob(os.path.join(temppath, "*.txt")):
                myzip.write(file, os.path.basename(file))
            myzip.close()
        
            shutil.rmtree(temppath)

    #for b in []:
    for b in quanthistling.dictdata.wordlistbooks.list:
        if bibtex_key_param != None and bibtex_key_param != b['bibtex_key']:
            continue
        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        if book:
            # create tmp-directory for files
            temppath = tempfile.mkdtemp()
            
            print "Exporting data for %s..." % b['bibtex_key']
            file_counterparts = open(os.path.join(temppath, "counterparts_%s.txt" % ( b['bibtex_key'] ) ), "w")

            for wordlistdata in book.wordlistdata:
                counterparts = model.meta.Session.query(model.WordlistAnnotation).join(
                        (model.WordlistEntry, model.WordlistAnnotation.entry_id==model.WordlistEntry.id),
                        (model.Wordlistdata, model.WordlistEntry.wordlistdata_id==model.Wordlistdata.id)
                    ).filter(model.Wordlistdata.id==wordlistdata.id).filter(model.WordlistAnnotation.value==u"counterpart").all()
                
                # write heads to file
                if len(counterparts) > 0:
                    for i in range(0,len(counterparts)):
                        counterpart = counterparts[i].string
                        url = url_for(controller='book', action='entryid_wordlist', bibtexkey=b['bibtex_key'], concept=counterparts[i].entry.concept.concept, language_bookname=wordlistdata.language_bookname, format='html')
                        file_counterparts.write(counterpart.strip().encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")

            # create archive
            file_counterparts.close()
            myzip = ZipFile(os.path.join(config['pylons.paths']['static_files'], 'downloads', '%s.zip' % b['bibtex_key']), 'w')
            for file in glob.glob(os.path.join(temppath, "*.txt")):
                myzip.write(file, os.path.basename(file))
            myzip.close()

            shutil.rmtree(temppath)


if __name__ == "__main__":
    main(sys.argv)
