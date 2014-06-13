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
re_english = re.compile(u"<i>([^<]*)</i>")
re_html = re.compile(u"</?\w{1,2}>")
re_singledash = re.compile(u"(?<!-)-(?!-)")

def substitute_characters(iso, fullentry):
    e = fullentry
    if iso != "eng":
        e = re.sub(u"\?", u"ʔ", e)
    e = re.sub(u"d@go{0}lu{1}".format(unichr(0x0304), unichr(0x0300)),
        u"du{0}{1}go{2}lu{3}".format(unichr(0x0304), unichr(0x0300),
            unichr(0x0304), unichr(0x0300)), e)
    e = re.sub(unichr(0x2013), "-", e)
    e = re.sub(unichr(0x03b7), unichr(0x014b), e)
    e = re.sub(unichr(0x03b9), unichr(0x0269), e)
    e = re.sub(unichr(0x04d9), unichr(0x0259), e)
    e = re.sub(unichr(0x0305), unichr(0x0304), e)
    e = re.sub(unichr(0x02c6), unichr(0x0302), e)
    e = re.sub(unichr(0x02c7), unichr(0x030c), e)
    return e

def insert_counterpart(entry, start, end, data):
    if entry.fullentry.strip() == "":
        return

    for (s, e) in annotations.functions.split_entry_at(entry, r"(?:[/;] ?|$)",
            start, end):
        counterpart = entry.fullentry[s:e]
        if counterpart.strip().startswith("Hausa"):
            continue

        entry.append_annotation(s, e, "counterpart", "dictinterpretation",
            counterpart)
        entry.append_annotation(s, e, u'doculect',
            u'dictinterpretation', data["language_bookname"])
        language_iso = Session.query(model.LanguageIso).filter_by(
            name=data["language_name"]).first()
        if language_iso is not None:
            entry.append_annotation(s, e, u'iso639-3',
                u'dictinterpretation', language_iso.langcode)

def main(argv):
    #book_bibtex_key = u"zgraggen1980"
    bibtex_keys_in_file = [ 'kraft1981-1', 'kraft1981-2', 'kraft1981-3' ]
    combined_bibtex_key = 'kraft1981'
    
    if len(argv) < 2:
        print "call: importkraft1981.py ini_file"
        exit(1)
    
    ini_file = argv[1]
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    for b in quanthistling.dictdata.wordlistbooks.list:
        if b['bibtex_key'] == bibtex_keys_in_file[0]:
            wordlistbookdata = b
            wordlistbookdata['bibtex_key'] = combined_bibtex_key

    importfunctions.delete_book_from_db(Session, combined_bibtex_key)
    importfunctions.delete_book_from_db(Session, bibtex_keys_in_file[0])
    
    book = importfunctions.insert_book_to_db(Session, wordlistbookdata)

    concepts = {}
    for book_bibtex_key in bibtex_keys_in_file:
        print "Parsing {0}...".format(book_bibtex_key)
        
        volume = None
        if book_bibtex_key == "kraft1981-1":
            volume = 1
        elif book_bibtex_key == "kraft1981-2":
            volume = 2
        elif book_bibtex_key == "kraft1981-3":
            volume = 3

        for b in quanthistling.dictdata.wordlistbooks.list:
            if b["bibtex_key"] == book_bibtex_key:
                wordlistbookdata = b
                wordlistbookdata['bibtex_key'] = combined_bibtex_key

        for data in wordlistbookdata["nonwordlistdata"]:
            data["volume"] = volume
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
                l = substitute_characters(data["language_name"], l)

                if re.search(u'^<p>', l):
                    l = re.sub(u'</?p>', '', l)

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
                            parts = l.split("\t")
                            for column, p in enumerate(parts):
                                match_number = re.match("(\d{1,3})\. ?", p)
                                if match_number:
                                    counterparts[int(match_number.group(1))] = \
                                        (p, len(match_number.group(0)), page,
                                            column, pos_on_page)
                                    pos_on_page += 1

            # store concepts
            if data["language_name"] == u"English":
                for k, v in counterparts.items():
                    concept = v[0][v[1]:].upper()
                    if k == 232:
                        concept = "MAT (TABARME)"
                    elif k == 233:
                        concept = "MAT (ZANA)"
                    concept = re.sub(u" ", u"_", concept)
                    concept = re.sub(u"'", u"_", concept)
                    concept = re.sub(u"\(", u"", concept)
                    concept = re.sub(u"\)", u"", concept)
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
                
            entry = {}
            for k, v in counterparts.items():
                entry_db = importfunctions.process_line(v[0], "wordlist")
                entry_db.wordlistdata = wordlistdata
                entry_db.pos_on_page = v[4]
                entry_db.startpage = v[2]
                entry_db.endpage = v[2]
                entry_db.startcolumn = v[3]
                entry_db.endcolumn = v[3]
                entry_db.volume = volume
                
                concept_id = concepts[k]
                concept_db =  model.meta.Session.query(
                    model.WordlistConcept).filter_by(concept=concept_id).first()
                if concept_db is None:
                    print("Concept not found: {0}".format(concept_id))
                entry_db.concept = concept_db

                s = v[1]
                e = len(v[0])
                inserted = insert_counterpart(entry_db, s, e, data)

        Session.commit()

    Session.commit()
    Session.close()


if __name__ == "__main__":
    main(sys.argv)
