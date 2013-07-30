# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import collections
import codecs
import re

import logging

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
#from pylons import tmpl_context as c

from paste.deploy import appconfig

from nltk.stem.snowball import SpanishStemmer

import quanthistling.dictdata.books

def main(argv):
    log = logging.getLogger()
    logging.basicConfig(level=logging.INFO)
    
    conf = appconfig('config:development.ini', relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)

    stemmer = SpanishStemmer(True)

    # load swadesh list
    swadesh_file = codecs.open(os.path.join(os.path.dirname(
        os.path.realpath(
            __file__)), "swadesh_spa.txt"), "r", "utf-8")

    swadesh_entries = []
    for line in swadesh_file:
        line = line.strip()
        for e in line.split(","):
            stem = stemmer.stem(e)
            swadesh_entries.append(stem)

    for b in quanthistling.dictdata.books.list:
        #if b['bibtex_key'] != "thiesen1998":
        #    continue

        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        
        if book:

            print "Filtering entries in %s..." % b['bibtex_key']

            for dictdata in book.dictdata:

                entries = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==dictdata.id).order_by("startpage", "pos_on_page").all()

                annotations = model.meta.Session.query(model.Annotation).join(model.Entry, model.Annotation.entry_id==model.Entry.id).filter(model.Entry.dictdata_id==dictdata.id).all()
                dict_annotations = collections.defaultdict(list)
                for a in annotations:
                    dict_annotations[a.entry_id].append(a)

                for e in entries:
                    if b['bibtex_key'] == "thiesen1998":
                        e.filtered = False
                    else:
                        e.filtered = True
                        for a in dict_annotations[e.id]:
                            if a.value == "iso-639-3" and a.string == "spa":
                                for a2 in dict_annotations[e.id]:
                                    if (a2.value == "head" or a2.value == "translation") and a2.start == a.start:
                                        phrase = re.sub(" ?\([^)]\)", "", a2.string)
                                        phrase = phrase.strip()
                                        if not " " in phrase:
                                            stem = stemmer.stem(phrase)
                                            if stem in swadesh_entries:
                                                e.filtered = False
#                                                if e.is_subentry:
#                                                    e.mainentry().filtered = False

                Session.commit()





if __name__ == "__main__":
    main(sys.argv)
