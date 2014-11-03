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

def annotate_head(entry, in_brackets):
    heads = []
    head_start = 0
    head_end = functions.get_last_bold_pos_at_start(entry)

    for h_start, h_end in functions.split_entry_at(entry, r'[,;]|$', head_start, head_end, False, in_brackets):
        for index in xrange(h_start, h_end):
            if entry.fullentry[index] == '-':
                entry.append_annotation(index, index+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
        h_start, h_end, head = functions.remove_parts(entry, h_start, h_end)
        while h_end > h_start and (head[-1].isdigit() or head[-1] == '-'):
            h_end -= 1
            head = head[:-1]
        while h_start < h_end and head[0] == '-':
            h_start += 1
            head = head[1:]
        head = functions.insert_head(entry, h_start, h_end, head)
        if head:
            heads.append(head)

    return heads

        
def annotate_everything(entry):
    in_brackets = functions.get_in_brackets_func(entry)

    #heads
    heads = annotate_head(entry, in_brackets)
    
    # pos
    ir = functions.get_first_italic_range(entry)
    if ir != -1:
        for p_start, p_end in functions.split_entry_at(entry, ' |$', *ir, in_brackets=in_brackets):
            functions.insert_pos(entry, p_start, p_end)

    rest_start = functions.get_pos_or_head_end(entry) +1 #.at end of pos
    rest_end = len(entry.fullentry)
    for num_start, num_end in functions.split_entry_at(entry, r'\d\.|$', rest_start, rest_end, False, in_brackets):
        first_point = functions.find_first_point(entry, num_start, num_end, in_brackets)
        first_bold = functions.get_first_bold_start_in_range(entry, num_start, num_end)
        if first_bold == -1:
            first_bold = first_point
        trans_end = min(first_point, first_bold)
        for t_start, t_end in functions.split_entry_at(entry, r'[,;]|$', num_start, trans_end, False, in_brackets):
            while t_start < t_end and entry.fullentry[t_start] in u' "¿¡':
                t_start += 1
            while t_end > t_start and entry.fullentry[t_end-1] in ' "?!.':
                t_end -= 1
            translation = entry.fullentry[t_start:t_end].translate(dict((ord(k),None) for k in u'¿¡?!'))
            functions.insert_translation(entry, t_start, t_end, translation)
    return heads
 
 
def main(argv):

    bibtex_key = u"ferreira2005"
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    cmd = """\
        delete from annotation
        using book tb, entry te
        where tb.bibtex_key = :bibtex_key and tb.id = te.book_id and te.id = entry_id
             and annotationtype_id = (select id from annotationtype where type = 'dictinterpretation')"""
    Session.execute(cmd, dict(bibtex_key=bibtex_key))

    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=129,pos_on_page=17).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
