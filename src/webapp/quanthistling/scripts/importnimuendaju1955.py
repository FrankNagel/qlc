# -*- coding: utf8 -*-

import sys, os, re
import collections
import codecs
import unicodedata

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

def conceptid_from_string(concept):
    concept = concept.upper()
    concept = re.sub(u"'", u"_", concept)
    concept = re.sub(u" ", u"_", concept)
    concept = re.sub(u"-", u"_", concept)
    concept = re.sub(u"[\(\)/.,!?: ]", u"", concept)
    concept = re.sub(u"_+", u"_", concept)
    return u"{0}".format(concept)


def main(argv):
    book_bibtex_key = 'nimuendaju1955'
    
    if len(argv) < 2:
        print "call: importnimuendaju1955.py ini_file"
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
        part = None

        lang = None
                
        for line in wordlistfile:
            l = line.strip()

            if re.search(u'^<p>', l):
                l = re.sub(u'</?p>', '', l)

                match_part = re.search("^<i>([^\.]+)\.</i>$", l)
                if match_part:
                    part = match_part.group(1)
                    continue

                lang = unicodedata.normalize("NFD", data["language_bookname"])

                if re_page.match(l):
                    match_page = re_page.match(l)
                    page = int(match_page.group(1))
                    pos_on_page = 1
                    if page >= int(data["startpage"]) and \
                            page <= int(data["endpage"]):
                        print "Parsing page {0}".format(page)
        
                else:
                    if page >= int(data["startpage"]) and \
                            page <= int(data["endpage"]):

                        if not part == lang and lang != "Portuguese":
                            continue

                        parts = l.split("\t")
                        if len(parts) != 4 and len(parts) != 2:
                            print("wrong number of tabs on page {0} pos {1}".format(page, pos_on_page))
                            print(l)
                            print(parts)
                            continue

                        for i in range(len(parts) / 2):
                            concept = conceptid_from_string(parts[i*2])
                            if concept == u"":
                                print("No concept")
                                print(l)
                                print(parts)
                                continue
                            parts_index = i*2+1
                            if data["language_name"] == u"Portuguese":
                                parts_index = i*2

                            counterpart = parts[parts_index]

                            counterparts[concept] = \
                                (counterpart, page, parts_index + 1,
                                    pos_on_page + parts_index)
                        pos_on_page += len(parts)

        print("  DONE language {0}.".format(lang.encode("utf-8")))
        # store concepts
        if data["language_name"] == u"Portuguese":
            for concept_id, _ in counterparts.items():
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
        for concept_id, v in counterparts.items():
            entry_db = importfunctions.process_line(v[0], "wordlist")
            entry_db.wordlistdata = wordlistdata
            entry_db.pos_on_page = v[3]
            entry_db.startpage = v[1]
            entry_db.endpage = v[1]
            entry_db.startcolumn = v[2]
            entry_db.endcolumn = v[2]
            
            concept_db =  model.meta.Session.query(
                model.WordlistConcept).filter_by(concept=concept_id).first()
            if concept_db is None:
                print(u"Concept not found: {0}".format(concept_id))

            entry_db.concept = concept_db

            inserted = insert_counterpart(entry_db, 0, len(v[0]), data)

    Session.commit()
    Session.close()


if __name__ == "__main__":
    main(sys.argv)
