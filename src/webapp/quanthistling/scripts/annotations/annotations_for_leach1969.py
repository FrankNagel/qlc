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
from manualannotations_for_leach1969 import manual_entries

def annotate_dialect(entry):
    # delete head annotations
    dialect_annotations = [ a for a in entry.annotations if a.value=='dialectidentification']
    for a in dialect_annotations:
        Session.delete(a)
    
    match = re.search(u'\([DU]\)', entry.fullentry)
    if match:
        if match.group(0) == '(D)':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto dyohxaya de Ocaina')
        elif match.group(0) == '(U)':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto uvohsa de Ocaina')        

def insert_translation(entry, s, e):
    start = s
    end = e
    string = entry.fullentry[start:end]
    # remove whitespaces
    while re.match(r" ", string):
        start = start + 1
        string = entry.fullentry[start:end]

    match_period = re.search(r"\. *$", string)
    if match_period:
        end = end - len(match_period.group(0))
        string = entry.fullentry[start:end]
    string = re.sub(u"\([CPUD]\)", "", string)
    
    functions.insert_translation(entry, start, end)
    #entry.append_annotation(start, end, u'translation', u'dictinterpretation', string.lower())

def remove_parts_translation(str, s, e):
    start = s
    end = e
    subsubstr = str
    match_bracket_end = re.search(u"\([(CPUD)]\) ?$", subsubstr)
    if match_bracket_end:
        end = end - len(match_bracket_end.group(0))
    return [start, end]

def annotate_head_and_pos(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos']
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []

    tmp = entry.fullentry.split(u'–', 1)
    if len(tmp) > 1:
        head = tmp[0] #.strip()
    else:
        tmp = entry.fullentry.split('(pl.)', 1)
        if len(tmp) > 1:
            head = tmp[0] #.strip()

    if head != None:
        head_start = 0
        match_pos = re.search(r" ([I,\.]+ .*?) ?$", head)
        if match_pos:
            pos_start = match_pos.start(1)
            pos_end = match_pos.end(1)
            substr = entry.fullentry[pos_start:pos_end]
            start = pos_start
            for match in re.finditer(r', ?', substr):
                end = match.start(0) + pos_start
                entry.append_annotation(start, end, u'pos', u'dictinterpretation')
                start = match.end(0) + pos_start
            end = pos_end
            entry.append_annotation(start, end, u'pos', u'dictinterpretation')
            head_end = match_pos.start(1) - 1
        else:
            head_end = len(head)
        substr = entry.fullentry[head_start:head_end]
        start = head_start
        for match in re.finditer(r' ?[/,;] ?', substr):
            end = match.start(0) + head_start
            match_bracket_end = re.search(r' ?\([DU]\) ?', entry.fullentry[start:end])
            if match_bracket_end:
                end = end - len(match_bracket_end.group(0))
            inserted_head = functions.insert_head(entry, start, end)
            #entry.append_annotation(start, end, u'head', u'dictinterpretation')
            heads.append(inserted_head)
            start = match.end(0) + head_start
        end = head_end
        match_bracket_end = re.search(r' ?(?:\([DU]\)|\(pl\.\)|\(SD\)) ?$', entry.fullentry[start:end])
        if match_bracket_end:
            end = end - len(match_bracket_end.group(0))
        
        inserted_head = ""
        if re.search(u"__ \(SD\) __", entry.fullentry[start:end]):
            string_head = re.sub(u" \(SD\) ", " ", entry.fullentry[start:end])
            inserted_head = functions.insert_head(entry, start, end, string_head)
        else:
            inserted_head = functions.insert_head(entry, start, end)
        #entry.append_annotation(start, end, u'head', u'dictinterpretation')
        heads.append(inserted_head)
        
    return heads

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_starts = []
    translation_ends = []

    match_dash = re.search(u' ?– ?', entry.fullentry)
    if match_dash:
        substr = entry.fullentry
        nl_annotations = [ a for a in entry.annotations if a.value=='newline']
        for a in nl_annotations:
            if (substr[a.start-1] == ')') and (substr[a.start] == ' '):
                substr = substr[:a.start] + u',' + substr[a.start+1:]
                
        substr = re.sub(r',( ?\(.*?\))', ' \1', substr)
        substr = substr[match_dash.end(0):len(entry.fullentry)]

        #translation_starts.append(match_dash.end(0))
        #translation_ends.append(len(entry.fullentry))
        #entry.append_annotation(match.end(0), len(entry.fullentry), u'translation', u'dictinterpretation')
        start = match_dash.end(0)
        for match in re.finditer(r'[,;] ?', substr):
            end = match.start(0) + match_dash.end(0)
            subsubstr = entry.fullentry[start:end]
            a = remove_parts_translation(subsubstr, start, end)
            insert_translation(entry, a[0], a[1])
            start = match.end(0) + match_dash.end(0)
        end = len(entry.fullentry)
        subsubstr = entry.fullentry[start:end]
        a = remove_parts_translation(subsubstr, start, end)
        insert_translation(entry, a[0], a[1])

def main(argv):
    bibtex_key = u"leach1969"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=105,pos_on_page=16).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head_and_pos(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translations(e)
            annotate_dialect(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

    #for e in manual_entries:
    #    dictdata = model.meta.Session.query(model.Dictdata).join(
    #        (model.Book, model.Dictdata.book_id==model.Book.id)
    #        ).filter(model.Book.bibtex_key==bibtex_key).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(e["startpage"])).first()
    #    
    #    entry_db = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
    #    ratio = difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio()
    #    if ratio > 0.80:
    #        entry_db.fullentry = e["fullentry"].decode('utf-8')
    #        # delete all annotations in db
    #        for a in entry_db.annotations:
    #            Session.delete(a)
    #        # insert new annotations
    #        for a in e["annotations"]:
    #            entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
    #    else:
    #        print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem. (ratio: %f)" % (e["startpage"], e["pos_on_page"], ratio)

    Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)