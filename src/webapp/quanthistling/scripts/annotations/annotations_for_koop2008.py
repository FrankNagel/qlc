# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter
import difflib

# Pylons model init sequence
import pylons.test
import logging

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.books

from paste.deploy import appconfig

import functions

def _insert_head(entry, start, end):
    str_head = entry.fullentry[start:end]
    if str_head.startswith(" "):
        start += 1
    if str_head.endswith(" "):
        end -= 1

    str_head = entry.fullentry[start:end]
    if str_head.startswith("-"):
        entry.append_annotation(start, start+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
        start += 1
    if str_head.endswith("-"):
        entry.append_annotation(end-1, end, u'boundary', u'dictinterpretation', u"morpheme boundary")
        end -= 1

    str_head = entry.fullentry[start:end]
    str_head = re.sub("[_#\*\(\)]", "", str_head)

    return functions.insert_head(entry, start, end, str_head)


def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    
    head = _insert_head(entry, 0, head_end)
    heads.append(head)

    return heads


def _insert_translation_1(entry, start, end):
    match_bracket = re.match(r" ?\([^)]*\) ?", entry.fullentry[start:end])
    if match_bracket:
        start += match_bracket.end(0)

    match = re.search(r"[\.!\?] \([^)]*\)$", entry.fullentry[start:end])
    if match:
        end -= len(match.group(0))
    for (s, e) in functions.split_entry_at(entry, r"(?:[,;?!] |$)", start, end):
        functions.insert_translation(entry, s, e)

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_head_end(entry)

    if re.search("\d ", entry.fullentry[translation_start:]):
        for match in re.finditer(r"(?<=\d )(.*?)(?:\d |$)", entry.fullentry[translation_start:]):
            _insert_translation_1(entry, translation_start+match.start(1), translation_start+match.end(1))
    else:
        _insert_translation_1(entry, translation_start, len(entry.fullentry))
 
def main(argv):

    bibtex_key = u"koop2008"
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=45,pos_on_page=31).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
