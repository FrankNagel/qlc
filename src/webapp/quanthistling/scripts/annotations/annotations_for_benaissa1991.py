# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter
import difflib

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions

def annotate_head(entry):
    # delete head annotations
    annotations = [a for a in entry.annotations if a.value == 'head'
                   or a.value == 'doculect' or a.value == 'iso-639-3']
    for a in annotations:
        Session.delete(a)

    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)

    head = functions.insert_head(entry, 0, head_end)
    heads.append(head)

    return heads


def annotate_pos(entry):
    # delete pos annotations
    pos = [a for a in entry.annotations if a.value == 'pos']
    for p in pos:
        Session.delete(p)

    italic = functions.get_first_italic_range(entry)

    if italic != -1:
        entry.append_annotation(italic[0], italic[1], u'pos',
                                u'dictinterpretation')
    else:
        functions.print_error_in_entry(entry, 'No POS detected.')


def annotate_translation(entry):
    # delete translations
    trans = [a for a in entry.annotations if a.value == 'translation']
    for t in trans:
        Session.delete(t)

    trans_start = functions.get_pos_or_head_end(entry)

    if re.search(r'\d\. ', entry.fullentry[trans_start:]):
        for match in re.finditer(r"(?<=\d\. )(.*?)(?:\d\. |$)",
                                 entry.fullentry[trans_start:]):

            start = trans_start + match.start(1)
            end = trans_start + match.end(1)
            process_translation(entry, start, end)
    else:
        process_translation(entry, trans_start, len(entry.fullentry))


def process_translation(entry, start, end):

    trans_ended = False
    s1 = start
    period = -1
    while not trans_ended:
        period = entry.fullentry.find('.', s1)
        if period != -1:
            for bracket in re.finditer(r'\(.*\)', entry.fullentry[s1:]):
                if bracket.start(0) <= period <= bracket.end(0):
                    trans_ended = False
                else:
                    trans_ended = True
            else:
                trans_ended = True

            s1 = start + period
        else:
            trans_ended = True

    s = start
    if period != -1:
        trans_end = period
    else:
        trans_end = end
    for match in re.finditer(r"(?:[,] |$)", entry.fullentry[s:trans_end]):
        e = start + match.start(0)
        functions.insert_translation(entry, s, e)
        s = start + match.end(0)

def main(argv):
    bibtex_key = u'benaissa1991'
    
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
        (model.Book, model.Dictdata.book_id == model.Book.id)
        ).filter(model.Book.bibtex_key == bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=1).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=3,pos_on_page=1).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=3,pos_on_page=4).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=3,pos_on_page=6).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=3,pos_on_page=41).all())

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translation(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)