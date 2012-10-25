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
    
def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
    
    head = ""
    heads = []
    # get everyting until the first dot
    tmp = entry.fullentry.split('.', 1)
    if len(tmp) > 1:
        if tmp[1] == '' or re.match(r'^\s*$', tmp[1]):
            head = None
        else:
            head = tmp[0].rsplit(' ', 1)[0]
    else:
        head = None

    if head == None or re.search(u'[A-Z]', head):
        head = re.sub(r'^(.*?)[A-Z].*', r'\1', entry.fullentry)
        head = head.strip()
        #print "uc head" + head.encode('utf8')
        if head == '' or head == entry.fullentry:
            head == None

    if head != None:
        head_start = 0
        head_end = len(head)
        match = re.search(r"\((.*?)\)", head)
        if match:
            head = entry.fullentry[head_start:match.start(0)]
            heads.append(head)
            heads.append(head + match.group(1))
            functions.insert_head(entry, head_start, match.start(0))
            #entry.append_annotation(head_start, match.start(0), u'head', u'dictinterpretation')
            functions.insert_head(entry, head_start, head_end)
            #entry.append_annotation(head_start, head_end, u'head', u'dictinterpretation', head + match.group(1))
        else:
            functions.insert_head(entry, head_start, head_end)
            #entry.append_annotation(head_start, head_end, u'head', u'dictinterpretation')
            heads.append(entry.fullentry[head_start:head_end])
            
    return heads

def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    # subentries have no pos here
    match_first_dot = re.search(r"\.", entry.fullentry)
    if entry.is_subentry or (match_first_dot and match_first_dot.start(0) == len(entry.fullentry)-1):
        return
    
    # suppose a maximum of three adjacent parts-of-speech
    match = re.search(r' (\w*?\.(?:, ?\w*?\.)?(?:, ?\w*?\.)?)', entry.fullentry)
    if match:
        pos_start = match.start(1)
        pos_end = match.end(1)
        substr = entry.fullentry[pos_start:pos_end]
        #print "before post: " + substr.encode('utf-8')
        start = pos_start
        for match_pos in re.finditer(r', ?', substr):
            end = match_pos.start(0) + pos_start
            entry.append_annotation(start, end, u'pos', u'dictinterpretation')
            start = match_pos.end(0) + pos_start
        end = pos_end
        entry.append_annotation(start, end, u'pos', u'dictinterpretation')

def annotate_translations(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_starts = []
    translation_ends = []

    if re.search(r'\d\.', entry.fullentry):
        for match in re.finditer(r'(?<=\d\.)(.*?)(?:\d\.|$)', entry.fullentry):
            end = match.end(1)
            start = match.start(1)
            translation_starts.append(start)
            translation_ends.append(end)
            #entry.append_annotation(start, end, u'translation', u'dictinterpretation')
    else:
        match = re.search(u'[A-Z¡]', entry.fullentry)
        if match:
            translation_starts.append(match.start(0))
            translation_ends.append(len(entry.fullentry))
            #entry.append_annotation(match.start(0), len(entry.fullentry), u'translation', u'dictinterpretation')
        else:
            match_dot = re.search(r'\. ?', entry.fullentry)
            if match_dot:
                translation_starts.append(match_dot.end(0))
                translation_ends.append(len(entry.fullentry))
                #entry.append_annotation(match_dot.end(0), len(entry.fullentry), u'translation', u'dictinterpretation')
            else:
                print "translation error"
                print entry.fullentry.encode('utf-8')
                print entry.startpage
                print entry.pos_on_page

    for i in range(len(translation_starts)):
        substr = entry.fullentry[translation_starts[i]:translation_ends[i]]
        #print "before post: " + substr.encode('utf-8')
        start = translation_starts[i]
        end = 0

        for match in re.finditer(u'(?:,|;|\? ¿| \(|(?:\)\.)?$) ?', substr):
            end = match.start(0) + translation_starts[i]
            if end > start and entry.fullentry[start:end] != "etc.":
                functions.insert_translation(entry, start, end)
            start = match.end(0) + translation_starts[i]
        #end = translation_ends[i]
        #if end > start:
        #    functions.insert_translation(entry, start, end)
    

def main(argv):
    bibtex_key = u"minor1971"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=64,pos_on_page=35).all()
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
            #annotate_examples(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
    
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)