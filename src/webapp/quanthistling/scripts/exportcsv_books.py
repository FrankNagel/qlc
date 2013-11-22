# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import codecs
import collections
import zipfile
import glob
import time

import logging

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
#from pylons import tmpl_context as c

from paste.deploy import appconfig

import quanthistling.dictdata.books

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
    #corpusversion = model.meta.Session.query(model.Corpusversion).order_by(model.Corpusversion.updated).first()
    iso_time = time.strftime("%Y-%m-%d", time.gmtime())
    
    books = dict()

    metadata_file = codecs.open(os.path.join(config['pylons.paths']['static_files'], 'downloads', "csv", "sources.csv"), "w", "utf-8")
    metadata_file.write("QLCID\tTYPE\tLANGUAGES\tIS_READY\tTITLE\tCOMPONENT\n")

    for b in quanthistling.dictdata.books.list + quanthistling.dictdata.toolboxfiles.list:
        #if b['bibtex_key'] != "thiesen1998":
        #    continue

        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        
        if book:

            print "Exporting CSV data for %s..." % b['bibtex_key']

            # collect book data
            languages = [ l.language_iso.langcode for dictdata in book.dictdata for l in dictdata.src_languages + dictdata.tgt_languages if l.language_iso]
            components = [ dictdata.component.name for dictdata in book.dictdata ]
            metadata_file.write(u"{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(book.bibtex_key, "dictionary", ",".join(languages), book.is_ready, book.bookinfo(), ",".join(components)))

            for dictdata in book.dictdata:

                print "  header..."

                data_file = codecs.open(os.path.join(
                    config['pylons.paths']['static_files'], 'downloads', "csv", "{0}-{1}-{2}.csv".format(
                        book.bibtex_key, dictdata.startpage, dictdata.endpage)), "w", "utf-8")

                data_file.write(u"@date: {0}\n".format(iso_time))
                data_file.write(u"@url: http://www.quanthistling.info/data/source/{0}/dictionary-{1}-{2}.html\n".format(book.bibtex_key, dictdata.startpage, dictdata.endpage))
                data_file.write(u"@source_title: {0}\n".format(book.title))
                data_file.write(u"@source_author: {0}\n".format(book.author))
                data_file.write(u"@source_year: {0}\n\n".format(book.year))

                doculect1 = None
                doculect2 = None
                doculects = []
                iso_src = []
                iso_tgt = []
                #data_file.write(u"#\tDOCULECT\tAPPROX_ISO639-3\n")

                # ISO and doculect stuff
                for l in dictdata.src_languages:
                    iso = "n/a"
                    if l.language_iso:
                        iso = l.language_iso.langcode
                    doculects.append(u"\"{0}, {1}, {2}, {3}\"".format(l.language_bookname.name, iso, l.language_bookname.name.encode('ascii','ignore'), dictdata.component.name))
                    doculect1 = l.language_bookname.name
                    #data_file.write(u"@head_iso: {0}\n".format(iso))
                    iso_src.append(u"\"{0}\"".format(iso))
                for l in dictdata.tgt_languages:
                    iso = "n/a"
                    if l.language_iso:
                        iso = l.language_iso.langcode
                    doculects.append(u"\"{0}, {1}, {2}, {3}\"".format(l.language_bookname.name, iso, l.language_bookname.name.encode('ascii','ignore'), dictdata.component.name))
                    doculect2 = l.language_bookname.name
                    iso_tgt.append(u"\"{0}\"".format(iso))

                data_file.write(u"<json>\n{\n    \"doculect\": [\n")
                doculect_str = ",\n        ".join(doculects)
                data_file.write(u"        {0}\n".format(doculect_str))
                data_file.write(u"    ]\n}\n</json>\n\n")

                data_file.write(u"<json>\n{\n    \"head_iso\": [\n")
                iso_str = ",\n        ".join(iso_src)
                data_file.write(u"        {0}\n".format(iso_str))
                data_file.write(u"    ]\n}\n</json>\n\n")

                data_file.write(u"<json>\n{\n    \"translation_iso\": [\n")
                iso_str = ",\n        ".join(iso_tgt)
                data_file.write(u"        {0}\n".format(iso_str))
                data_file.write(u"    ]\n}\n</json>\n\n")

                print "  data..."
                data_file.write(u"QLCID\tHEAD\tHEAD_DOCULECT\tTRANSLATION\tTRANSLATION_DOCULECT\tPOS\n")

                #c.url_for = url_for
                #c.base_url = "http://www.quanthistling.info/data"
                #c.relative_url = url_for(controller='book', action='dictdata', bibtexkey=c.book.bibtex_key, startpage=c.dictdata.startpage, endpage=c.dictdata.endpage, format='html')

                #c.heading = c.book.bookinfo()
                #c.basename = "dict-%s-%i-%i" % (b['bibtex_key'], c.dictdata.startpage, c.dictdata.endpage)
                entries = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==dictdata.id).order_by("startpage", "pos_on_page").all()

                annotations = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==dictdata.id).all()
                dict_annotations = collections.defaultdict(list)
                for a in annotations:
                    dict_annotations[a.entry_id].append(a)

                for e in entries:
                    heads = []
                    translations = []
                    pos = []
                    doculects_heads = []
                    doculects_translations = []
                    entry_id = "{0}/{1}/{2}".format(book.bibtex_key, e.startpage, e.pos_on_page)
                    for a in dict_annotations[e.id]:
                        if a.value == "head":
                            heads.append(a.string)
                            doculect = ""
                            for a2 in dict_annotations[e.id]:
                                if a2.value == "doculect" and a2.start == a.start:
                                    doculect = a2.string
                            if doculect == "":
                                doculect = doculect1
                            doculects_heads.append(doculect)


                        elif a.value == "translation":
                            translations.append(a.string)
                            doculect = ""
                            for a2 in dict_annotations[e.id]:
                                if a2.value == "doculect" and a2.start == a.start:
                                    doculect = a2.string
                            if doculect == "":
                                doculect = doculect2
                            doculects_translations.append(doculect)


                        elif a.value == "pos":
                            pos.append(a.string)

                    for i, head in enumerate(heads):
                        for j, translation in enumerate(translations):
                            data_file.write(u"{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
                                entry_id, head, doculects_heads[i], translation, doculects_translations[j], "|".join(pos)
                            ))


                data_file.close()

                #c.count_heads = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"head").count()
                #c.count_translations = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"translation").count()
                #c.count_pos = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"pos").count()
                #c.count_examples_src = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"example-src").count()
                #c.count_examples_tgt = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Annotation.value==u"example-tgt").count()
                #c.count_manually_corrected = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).filter(model.Entry.has_manual_annotations==True).count()


    metadata_file.close()

    #print "Zipping..."
    #myzip = zipfile.ZipFile(os.path.join(config['pylons.paths']['static_files'], 'downloads', "csv", 'data.zip'), 'w', zipfile.ZIP_DEFLATED)
    #for file in glob.glob(os.path.join(config['pylons.paths']['static_files'], 'downloads', "csv", "*.csv")):
    #    myzip.write(file, os.path.basename(file))
    #myzip.close()

if __name__ == "__main__":
    main(sys.argv)
