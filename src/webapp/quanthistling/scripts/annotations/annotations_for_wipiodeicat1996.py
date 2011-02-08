# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter

# Pylons model init sequence
import pylons.test
import logging

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.books

from paste.deploy import appconfig

import functions

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    for match_crossref in re.finditer(u'\((?:vea|Sinón\.) (.*?)\)', entry.fullentry):
        start = match_crossref.start(1)
        substr = entry.fullentry[match_crossref.start(1):match_crossref.end(1)]
        for match in re.finditer(r', ?', substr):
            end = match.start(0) + match_crossref.start(1)
            entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
            start = match.end(0) + match_crossref.start(1)
        end = match_crossref.end(1)
        entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
        #entry.append_annotation(match.start(1), match.end(1), u'crossreference', u'dictinterpretation')

def insert_head(entry, start, end):
    substr = entry.fullentry[start:end]
    match = re.search(r"(?! )(\()(.*?)\)", substr)
    if match:
        heads = []
        head_base = entry.fullentry[start:match.start(1)]
        entry.append_annotation(start, match.start(1), u"head", u"dictinterpretation")
        heads.append(head_base)
        entry.append_annotation(start, end, u"head", u"dictinterpretation", head_base + match.group(2))
        heads.append(head_base + match.group(2))
        return heads
    else:
        entry.append_annotation(start, end, u"head", u"dictinterpretation")
        return [substr]

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []
    
    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_start_pos = 0

    heads = []

    if head_end_pos > -1:
        start = head_start_pos
        substr = entry.fullentry[head_start_pos:head_end_pos]
        for match in re.finditer(r', ?', substr):
            end = match.start(0) + head_start_pos
            inserted_heads = insert_head(entry, start, end)
            #entry.append_annotation(start, end, u'head', u'dictinterpretation')
            heads.extend(inserted_heads)
            start = match.end(0) + head_start_pos
        end = head_end_pos
        inserted_heads = insert_head(entry, start, end)
        #entry.append_annotation(start, end, u'head', u'dictinterpretation')
        heads.extend(inserted_heads)
    else:
        if entry.fullentry[0] == u"║" and entry.is_subentry():
            head_annotations_mainentry = [ a for a in entry.mainentry().annotations if a.value=='head']
            for a in head_annotations_mainentry:
                entry.append_annotation(0, 1, "head", "dictinterpretation", a.string)
        else:
            print "no head"
            print entry.fullentry.encode('utf-8')
        
    return heads

def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    if len(sorted_annotations) > 0:
        italic_annotation = sorted_annotations[0]
    else:
        return
    
    start = italic_annotation.start
    end = italic_annotation.end
    entry.append_annotation(start, end, u'pos', u'dictinterpretation')

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    if len(pos_annotations) > 0:
        head_end_pos = pos_annotations[0].end
    else:
        head_end_pos = functions.get_last_bold_pos_at_start(entry)
        
    if head_end_pos > -1:
        substr = entry.fullentry[head_end_pos:]
        if re.match(u" ?\(vea ", substr):
            return
        start = head_end_pos
        for match in re.finditer(r'(?:, ?|; ?|\d\. )', substr):
            end = match.start(0) + head_end_pos
            pattern = re.compile(u' ?\(Sinón ')
            match_link = pattern.search(entry.fullentry[start:end])
            if match_link:
                end = match_link.start(0)
            if not(re.match(r"\s*$", entry.fullentry[start:end])):
                functions.insert_translation(entry, start, end)
            start = match.end(0) + head_end_pos
        end = len(entry.fullentry)
        pattern = re.compile(u' ?\(Sinón ')
        match_link = pattern.search(entry.fullentry[start:end])
        if match_link:
            end = match_link.start(0)
        if not(re.match(r"\s*$", entry.fullentry[start:end])):
            functions.insert_translation(entry, start, end)

def main(argv):
    bibtex_key = u"wipiodeicat1996"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=109,pos_on_page=18).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
            annotate_crossrefs(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)