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

def get_bold_range(entry, max_from_start = 0):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    if len(sorted_annotations) == 0:
        return -1, -1

    if sorted_annotations[0].start > max_from_start:
        return -1, -1
        
    last_bold_end = sorted_annotations[0].start
    first_bold_start = sorted_annotations[0].start
    at_start = True
    for a in sorted_annotations:
        if at_start and ((a.start <= (last_bold_end + 1)) or \
                entry.fullentry[last_bold_end:a.start].strip() == u"♦"):
            last_bold_end = a.end            
        else:
            at_start = False

    return first_bold_start, last_bold_end

def insert_head(entry, start, end):
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
    for match in re.finditer(u"-", str_head):
        entry.append_annotation(match.start(0), match.end(0), u'boundary', u'dictinterpretation', u"morpheme boundary")

    str_head = re.sub("-", "", str_head)
    str_head = re.sub("[!12]", "", str_head)
    return functions.insert_head(entry, start, end, str_head)


def annotate_head(entry):
    # delete head annotations
    annotations = [a for a in entry.annotations if a.value == 'head'
                   or a.value == 'doculect' or a.value == 'iso-639-3' or a.value == 'morpheme boundary']
    for a in annotations:
        Session.delete(a)

    heads = []

    head_start, head_end = get_bold_range(entry, max_from_start = 5)

    if head_start == -1:
        functions.print_error_in_entry(entry, 'No head detected.')
        return []

    match_number = re.match(u"[^♦]*♦ \d\. ?", entry.fullentry[:head_end])
    if match_number:
        head_start = match_number.end(0)

    head = insert_head(entry, head_start, head_end)
    heads.append(head)

    return heads


def annotate_pos(entry):
    # delete pos annotations
    pos = [a for a in entry.annotations if a.value == 'pos']
    for p in pos:
        Session.delete(p)

    italic = functions.get_first_italic_range(entry)
    head_end = functions.get_head_end(entry)

    if italic != -1 and ((italic[0] - head_end < 3) or \
            re.match(u"^ ?\[[^\]]*\] ?$", entry.fullentry[head_end:italic[0]])):
        entry.append_annotation(italic[0], italic[1], u'pos',
                                u'dictinterpretation')


def annotate_translation(entry):
    # delete translations
    trans = [a for a in entry.annotations if a.value == 'translation']
    for t in trans:
        Session.delete(t)

    trans_start = functions.get_pos_or_head_end(entry)
    trans_end = len(entry.fullentry)
    match_colon = entry.fullentry[trans_start:].find(":")
    if match_colon != -1:
        trans_end = trans_start + match_colon
    else:
        match_period = entry.fullentry[trans_start:].find(".")
        if match_period != -1:
            trans_end = trans_start + match_period

    match_bracket = re.search("\[[^\]]*\] ?$", entry.fullentry[trans_start:trans_end])
    if match_bracket:
        trans_end -= len(match_bracket.group(0))

    for s, e in functions.split_entry_at(entry, r"(?:[,;] |$)", trans_start, trans_end):
        functions.insert_translation(entry, s, e)


def main(argv):
    bibtex_key = u'ramirez2006'
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=216,pos_on_page=11).all()

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