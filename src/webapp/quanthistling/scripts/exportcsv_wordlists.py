# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import codecs
import collections
import zipfile
import glob

import logging

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
#from pylons import tmpl_context as c

from paste.deploy import appconfig

import quanthistling.dictdata.wordlistbooks

def main(argv):
    log = logging.getLogger()
    logging.basicConfig(level=logging.INFO)
    
    conf = appconfig('config:development.ini', relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    #metadata.create_all(bind=Session.bind)

    #c.corpushistory = model.meta.Session.query(model.Corpusversion).all()
    corpusversion = model.meta.Session.query(model.Corpusversion).order_by(model.Corpusversion.updated).first()
    iso_time = corpusversion.updated.strftime("%Y-%m-%d")
    
    books = dict()

    metadata_file = codecs.open(os.path.join(config['pylons.paths']['static_files'], 'downloads', "csv", "sources.csv"), "a", "utf-8")
    #metadata_file.write("ID\tTYPE\tLANGUAGES\tIS_READY\tTITLE\n")

    for b in quanthistling.dictdata.wordlistbooks.list:
        #if b['bibtex_key'] != "thiesen1998":
        #    continue

        if b['bibtex_key'] == u"kraft1981-1":
            b["bibtex_key"] = u"kraft1981"

        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        
        if book:

            print "Exporting CSV data for %s..." % b['bibtex_key']

            # collect book data
            languages = [ wordlistdata.language_iso.langcode for wordlistdata in book.wordlistdata if wordlistdata.language_iso]
            components = [ wordlistdata.component.name for wordlistdata in book.wordlistdata if wordlistdata.component ]
            metadata_file.write(u"{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(book.bibtex_key, "wordlist", ",".join(languages), book.is_ready, book.bookinfo(), ",".join(components)))

            data_file = codecs.open(os.path.join(
                config['pylons.paths']['static_files'], 'downloads', "csv", "{0}.csv".format(
                    book.bibtex_key)), "w", "utf-8")

            print "  header..."

            data_file.write(u"@date: {0}\n".format(iso_time))
            data_file.write(u"@url: http://www.quanthistling.info/data/source/{0}/wordlist.html\n".format(book.bibtex_key))
            data_file.write(u"@source_title: {0}\n".format(book.title))
            data_file.write(u"@source_author: {0}\n".format(book.author))
            data_file.write(u"@source_year: {0}\n".format(book.year))

            for wordlistdata in book.wordlistdata:
                iso = "n/a"
                if wordlistdata.language_iso:
                    iso = wordlistdata.language_iso.langcode
                if wordlistdata.component:
                    data_file.write(u"@doculect: {0}, {1}, {2}, {3}\n".format(wordlistdata.language_bookname.name, iso, wordlistdata.language_bookname.name.encode('ascii','ignore'), wordlistdata.component.name))
                else:
                    data_file.write(u"@doculect: {0}, {1}, {2}\n".format(wordlistdata.language_bookname.name, iso, wordlistdata.language_bookname.name.encode('ascii','ignore')))

            print "  data..."

            data_file.write(u"QLCID\tCONCEPT\tCOUNTERPART\tCOUNTERPART_DOCULECT\n")

            for wordlistdata in book.wordlistdata:


                doculect1 = wordlistdata.language_bookname.name

                entries = model.meta.Session.query(model.WordlistEntry).filter(model.WordlistEntry.wordlistdata_id==wordlistdata.id).all()

                annotations = model.meta.Session.query(model.WordlistAnnotation).join(model.WordlistEntry, model.WordlistAnnotation.entry_id==model.WordlistEntry.id).filter(model.WordlistEntry.wordlistdata_id==wordlistdata.id).all()
                dict_annotations = collections.defaultdict(list)
                for a in annotations:
                    dict_annotations[a.entry_id].append(a)

                for e in entries:
                    counterparts = []
                    doculects_counterparts = []
                    entry_id = u"{0}/{1}/{2}".format(book.bibtex_key, wordlistdata.language_bookname.name, e.concept.concept)
                    for a in dict_annotations[e.id]:
                        if a.value == "counterpart":
                            counterparts.append(a.string)
                            doculect = ""
                            for a2 in dict_annotations[e.id]:
                                if a2.value == "doculect" and a2.start == a.start:
                                    doculect = a2.string
                            if doculect == "":
                                doculect = doculect1
                            doculects_counterparts.append(doculect)

                    for i, counterpart in enumerate(counterparts):
                        data_file.write(u"{0}\t{1}\t{2}\t{3}\n".format(
                            entry_id, e.concept.concept, counterpart, doculects_counterparts[i]
                        ))


            data_file.close()

            #c.count_heads = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"head").count()
            #c.count_translations = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"translation").count()
            #c.count_pos = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"pos").count()
            #c.count_examples_src = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"example-src").count()
            #c.count_examples_tgt = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"example-tgt").count()
            #c.count_manually_corrected = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Entry.has_manual_annotations==True).count()


    metadata_file.close()

    print "Zipping..."

    myzip = zipfile.ZipFile(os.path.join(config['pylons.paths']['static_files'], 'downloads', "csv", 'data.zip'), 'w', zipfile.ZIP_DEFLATED)
    for file in glob.glob(os.path.join(config['pylons.paths']['static_files'], 'downloads', "csv", "*.csv")):
        myzip.write(file, os.path.basename(file))
    myzip.close()

if __name__ == "__main__":
    main(sys.argv)
