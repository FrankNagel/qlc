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


pos_regex = r'\(\w*?\)'


def _entry_end(entry):
    brackets = [[a.start(0), a.end(0)] for a in re.finditer(r'\(.*?\)', entry.fullentry)]

    entry_ended = False
    start = 0

    newlines = [a for a in entry.annotations if a.value == 'newline']
    if len(newlines) > 0:
        entry_end = newlines[0].start
        entry_ended = True
    else:
        entry_end = len(entry.fullentry)
    while not entry_ended:
        period = entry.fullentry.find(u'.', start)
        if period != -1:
            if len(brackets) == 0:
                entry_end = period
                entry_ended = True
            for b in brackets:
                if b[0] <= period < b[1]:
                    entry_ended = False
                    start = b[1]
                    break
                else:
                    entry_end = period
                    entry_ended = True
        else:
            entry_end = len(entry.fullentry)
            entry_ended = True

    return entry_end


def _get_multiple_heads(entry, end):
    start = 0
    for match_pos in re.finditer(pos_regex, entry.fullentry[:end]):
        if match_pos.end(0) == end:
            pass



def annotate_head_and_pos(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations
                        if a.value == 'head' or a.value == 'iso-639-3' or
                           a.value == 'doculect' or a.value == 'pos']
    for a in head_annotations:
        Session.delete(a)
    # Delete this code and insert your code
    head = None
    heads = []

    entry_end = _entry_end(entry)

    if re.search(r'\(.*\)', entry.fullentry[:entry_end]) is None:
        return []

    splitted_heads = [a for a in
                      functions.split_entry_at(entry, pos_regex, 0, entry_end)
                      if entry.fullentry[a[0]:a[1]].find(';') == -1]

    for h in splitted_heads:
        start = h[0]
        for match_comma in re.finditer('(?:[,] ?|$)', entry.fullentry[h[0]:h[1]]):
            end = h[0] + match_comma.start(0)
            hd = entry.fullentry[start:end]
            if len(hd) > 0:
                chars_to_exclude = [u' ', u'-', u'–']
                chars_to_skip = 0
                for c in hd:
                    if c in chars_to_exclude:
                        chars_to_skip += 1
                    else:
                        break
                start += chars_to_skip
            head = functions.insert_head(entry, start, end)
            if head is not None:
                heads.append(head)
            start = h[0] + match_comma.end(0)

    for match_pos in re.finditer(pos_regex, entry.fullentry[:entry_end]):
        if match_pos.end(0) != entry_end:
            entry.append_annotation(match_pos.start(0) + 1, match_pos.end(0) - 1,
                                u'pos', u'dictinterpretation')

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations
                         if a.value == 'translation']

    for a in trans_annotations:
        Session.delete(a)

    trans_start = functions.get_pos_or_head_end(entry)
    if entry.fullentry[trans_start:].startswith(')'):
        trans_start = trans_start + 1
    newlines = functions.get_list_ranges_for_annotation(entry, 'newline')
    if len(newlines) > 0:
        trans_end = newlines[0][0]
    else:
        trans_end = _entry_end(entry)

    part_start = trans_start
    for match_semi_colon in re.finditer("(?:[,;] ?|$)",
                                        entry.fullentry[trans_start:trans_end]):
        e = match_semi_colon.start(0)
        s = match_semi_colon.end(0)
        for q in re.finditer(r'".*" ', entry.fullentry[trans_start:trans_end]):
            if q.start(0) <= match_semi_colon.end(0) <= q.end(0):
                e = q.end(0)
                break

        for b in re.finditer(r'\(.*\)', entry.fullentry[trans_start:trans_end]):
            if b.start(0) <= match_semi_colon.end(0) <= b.end(0):
                e = b.end(0)
                break

        part_end = trans_start + e

        functions.insert_translation(entry, part_start, part_end)
        if s > e:
            part_start = trans_start + s
        else:
            part_start = trans_start + e


def main(argv):

    bibtex_key = u"ottott1983"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=115,pos_on_page=14).all()
        
        startletters = set()
    
        for e in entries:
            try:
                #print "current page: %i, pos_on_page: %i" % (e.startpage, e.pos_on_page)
                heads = annotate_head_and_pos(e)
                if not e.is_subentry:
                    for h in heads:
                        if len(h) > 0:
                            startletters.add(h[0].lower())
                # annotate_pos(e)
                annotate_translations(e)
            except TypeError:
                print "   error on startpage: %i, pos_on_page: %i" % (e.startpage, e.pos_on_page)
                raise

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
