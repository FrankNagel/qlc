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
from manualannotations_for_minor1987 import manual_entries


def remove_parts_translation(str, s, e):
    start = s
    end = e
    subsubstr = str
    match_parts_end = re.search(u" ?Sinón: .*?$", subsubstr)
    if match_parts_end:
        end = end - len(match_parts_end.group(0))
    match_parts_end = re.search(u" ?Parón: .*?$", subsubstr)
    if match_parts_end:
        end = end - len(match_parts_end.group(0))
    match_parts_end = re.search(u" ?etc\. ?$", subsubstr)
    if match_parts_end:
        end = end - len(match_parts_end.group(0))
    return [start, end]

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    for match in re.finditer(u'(?:Parón|Sinón): (.*?)\.', entry.fullentry):
        substr = entry.fullentry[match.start(1):match.end(1)]
        #entry.append_annotation(match.start(1), match.end(1), u'crossreference', u'dictinterpretation')
        start = match.start(1)
        for match_comma in re.finditer(r'(:?, ?|$)', substr):
            end = match_comma.start(0) + match.start(1)
            entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
            start = match_comma.end(0) + match.start(1)
    
def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)
        
    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_start_pos = 0

    heads = []
    
    match = re.search(u" ?\(.*?\) ?$", entry.fullentry[:head_end_pos])
    if match:
        head_end_pos = match.start(0)

    start = head_start_pos
    for match in re.finditer(r' ?, ?', entry.fullentry[head_start_pos:head_end_pos]):
        end = match.start(0) + head_start_pos
        inserted_head = functions.insert_head(entry, start, end)
        heads.append(inserted_head)
        start = match.end(0) + head_start_pos
    end = head_end_pos
    inserted_head = functions.insert_head(entry, start, end)
    heads.append(inserted_head)

    #inserted_head = functions.insert_head(entry, head_start_pos, head_end_pos)
    #heads.append(inserted_head)
    
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
    
    #entry.append_annotation(italic_annotation.start, italic_annotation.end, u'pos', u'dictinterpretation')
    pos_start = italic_annotation.start
    pos_end = italic_annotation.end
    start = pos_start
    substr = entry.fullentry[pos_start:pos_end]
    for match in re.finditer(r', ?', substr):
        end = match.start(0) + pos_start
        entry.append_annotation(start, end, u'pos', u'dictinterpretation')
        start = match.end(0) + pos_start
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
        for match in re.finditer(r'(?<=\d\.)(.*?)(?:\d\.|$|\()', entry.fullentry):
            end = match.end(1)
            start = match.start(1)
            translation_starts.append(start)
            translation_ends.append(end)
            #a = remove_parts_translation(entry.fullentry[start:end], start, end)
            #entry.append_annotation(a[0], a[1], u'translation', u'dictinterpretation')
    else:
        sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
        sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
        end_pos = 0
        if len(sorted_annotations) > 0:
            end_pos = sorted_annotations[0].end
            pattern = re.compile(r' ?(.*?)(?:\(|$)')
        else:
            pattern = re.compile(r'^.*?\.(.*?)(?:\(|$)')
        match = pattern.search(entry.fullentry, end_pos)
        if match:
            end = match.end(1)
            start = match.start(1)
            translation_starts.append(start)
            translation_ends.append(end)
            #a = remove_parts_translation(entry.fullentry[start:end], start, end)
            #entry.append_annotation(a[0], a[1], u'translation', u'dictinterpretation')

    for i in range(len(translation_starts)):
        substr = entry.fullentry[translation_starts[i]:translation_ends[i]]
        match_parts_end = re.search(u"\. (?:Parón|Sinón|Vocativo|Pl):", substr)
        if match_parts_end:
            substr = entry.fullentry[translation_starts[i]:(translation_starts[i]+match_parts_end.start(0))]
        #print "before post: " + substr.encode('utf-8')
        start = translation_starts[i]
        end = 0

        for match in re.finditer(u'(?:[,;] ?|\? ¿|$)', substr):
            end = match.start(0) + translation_starts[i]
            subsubstr = entry.fullentry[start:end]
            a = remove_parts_translation(subsubstr, start, end)
            subsubstr = entry.fullentry[a[0]:a[1]]
            #print "after post: " + subsubstr.encode('utf-8')
            if (a[0] < a[1]) and not(re.match(r"\s*$", subsubstr)):
                functions.insert_translation(entry, a[0], a[1])
                
            start = match.end(0) + translation_starts[i]
        #end = translation_ends[i]
        #subsubstr = entry.fullentry[start:end]
        #a = remove_parts_translation(subsubstr, start, end)
        #subsubstr = entry.fullentry[a[0]:a[1]]
        #print "after post: " + subsubstr.encode('utf-8')
        #if (a[0] < a[1]) and not(re.match(r"\s*$", subsubstr)):
            #entry.append_annotation(a[0], a[1], u'translation', u'dictinterpretation')
        #    functions.insert_translation(entry, a[0], a[1])
    

def annotate_examples(entry):
    # delete pos annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    pattern = re.compile(r'(?:\.|\?|\!)')
    pattern_bracket = re.compile(r'\(')
    for match in re.finditer(r'\(Ej\. ?(.*?\)?\.?)\)', entry.fullentry):
        #print entry.fullentry.encode('utf-8')
        start_src = match.start(1)
        end_tgt = match.end(1)
        # correct open bracket problem
        if pattern_bracket.search(entry.fullentry, start_src, end_tgt):
            #print "bracket in entry"
            #print entry.fullentry.encode('utf-8')
            #print entry.startpage
            #print entry.pos_on_page
            end_tgt = end_tgt + 2
        m = pattern.search(entry.fullentry, start_src, end_tgt)
        if m:
            end_src = m.end(0)
            start_tgt = m.end(0) + 1
            entry.append_annotation(start_src, end_src, u'example-src', u'dictinterpretation')
            entry.append_annotation(start_tgt, end_tgt, u'example-tgt', u'dictinterpretation')
        else:
            print "false example"
            print entry.fullentry.encode('utf-8')


def main(argv):
    bibtex_key = u"minor1987"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=5,pos_on_page=5).all()
        #entries = []
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
            annotate_examples(e)
            annotate_crossrefs(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
        
        Session.commit()

    for e in manual_entries:
        dictdata = model.meta.Session.query(model.Dictdata).join(
            (model.Book, model.Dictdata.book_id==model.Book.id)
            ).filter(model.Book.bibtex_key==bibtex_key).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(e["startpage"])).first()
        
        entry_db = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
        if difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio() > 0.95:
            entry_db.fullentry = e["fullentry"].decode('utf-8')
            # delete all annotations in db
            for a in entry_db.annotations:
                Session.delete(a)
            # insert new annotations
            for a in e["annotations"]:
                entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
        else:
            print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem." % (e["startpage"], e["pos_on_page"])

    Session.commit()

if __name__ == "__main__":
    main(sys.argv)