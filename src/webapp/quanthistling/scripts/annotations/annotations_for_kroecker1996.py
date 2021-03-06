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

superscripts = u'\u2070\u2071\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079'
superscripts_tp = dict((ord(str(i)), superscripts[i]) for i in xrange(len(superscripts)))

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_all = entry.fullentry[:head_end]
    head_all = head_all.rstrip()

    #ignoring hyphens, if any
    head_all = head_all.replace('-', '')
    head_all = head_all.translate(superscripts_tp)
    
    head = functions.insert_head(entry, 0, head_end, head_all)        
    heads.append(head)

    return False, heads


def annotate_pos(entry):
    # delete translation annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    italic = functions.get_first_italic_in_range(entry, 0, len(entry.fullentry))
    if italic != -1:
        entry.append_annotation(italic[0], italic[1], u'pos', u'dictinterpretation')
    else:
        functions.print_error_in_entry(entry, "Could not find italic for POS")

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_pos_or_head_end(entry)
    translation_end = entry.fullentry.find('.', translation_start)

    if translation_end == -1:
        translation_end = len(entry.fullentry)

    for t_start, t_end in functions.split_entry_at(entry, r',|;|$', translation_start, translation_end):
        functions.insert_translation(entry, t_start, t_end)
 
def main(argv):

    bibtex_key = u"kroeker1996"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=10,pos_on_page=1).all()

        startletters = set()
    
        for e in entries:
            is_dialect, heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            if not is_dialect:
                annotate_pos(e)
                annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
