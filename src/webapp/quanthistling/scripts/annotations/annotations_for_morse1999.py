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
    head = entry.fullentry[start:end]
    head = re.sub("[* ]*$", "", head)
    head = functions.insert_head(entry, start, end, head)
    return head

def annotate_crossref(entry, start, end, in_brackets):
    for c_start, c_end in functions.split_entry_at(entry, r' V\. |sin\. |$', start, end, True, in_brackets):
        c_end = functions.find_first_point(entry, c_start, c_end)
        for cr_start, cr_end in functions.split_entry_at(entry, ur' ǀ |[,;:] |$', c_start, c_end, False, in_brackets):
            if cr_start != cr_end:
                entry.append_annotation(cr_start, cr_end, u'crossreference', u'dictinterpretation')

def annotate_everything(entry):
    # heads
    head = None
    heads = []
    
    head_end_tmp = functions.get_last_bold_pos_at_start(entry)
    head_tmp = entry.fullentry[:head_end_tmp]
    match = re.match(u'(\w+.*)\d+\.', head_tmp)
      
    # remove numbers at end of head
    if match:
        head_tmp = match.group(1)
        head_end_tmp = head_end_tmp - 3

    for h_start, h_end in functions.split_entry_at(entry, r', |$', 0, head_end_tmp):
        head = insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)

    in_brackets = functions.get_in_brackets_func(entry)
    for p_start, p_end in functions.split_entry_at(entry, ur' —|$', head_end_tmp, len(entry.fullentry),
                                                   in_brackets=in_brackets):
        # parts of speech
        pos_se = functions.get_first_italic_in_range(entry, p_start, p_end)
        pos = entry.fullentry[pos_se[0]:pos_se[1]]
        functions.insert_pos(entry, pos_se[0], pos_se[1], pos)   

        # translations
        rest_start = pos_se[1]

        #skip first pair of brackets
        match = re.compile(r'\s*\([^(]*\)').match(entry.fullentry, rest_start, p_end)
        if match:
            rest_start = match.end()

        for num_start, num_end in functions.split_entry_at(entry, r' \d\. |$', rest_start, p_end, True,
                                                           in_brackets=in_brackets):
            trans_end = functions.find_first_point(entry, num_start, num_end, in_brackets)
            match = re.compile('\s*\(sin(.*)\)\s*').match(entry.fullentry, trans_end, num_end)
            if match: #simple crossrefs (sin ...)
                for cr_start, cr_end in functions.split_entry_at(entry, ur' ǀ |[,;:] |$', match.start(1), match.end(1),
                                                                 lambda x,y: False):
                    if cr_start != cr_end:
                        entry.append_annotation(cr_start, cr_end, u'crossreference', u'dictinterpretation')
                trans_end = match.start()
            for t_start, t_end in functions.split_entry_at(entry, r',|;|$', num_start, trans_end):
                functions.insert_translation(entry, t_start, t_end)

            if not match:
                annotate_crossref(entry, trans_end, num_end, in_brackets)

    return heads


def main(argv):

    bibtex_key = u"morse1999"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=12).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_dialect(e)
            #annotate_pos(e)
            #annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
