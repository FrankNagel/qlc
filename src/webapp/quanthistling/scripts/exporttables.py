#-*- coding: utf8 -*-

# import Python system modules to write files
import sys, os, glob
import re
import codecs

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
        print "call: export_tables.py ini_file"
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
    for b in quanthistling.dictdata.books.list + quanthistling.dictdata.toolboxfiles.list \
            + quanthistling.dictdata.wordlistbooks.list:
        if bibtex_key_param != None and bibtex_key_param != b['bibtex_key']:
            continue
        
        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()

        if book:

            book_dir = os.path.join(
                config['pylons.paths']['static_files'], 'downloads', "datapackages", book.bibtex_key)
            if not os.path.exists(book_dir):
                os.makedirs(book_dir)

            annotations_dir = os.path.join(book_dir, "annotations")
            if not os.path.exists(annotations_dir):
                os.makedirs(annotations_dir)

            print "Exporting entries for %s..." % b['bibtex_key']

            entry_file = codecs.open(os.path.join(book_dir, "entries.csv"), "w", "utf-8")
            entry_file.write("ENTRY_ID\tENTRY\n")
            annotations_formatting_file = codecs.open(os.path.join(annotations_dir, "formatting.csv"), "w", "utf-8")
            annotations_formatting_file.write("ENTRY_ID\tSTART\tEND\tVALUE\tANNOTATION\n")
            annotations_pagelayout_file = codecs.open(os.path.join(annotations_dir, "pagelayout.csv"), "w", "utf-8")
            annotations_pagelayout_file.write("ENTRY_ID\tSTART\tEND\tVALUE\tANNOTATION\n")
            annotations_dictinterpretation_file = codecs.open(os.path.join(annotations_dir, "dictinterpretation.csv"), "w", "utf-8")
            annotations_dictinterpretation_file.write("ENTRY_ID\tSTART\tEND\tVALUE\tANNOTATION\n")

            if book.type == "wordlist":
                entries = model.meta.Session.query(model.Entry).filter(model.WordlistEntry.book_id==book.id).order_by("startpage", "pos_on_page").all()
            else:
                entries = model.meta.Session.query(model.Entry).filter(model.Entry.book_id==book.id).order_by("startpage", "pos_on_page").all()
            for e in entries:
                if book.type == "wordlist":
                    entry_id = u"{0}/{1}/{2}".format(book.bibtex_key, wordlistdata.language_bookname.name, e.concept.concept)
                else:
                    entry_id = "{0}/{1}/{2}".format(book.bibtex_key, e.startpage, e.pos_on_page)

                entry_file.write(u"{0}\t{1}\n".format(entry_id, e.fullentry))

                for a in e.annotations:
                    t = a.annotationtype.type
                    line = u"{0}\t{1}\t{2}\t{3}\t{4}\n".format(entry_id, a.start, a.end, a.value, a.string)
                    if t == 'formatting':
                        annotations_formatting_file.write(line)
                    elif t == 'dictinterpretation':
                        annotations_dictinterpretation_file.write(line)
                    elif t == 'pagelayout':
                        annotations_pagelayout_file.write(line)

            entry_file.close()
            annotations_formatting_file.close()
            annotations_dictinterpretation_file.close()
            annotations_pagelayout_file.close()

if __name__ == "__main__":
    main(sys.argv)