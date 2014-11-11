# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

# Pylons model init sequence
import pylons.test
from paste.deploy import appconfig

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
import functions

def _add_head_with_comma(entry, s, e):
    start = s
    heads = []
    for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[s:e]):
        end = s + match_comma.start(0)
        start, end, string = functions.remove_parts(entry, start, end)
        if entry.fullentry[end-1] == ':':
            end -= 1
            string = string[:-1]
        string = string.replace('/', '')
        head = functions.insert_head(entry, start, end, string)
        if head:
            heads.append(head)
        start = s + match_comma.end(0)
    return heads


def annotate_head(entry, start, end):
    heads = []

    bolds = [b for b in functions.get_list_bold_ranges(entry) if b[0] >= start and b[1] <= end]
    last_bold_end = start
    for b in bolds:
        between = entry.fullentry[last_bold_end:b[0]]
        # remove brackets
        between = re.sub(r"\([^)]*\)", "", between)
        between = re.sub(r",", "", between)
        between = re.sub(r"\s+", "", between)
        if between != "":
            break
        heads += _add_head_with_comma(entry, b[0], b[1])
        last_bold_end = b[1]

    return heads, last_bold_end


bracket_pattern = re.compile(r'\s*\([^)]*\)\s*')

def annotate_translations(entry, start, end):
    brackets = functions.find_brackets(entry)
    in_brackets = functions.get_in_brackets_func(entry, brackets)

    for num_start, num_end in functions.split_entry_at(entry, r'\d\.|$', start, end, False, in_brackets):
        for t_start, t_end in functions.split_entry_at(entry, r',|$', num_start, num_end, False, in_brackets):
            for t_start2, t_end2 in functions.split_entry_at(entry, r'\([^)]*\):?|$', t_start, t_end,
                                                             False, in_brackets):
                if in_brackets(t_start2, t_start2) or in_brackets(t_end2, t_end2):
                    #can happen with nested brackets
                    continue
                # remove brackets at start
                while True:
                    match = bracket_pattern.match(entry.fullentry, t_start2, t_end2)
                    if not match:
                        break
                    t_start2 = match.end()
                t_end2 = functions.find_first(entry, '(', t_start2, t_end2, lambda x, y: False)
                functions.insert_translation(entry, t_start2, t_end2)


def annotate_backentries(entry):
    """
    Two possibilities: "<b>head:</b> translation" or "<b>head</b>(pos): translation"
    Occurs only at the end.
    """
    heads = []
    bold = functions.get_list_bold_ranges(entry)
    brackets = functions.find_brackets(entry)
    end = len(entry.fullentry)

    while True:
        index = entry.fullentry.rfind(':', 0, end)
        if index <= 0:
            break
        bracket_region = next((b for b in brackets  if b[1] == index), None)
        if bracket_region:
            index = bracket_region[0]
            index = functions.rstrip(entry, 0, index) - 1 #strip whitespace and one step more to match case with bold :
        head_region = next((b for b in bold  if b[1]-1 == index), None)
        if not head_region:
            break
        head, start = annotate_head(entry, *head_region)
        heads.extend(head)
        annotate_translations(entry, start, end)
        end = head_region[0]
    return heads, end


def delete_dictinterpretation(entry):
    for a in entry.annotations:
        if a.annotationtype.type == 'dictinterpretation':
            Session.delete(a)

def main(argv):

    bibtex_key = u"payne1980"

    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata)\
      .join(model.Book, model.Dictdata.book_id == model.Book.id)\
      .filter(model.Book.bibtex_key == bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=42,pos_on_page=18).all()

        startletters = set()

        for e in entries:
            delete_dictinterpretation(e)
            heads, end = annotate_backentries(e)
            heads2, start = annotate_head(e, 0, end)
            heads.extend(heads2)
            annotate_translations(e, start, end)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
