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

def insert_head(entry, start, end):
    start, end = functions.strip(entry, start, end)
    while start < end and entry.fullentry[end-1].isdigit():
        end -= 1

    if entry.fullentry[start] == "-":
        entry.append_annotation(start, start+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
        start += 1
    if entry.fullentry[end-1] == "-":
        entry.append_annotation(end-1, end, u'boundary', u'dictinterpretation', u"morpheme boundary")
        end -= 1

    return functions.insert_head(entry, start, end)


def annotate_head(entry, start, end):
    head = None
    heads = []
    
    bold = functions.get_first_bold_in_range(entry, start, end)
    if bold != -1 and bold[0] - 2 < start:
        head = insert_head(entry, *bold)
        if head:
            heads.append(head)
        head_end = bold[1]
    else:
        head_end = start
    return heads, head_end


def annotate_pos(entry, start, end):
    while True:
        italic = functions.get_first_italic_in_range(entry, start, end)
        if italic != -1 and italic[0] - 2 < start:
            for p_start, p_end in functions.split_entry_at(entry, '/|$', italic[0], italic[1], False,
                                                           lambda x,y: False):
                p_start, p_end = functions.strip(entry, p_start, p_end, ' ', '. ')
                if p_start < p_end:
                    entry.append_annotation(p_start, p_end, u'pos', u'dictinterpretation',
                                            entry.fullentry[p_start:p_end])
            start = skip_brackets(entry, italic[1], end)
        else:
            break
    return start

def annotate_translations(entry, start, end):
    start = skip_brackets(entry, start, end)
    match_last_pos = re.compile("/[^.]*\.").match(entry.fullentry, start, end)
    if match_last_pos:
        start = match_last_pos.end(0)
    
    brackets = functions.find_brackets(entry, '[', ']')
    brackets.extend(functions.find_brackets(entry, '(', ')'))
    brackets.sort()
    in_brackets = functions.get_in_brackets_func(entry, brackets)
    for num_start, num_end in functions.split_entry_at(entry, '\d\. |$', start, end, True, in_brackets):
        num_end = re.compile('[.:] |$').search(entry.fullentry, num_start, num_end).start()
        for t_start, t_end in functions.split_entry_at(entry, '[,;!?][ (]|$', num_start, num_end, False, in_brackets):
            functions.insert_translation(entry, t_start, t_end)

def skip_brackets(entry, start, end):
    efe = entry.fullentry
    brackets = functions.find_brackets(entry)
    while start < end:
        while efe[start].isspace():
            start += 1
        if efe[start] != '(' or start == end:
            break
        try:
            start = next(b[1] for b in brackets if b[0] == start)
            if start < end and efe[start] == '.':
                start += 1
        except StopIteration:
            print brackets, start
            functions.print_error_in_entry(entry, "Problem finding matching brackets.")
            return end
    return start

def annotate_first_line(entry, start, end):
    head_annotations = [ a for a in entry.annotations if a.value in
                         ['head', "iso-639-3", "doculect", 'boundary', 'pos', 'translation']]
    for a in head_annotations:
        Session.delete(a)

    heads, start = annotate_head(entry, start, end)
    start = annotate_pos(entry, start, end)
    annotate_translations(entry, start, end)
    return heads

def annotate_secondary_line(entry, start, end):
    start = skip_brackets(entry, start, end)
    heads, start = annotate_head(entry, start, end)
    start = annotate_pos(entry, start, end)
    annotate_translations(entry, start, end)
    return heads

def main(argv):
    bibtex_key = u"dooley2006"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=4).all()

        startletters = set()
    
        for e in entries:
            #split on newline, but ignore newline at pagebreak
            pagebreaks = [b[0] for b in functions.get_list_ranges_for_annotation(e, 'pagebreak')]
            newlines = [n[0] for n in functions.get_list_ranges_for_annotation(e, 'newline')
                        if not [ b for b in pagebreaks if abs(n[0] - b) < 3 ]]
            lines = []
            n = last = 0
            for n in newlines:
                lines.append((last, n))
                last = n
            lines.append((n, len(e.fullentry)))
            heads = annotate_first_line(e, *lines.pop(0))
            for l in lines:
                heads.extend(annotate_secondary_line(e, *l))
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
