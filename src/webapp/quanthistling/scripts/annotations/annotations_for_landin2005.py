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

def annotate_entry(entry):
    for a in entry.annotations:
        if a.value in ['head', 'iso-639-3', 'doculect', 'pos', 'translation']:
            Session.delete(a)

    newlines = functions.get_list_ranges_for_annotation(entry, 'newline')
    lines = []
    n = last = 0
    for n, _ in newlines:
        lines.append((last, n))
        last = n
    lines.append((n, len(entry.fullentry)))

    heads = annotate_first_line(entry, *lines.pop(0))
    for l in lines:
        annotate_secondary_line(entry, heads, *l)
    return heads

def annotate_first_line(entry, start, end):
    heads, start = annotate_head(entry, start, end)
    match = re.compile('\s*\d\s*').match(entry.fullentry, start, end)
    if match:
        start = match.end()
    start = annotate_pos(entry, start, end)
    annotate_translation(entry, start, end)
    return heads

def annotate_secondary_line(entry, heads, start, end):
    match = re.compile('\s*\d\s*').match(entry.fullentry, start, end)
    if match:
        start = match.end()
    else:
        start = annotate_subhead(entry, heads, start, end)
    start = annotate_pos(entry, start, end)
    annotate_translation(entry, start, end)

def annotate_head(entry, start, end):
    heads = []
    bold = [b for b in functions.get_list_bold_ranges(entry, start) if b[1] <= end]
    if bold:
        s, e = bold[0]
    else:
        tabs = [t[0] for t in functions.get_list_ranges_for_annotation(entry, 'tab') if start < t[0] < end]
        if not tabs:
            functions.print_error_in_entry(entry, "No bold range in %i,%i, nor TAB found" % (start, end))
            return heads, start
        s,e = start, tabs[0]
        
    head = functions.insert_head(entry, s, e)
    if head is None:
        functions.print_error_in_entry(entry, "Head is None")
    else:
        heads.append(head)
    return heads, e

def annotate_subhead(entry, heads, start, end):
    bold = [b for b in functions.get_list_bold_ranges(entry, start) if b[1] <= end]
    if not bold:
        functions.print_error_in_entry("No bold range in %i,%i" % (start, end))
        return heads, start
    s, e = bold[0]
    part = entry.fullentry[s:e].strip(u' -–')
    if not part:
        functions.print_error_in_entry(entry, "No head found in %i,%i" % (start, end))
        return e
    for h in heads:
        functions.insert_head(entry, s, e, h+part)
    return e

def annotate_pos(entry, start, end):
    match = re.compile('\(([^)]*)\)').search(entry.fullentry, start, end)
    if match:
        for p_start, p_end in functions.split_entry_at(entry, r',\s*|$', match.start(1), match.end(1),
                                                       in_brackets=lambda x,y: False):
            entry.append_annotation(p_start, p_end, u'pos', u'dictinterpretation')
        start = match.end()
    return start

def annotate_translation(entry, start, end):
    for s, e in functions.split_entry_at(entry, r"[,?] |$", start, end):
        s, e, translation = functions.remove_parts(entry, s, e)
        match = re.compile(r'sing\. |pl\. |lit\. ').match(entry.fullentry, s, e)
        if match:
            translation = entry.fullentry[match.end():e] 
        functions.insert_translation(entry, s, e, translation)

def main(argv):

    bibtex_key = u"landin2005"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=8,pos_on_page=5).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_entry(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
