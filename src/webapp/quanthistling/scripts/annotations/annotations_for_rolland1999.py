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

    bold = functions.get_list_bold_ranges(entry)
    if not bold:
        functions.print_error_in_entry(entry, "Found no bold part at the beginning.")
        return heads
    head_end = bold[0][1]

    for (s, e) in functions.split_entry_at(entry, r"(?:, |$)", 0, head_end):
        s,e, head = functions.remove_parts(entry, s,e)
        while head and (head[-1].isdigit() or head[-1] == '!'):
            head = head[:-1]
        head = functions.insert_head(entry, s, e, head)
        if head is None:
            functions.print_error_in_entry(entry, "head is None")
        else:
            heads.append(head)

    return heads

def annotate_pos(entry):
    # delete translation annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    italic = functions.get_first_italic_in_range(entry, head_end, head_end+10)
    if italic != -1 and entry.fullentry[italic[0]:italic[1]].strip() != "Vea":
        entry.append_annotation(italic[0], italic[1], u'pos', u'dictinterpretation')
    
def _insert_translation_1(entry, start, end):
    translation_end = functions.find_first_point(entry, start, end)

    tr = entry.fullentry[start:translation_end].strip()
    if tr.startswith("Vea") or tr.startswith("plural"):
        return

    for (s, e) in functions.split_entry_at(entry, ur"! ¡|[,;] |$", start, translation_end):
        s, e, translation = functions.remove_parts(entry, s, e)
        translation = translation.translate(dict((ord(c), None) for c in u'!?¿¡'))
        functions.insert_translation(entry, s, e, translation)

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = max(functions.get_pos_or_head_end(entry),
                            functions.get_last_bold_pos_at_start(entry))
    
    match_period = re.match(" ?\.", entry.fullentry[translation_start:])
    if match_period:
        translation_start += len(match_period.group(0))

    for num_start, num_end in functions.split_entry_at(entry, r'\d\. |$', translation_start,
                                                       len(entry.fullentry), True):
        _insert_translation_1(entry, num_start, num_end)
        
 
def main(argv):

    bibtex_key = u"rolland1999"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=101,pos_on_page=23).all()

        startletters = set()
    
        for e in entries:
            #skip subentries which start with '||'
            if e.is_subentry and (e.fullentry.startswith('||') or e.fullentry.startswith(' ||')):
                for a in e.annotations:
                    if a.annotationtype.type == 'dictinterpretation':
                        Session.delete(a)
                continue
            
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
