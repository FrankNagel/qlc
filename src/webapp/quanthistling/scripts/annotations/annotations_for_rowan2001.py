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
    head_annotations = [a for a in entry.annotations if a.value == 'head' or a.value == "iso-639-3" or a.value == "doculect"]
    for a in head_annotations:
        Session.delete(a)

    heads = []

    newlines = [a for a in entry.annotations if a.value == 'newline']
    newlines = sorted(newlines, key=attrgetter('start'))
    if len(newlines) > 0:
        head_end = functions.get_last_bold_pos_at_start(entry)

        for h_start, h_end in functions.split_entry_at(entry, ',|$', 0, head_end):
            for i in ( index for index in xrange(h_start, h_end) if entry.fullentry[index] == '-' ):
                entry.append_annotation(i, i+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
            h_start, h_end, head = functions.remove_parts(entry, h_start, h_end)
            if not head.strip():
                functions.print_error_in_entry(entry, "head is None")
            else:
                head = head.replace('-', '')
                head = functions.insert_head(entry, h_start, h_end, head)
                heads.append(head)

    return heads

def annotate_pos(entry):
    # delete pos annotations
    trans_annotations = [a for a in entry.annotations if a.value == 'pos']
    for a in trans_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    italic = functions.get_first_italic_in_range(entry, 0, head_end+10)
    if italic != -1:
        start = italic[0]
        end = italic[1]
        bracket = re.search('\(.*\)$', entry.fullentry[start:end])
        if bracket:
            end = start + bracket.regs[0][0]
        entry.append_annotation(start, end, u'pos', u'dictinterpretation')

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if a.value == 'translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_pos_or_head_end(entry)

    if re.search("\d\. ", entry.fullentry[translation_start:]):
        for match in re.finditer(r"(?<=\d\. )(.*?)(?:\d\. |$)",
                                 entry.fullentry[translation_start:]):
            process_translation(entry, translation_start+match.start(1),
                                translation_start+match.end(1))
    else:
        process_translation(entry, translation_start, len(entry.fullentry))

def process_translation(entry, start, end):
    translation_end = entry.fullentry.find('.', start)

    if translation_end == -1:
        translation_end = end

    brackets = re.match(r'[\s]*\(.*\)', entry.fullentry[start:])
    if brackets:
        start += brackets.regs[0][1]

    for (s, e) in functions.split_entry_at(entry, r"(?:[,;] |$)", start, translation_end):
        functions.insert_translation(entry, s, e)

def main(argv):

    bibtex_key = u"rowan2001"
    
    if len(argv) < 2:
        print "call: annotations_for_%s.py ini_file" % bibtex_key
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=4).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=22).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=23).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=24).all())

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
