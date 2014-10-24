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

def annotate_head_in_brackets(entry, head_start, head_end, heads):
    index = entry.fullentry.find('(', 0, head_end)
    if index == -1:
        return head_end
    regex = re.compile(' \([^(]+\)')
    for match in regex.finditer(entry.fullentry, head_start, head_end):
        if '.' in match.group():
            continue
        head_start = match.start()+2
        if entry.fullentry[head_start] == '-':
            entry.append_annotation(head_start, head_start+1,
                                    u'boundary', u'dictinterpretation', u"morpheme boundary")
            head_start += 1
        head = functions.insert_head(entry, head_start, match.end()-1)
        if head is not None:
            heads.append(head)
    return index

def annotate_everything(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value in ['head', "iso-639-3", "doculect", 'translation', 'boundary' ]]
    for a in head_annotations:
        Session.delete(a)

    #annotate heads
    heads = []

    sorted_annotations = [ a for a in entry.annotations if a.value=='tab']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    if len(sorted_annotations) < 2:
        functions.print_error_in_entry(entry, "number of tabs is lower 2")
        return heads

    head_start = 0
    head_end = functions.get_last_bold_pos_at_start(entry)
    boundary_index = entry.fullentry.find('-', 0, head_end)
    if boundary_index != -1:
        entry.append_annotation(boundary_index, boundary_index+1,
                                u'boundary', u'dictinterpretation', u"morpheme boundary")
        if boundary_index == 0:
            head_start = 1
        else:
            head_end = boundary_index

    first_head_end = annotate_head_in_brackets(entry, head_start, head_end, heads)
    head = functions.insert_head(entry, head_start, first_head_end)
    heads.append(head)

    #annotate translation
    for s, e in functions.split_entry_at(entry, r"(?:[;] |$)", sorted_annotations[1].end, len(entry.fullentry)):
        s, e, string = functions.remove_parts(entry, s, e)
        string = re.sub('[!?¿¡]', '', string)
        string = re.sub('\s*[0-9][a-z]+\s*', '', string) #remove POS from translation 3sg 2pl 
        functions.insert_translation(entry, s, e, string)
    
    return heads

def main(argv):

    bibtex_key = u"kakumasukakumasu2007"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=100,pos_on_page=5).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
