# -*- coding: utf8 -*-

import sys, os, re
import collections
import codecs

sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.wordlistbooks

from paste.deploy import appconfig

import importfunctions
import annotations.functions

dictdata_path = 'quanthistling/dictdata'

re_page = re.compile(u"\[Seite (\d+)\]$")
map_tabs = {
    u"Portuguese": 0,
    u"English": 1,
    u"Mamaindé": 2,
    u"Latundé": 3,
    u"Negaroté": 4,
}

def insert_counterpart(entry, start, end, data):
    if entry.fullentry.strip() == "":
        return

    entry.append_annotation(start, end, "counterpart", "dictinterpretation",
        entry.fullentry)
    entry.append_annotation(start, end, u'doculect',
        u'dictinterpretation', data["language_bookname"])
    language_iso = Session.query(model.LanguageIso).filter_by(
        name=data["language_name"]).first()
    if language_iso is not None:
        entry.append_annotation(start, end, u'iso639-3',
            u'dictinterpretation', language_iso.langcode)

def main(argv):
    book_bibtex_key = 'eberhard2005'
    
    if len(argv) < 2:
        print "call: importeberhard2005.py ini_file"
        exit(1)
    
    ini_file = argv[1]
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)


    for b in quanthistling.dictdata.wordlistbooks.list:
        if b['bibtex_key'] == book_bibtex_key:
            wordlistbookdata = b

    importfunctions.delete_book_from_db(Session, book_bibtex_key)    
    book = importfunctions.insert_book_to_db(Session, wordlistbookdata)

    concepts = {}

    print "Parsing {0}...".format(book_bibtex_key)

    for data in wordlistbookdata["nonwordlistdata"]:
        nonwordlistdata = importfunctions.insert_nonwordlistdata_to_db(
            Session, data, book, os.path.join(dictdata_path, data['file']))

    for data in wordlistbookdata["wordlistdata"]:

        wordlistdata = importfunctions.insert_wordlistdata_to_db(
            Session, data, book)

        wordlistfile = codecs.open(os.path.join(
            dictdata_path, wordlistbookdata["file"]), "r", "utf-8")

        page = 0
        pos_on_page = 1
        counterparts = {}
                
        for line in wordlistfile:
            l = line.strip()

            if re.search(u'^<p>', l):
                l = re.sub(u'</?p>', '', l)

                if re_page.match(l):
                    match_page = re_page.match(l)
                    page = int(match_page.group(1))
                    pos_on_page = 1
                    print "Parsing page {0}".format(page)

                match_number = re.match("(\d{1,3})\. ?", l)
                if match_number:
                    concept_nr = int(match_number.group(1))
                    l = l[len(match_number.group(0)):]
                    parts = l.split("\t")
                    parts_index = map_tabs[data["language_bookname"]]
                    if parts_index < len(parts):
                        c = parts[parts_index]
                        counterparts[concept_nr] = \
                            (c, page, parts_index + 1,
                                pos_on_page + parts_index)
                    pos_on_page += len(parts)

        # store concepts
        if data["language_name"] == u"Portuguese":
            for k, v in counterparts.items():
                concept = v[0].upper()
                concept = re.sub(u" ", u"_", concept)
                concept = re.sub(u"'", u"_", concept)
                concept = re.sub(u"/", u"_", concept)
                concept = re.sub(u"\(", u"", concept)
                concept = re.sub(u"\)", u"", concept)
                concept = re.sub(u"\?", u"", concept)
                concept_id = u"{0}".format(concept)
                concepts[k] = concept_id

                # add concept to db if it is not there
                concept_db =  model.meta.Session.query(
                    model.WordlistConcept).filter_by(
                    concept=concept_id).first()
                if concept_db == None:
                    concept_db = model.WordlistConcept()
                    concept_db.concept = concept_id
                    Session.add(concept_db)
            Session.commit()
            
        # store entries
        for k, v in counterparts.items():
            entry_db = importfunctions.process_line(v[0], "wordlist")
            entry_db.wordlistdata = wordlistdata
            entry_db.pos_on_page = v[3]
            entry_db.startpage = v[1]
            entry_db.endpage = v[1]
            entry_db.startcolumn = v[2]
            entry_db.endcolumn = v[2]
            
            concept_id = concepts[k]
            concept_db =  model.meta.Session.query(
                model.WordlistConcept).filter_by(concept=concept_id).first()
            if concept_db is None:
                print("Concept not found: {0}".format(concept_id))
            entry_db.concept = concept_db

            inserted = insert_counterpart(entry_db, 0, len(c), data)

    Session.commit()
    Session.close()


if __name__ == "__main__":
    main(sys.argv)
