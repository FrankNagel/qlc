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

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    tabs_in_head = functions.get_list_ranges_for_annotation(entry, "tab", start=0, end=head_end-2)

    if tabs_in_head:
        start = 0
        for t in tabs_in_head:
            end = t[0]
            head = functions.insert_head(entry, start, end)
            heads.append(head)
            start = t[1]
        head = functions.insert_head(entry, start, head_end)
        if head:
            heads.append(head)
        else:
            functions.print_error_in_entry(entry, "tab in wrong position")
    else:
        head = functions.insert_head(entry, 0, head_end)
        heads.append(head)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    translation_start = head_end
    italic = functions.get_first_italic_in_range(entry, head_end, len(entry.fullentry))
    if italic != -1 and italic[0] <= (head_end+1):
        translation_start = italic[1]

    bold = functions.get_first_bold_in_range(entry, translation_start, len(entry.fullentry))
    if bold != -1 and bold[0] <= (translation_start+1):
        translation_end = bold[1]

        if re.search("\d ", entry.fullentry[translation_start:translation_end]):
            for match in re.finditer(r"(?<=\d )(.*?)(?:\d |$)", entry.fullentry[translation_start:translation_end]):
                functions.insert_translation(entry, translation_start+match.start(1), translation_start+match.end(1))
        else:
            functions.insert_translation(entry, translation_start, translation_end)

        translation_start = translation_end

    translation_end = len(entry.fullentry)

    match_bracket = re.search(u" ?\([^\)]*\) ?$", entry.fullentry[translation_start:translation_end])
    if match_bracket:
        translation_end = translation_start + match_bracket.start(0)

    if translation_start < translation_end - 1:
        for s, e in functions.split_entry_at(entry, r"(?:, |$)", translation_start, translation_end):
            functions.insert_translation(entry, s, e)

 
def main(argv):

    bibtex_key = u"griffiths2002"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=5,pos_on_page=11).all()

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
