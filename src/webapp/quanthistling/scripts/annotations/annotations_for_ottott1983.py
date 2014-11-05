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


page_pattern = re.compile('\[Seite\s+\d+\]')
def clean_out_pagebreaks(string):
    match = page_pattern.match(string)
    if match:
        return string[:match.start()] + string[match.end():]
    return string

def annotate_head_and_pos(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations
                        if a.value == 'head' or a.value == 'iso-639-3' or
                           a.value == 'doculect' or a.value == 'pos']
    for a in head_annotations:
        Session.delete(a)

    heads = []

    head_start = 0
    while True: #possible several '<head> (<pos>)' seperated by ','
        head_end = functions.find_first(entry, '(', head_start, len(entry.fullentry), lambda x,y: False)
        if head_end == len(entry.fullentry):
            head_end = functions.find_first(entry, ' V. ', 0, len(entry.fullentry))
            if head_end == len(entry.fullentry):
                return heads # early return if i can't parse a head
            have_pos = False
        else:
            have_pos = True

        for h_start, h_end in functions.split_entry_at(entry, r',|$', head_start, head_end):
            h_start = functions.lstrip(entry, h_start, h_end, u' -–')
            head = functions.insert_head(entry, h_start, h_end)
            if head:
                heads.append(head)

        if have_pos:
            pos_end = functions.find_first(entry, ')', head_end, len(entry.fullentry), lambda x,y: False)
            entry.append_annotation(head_end+1, pos_end, u'pos', u'dictinterpretation')
        else:
            break
        #another head?
        if pos_end + 1 < len(entry.fullentry) and \
          re.compile(u',|\s*[-–]').match(entry.fullentry, pos_end + 1):
            head_start = pos_end + 2
        else:
            break

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

    #crossrefs
    crossref_match = re.compile('\s*V\. ').match(entry.fullentry, trans_start)
    if crossref_match:
        return trans_start

    in_brackets = functions.get_in_brackets_func(entry)
    trans_end = min(functions.find_first_point(entry, trans_start, len(entry.fullentry), in_brackets),
                    functions.find_first(entry, u' V. ', trans_start, len(entry.fullentry), in_brackets))

    for t_start, t_end in functions.split_entry_at(entry, r'[,;]|$', trans_start, trans_end, False, in_brackets):
        t_start, t_end, translation = functions.remove_parts(entry, t_start, t_end)
        translation = clean_out_pagebreaks(translation)
        functions.insert_translation(entry, t_start, t_end, translation)
    return trans_end

def annotate_crossref(entry, start):
    crossref_match = re.compile('\.?\s+V\. ').match(entry.fullentry, start)
    if not crossref_match:
        return
    start = crossref_match.end()
    in_brackets = functions.get_in_brackets_func(entry)
    end = functions.find_first_point(entry, start, len(entry.fullentry), in_brackets)
    for c_start, c_end in functions.split_entry_at(entry, r'[,;]|$', start, end, False, in_brackets):
        c_start = functions.lstrip(entry, c_start, c_end, u' -–')
        c_start, c_end, crossref = functions.remove_parts(entry, c_start, c_end)
        if crossref.startswith('Apuntes Gramaticales'):
            return
        crossref = clean_out_pagebreaks(crossref)
        entry.append_annotation(c_start, c_end, u'crossreference', u'dictinterpretation', crossref)


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
                heads = annotate_head_and_pos(e)
                if not e.is_subentry:
                    for h in heads:
                        if len(h) > 0:
                            startletters.add(h[0].lower())
                if heads:
                    trans_end = annotate_translations(e)
                    annotate_crossref(e, trans_end)
            except TypeError:
                print "   error on startpage: %i, pos_on_page: %i" % (e.startpage, e.pos_on_page)
                raise

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
