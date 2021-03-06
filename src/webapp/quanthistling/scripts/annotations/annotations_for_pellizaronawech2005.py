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

def insert_head(entry, head_s, head_e):
    for m in re.finditer("-", entry.fullentry[head_s:head_e]):
        entry.append_annotation(head_s + m.start(0), head_s + m.end(0), u'boundary', u'dictinterpretation', u"morpheme boundary")

    heads = []
    for (s, e) in functions.split_entry_at(entry, r"(?:, |$)", head_s, head_e):
        head = entry.fullentry[s:e]
        head = re.sub(u"[¿?¡!\(\)\-\.]", u"", entry.fullentry[s:e])
        head = re.sub("[-\.]", "", head)
        inserted_head = functions.insert_head(entry, s, e, head)
        if inserted_head is not None:
            heads.append(inserted_head)

    return heads

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value in ['head', 'doculect', 'iso-639-3', 'boundary'] ]
    for a in head_annotations:
        Session.delete(a)
    
    heads = []

    start = 0
    end = 0

    head_end = functions.get_last_bold_pos_at_start(entry)
    if head_end > 0:
        start = 0
        end = head_end
        match = re.match(u' ?[\+\-\*▪•®] ?', entry.fullentry[start:end])
        if match:
            start = start + match.end(0)
    else:
        pattern = re.compile(u' ?=')
        match_transstart = pattern.search(entry.fullentry)
        if match_transstart:
            transstart = match_transstart.start(0)
        else:
            transstart = len(entry.fullentry)
        first_italic = functions.get_first_italic_start_in_range(entry, 0, len(entry.fullentry))
        if first_italic == -1:
                first_italic = len(entry.fullentry)
        
        if transstart < first_italic:
            first_italic = transstart

        if first_italic < len(entry.fullentry):
            start = 0
            end = first_italic
            match = re.match(u' ?[\+\-\*▪•®] ?', entry.fullentry[start:end])
            if match:
                start = start + match.end(0)

    if end > 0:
        substr = entry.fullentry[start:end]
        match_stratum = re.search("\(del (?:cast\.|quechua)\) ?$", substr)
        if match_stratum:
            end = end - len(match_stratum.group(0))
            substr = entry.fullentry[start:end]
            if "quechua" in match_stratum.group(0):
                entry.append_annotation(start + match_stratum.start(0), end, u"stratum", u"dictinterpretation", u"Quechua")
            else:
                entry.append_annotation(start + match_stratum.start(0), end, u"stratum", u"dictinterpretation", u"Spanish")
            
        s = start
        for match in re.finditer(u"(?:\)?[,;] ?| ?\(|\)? ?$)", substr):
            mybreak = False
            # are we in a bracket?
            for m in re.finditer(r'\([^)]*\)', substr):
                #print m.start(0)
                #print match.start(0)
                if match.start(0) >= m.start(0) and match.end(0) <= m.end(0):
                    mybreak = True
                
            if not mybreak:
                e = start + match.start(0)
                # remove brackets
                string = entry.fullentry[s:e]
                if re.match(u"\(", string) and re.search(u"\)$", string) and not re.search(u"[\(\)]", string[1:-1]):
                    s = s + 1
                    e = e - 1
                    
                inserted_heads = insert_head(entry, s, e)
                if len(inserted_heads) > 0:
                    heads += inserted_heads
                s = start + match.end(0)

    if len(heads) == 0:
        print "no head found for entry: " + entry.fullentry.encode('utf-8')
        
    return heads

def annotate_pos_and_crossrefs(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value in ['pos', 'crossref'] ]
    for a in pos_annotations:
        Session.delete(a)
        entry.annotations.remove(a) #make sure entry.annotations is in sync with db; later i'll check for multi
                                    #detected crossrefs (italic and between examples)
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    head_end = functions.get_head_end(entry)
    for italic_annotation in sorted_annotations:
        match_crossref = re.match(u" ?[Ii]s[., ]+", entry.fullentry[italic_annotation.start:italic_annotation.end])
        if match_crossref:
            start = italic_annotation.start + len(match_crossref.group(0))
            for match in re.finditer(u"(?:[;,.] ?|$)", entry.fullentry[start:italic_annotation.end]):
                end = italic_annotation.start + len(match_crossref.group(0)) + match.start(0)
                if entry.fullentry[end-1] == ".":
                    end = end - 1
                if start < end:
                    entry.append_annotation(start, end, u'crossref', u'dictinterpretation')
                start = italic_annotation.start + len(match_crossref.group(0)) + match.end(0)                    
        elif italic_annotation.start <= head_end + 3:
            end = italic_annotation.end
            it_text = entry.fullentry[italic_annotation.start:end]
            match_bracket = re.search(u"\([^)]*\) ?$", it_text) #central part of the old strategy
            br_index = it_text.find('(')
            if br_index != -1:
                while br_index > -1 and it_text[br_index-1].isspace():
                    br_index -= 1
                end = italic_annotation.start + br_index
                #create Log output for different bracket handling
                #if not match_bracket or br_index != match_bracket.start():
                #    functions.print_error_in_entry(entry, 'INFO: different bracket handling from svn332')
            entry.append_annotation(italic_annotation.start, end, u'pos', u'dictinterpretation')


def annotate_translations(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    match_first_equal  = None
    for match in re.finditer(u"=", entry.fullentry):
        inbracket = False
        for m in re.finditer(r'\([^)]*\)', entry.fullentry):
            if match.start(0) > m.start(0) and match.start(0) < m.end(0):
                inbracket = True
                break
        if not inbracket:
            match_first_equal = match
            break

    if not match_first_equal:
        functions.print_error_in_entry(entry, "no equal sign, no translation")
        return
        
    re_trans = re.compile(r"\= ?((?:[^.?!(]*\([^)]*\)[^.!?(]*)+|[^\.!?]*)[?!.]")
    match_trans = re_trans.search(entry.fullentry, match_first_equal.start(0))

    if not match_trans:
        re_trans2 = re.compile(r'\= ?(.*?)$')
        match_trans = re_trans2.search(entry.fullentry, match_first_equal.start(0))
    
    if not match_trans:
        functions.print_error_in_entry(entry, "no translation found")

    trans_start = match_trans.start(1)
    trans_end = match_trans.end(1)
    substr = entry.fullentry[trans_start:trans_end]

    start = trans_start
    for match in re.finditer(r'(?:[,;] ?|$)', substr):
        mybreak = False
        # are we in a bracket?
        for m in re.finditer(r'\(.*?\)', substr):
            if match.start(0) > m.start(0) and match.end(0) < m.end(0):
                mybreak = True
                
        if not mybreak:
            end = match.start(0) + trans_start
            match_arrow = re.match(u" ??[➱⇨] ?", entry.fullentry[start:end])
            if match_arrow:
                start = start + len(match_arrow.group(0))
            translation = entry.fullentry[start:end]
            match_nombre = re.match(u"nombre de [^(]+ \((?:= )?([^)]+)\)", translation)
            if match_nombre:
                translation = match_nombre.group(1)
                
            match_ending = re.search(r"/(a|o|as|do)\b", translation)
            if match_ending:
                translation2 = translation[:match_ending.start(0)] + translation[match_ending.end(0):]
                functions.insert_translation(entry, start, end, translation2)
                translation2 = translation[:match_ending.start(0)-len(match_ending.group(1))] + match_ending.group(1) + translation[match_ending.end(0):]
                functions.insert_translation(entry, start, end, translation2)
            else:
                functions.insert_translation(entry, start, end, translation)
            start = match.end(0) + trans_start


def _already_known(annotations, start, end):
    for a in annotations:
        upper = min(end, a.end)
        lower = max(start, a.start)
        if upper > lower:
            return True
    return False

def annotate_examples_and_crossrefs(entry): 
    # delete pos annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    trans_end = functions.get_translation_end(entry)

    #crossrefs are sometimes mixed with examples. Crossrefs in italic will be known already.
    known_crossrefs = [a for a in entry.annotations if a.value == 'crossref']
    
    #process examples and crossrefs
    re_ex = re.compile(r'[.!?] ?(.*?) ?\= ?(.*?)(?=[.?!])')
    re_crossref = re.compile(r'\s*[.!?]?\s*[(]?\s*[Ii]s[.]?\s*([^.]*)\s*[)]?(?=[.])')
    oldpos = -1
    pos = trans_end
    while oldpos != pos:
        oldpos = pos
        cr_match = re_crossref.match(entry.fullentry, pos)
        if cr_match:
            if not _already_known(known_crossrefs, cr_match.start(1), cr_match.end(1)):
                entry.append_annotation(cr_match.start(1), cr_match.end(1), u'crossref', u'dictinterpretation')
            pos = cr_match.end()
            continue
        ex_match = re_ex.match(entry.fullentry, pos)
        if ex_match:
            match_suspect = re.search(u"[Ii]s\.", entry.fullentry[ex_match.start():ex_match.end()])
            if match_suspect:
                functions.print_error_in_entry(entry, "WARN: '[Ii]s' in examples.")
            entry.append_annotation(ex_match.start(1), ex_match.end(1), u'example-src', u'dictinterpretation',
                                    entry.fullentry[ex_match.start(1):ex_match.end(1)].lower())
            entry.append_annotation(ex_match.start(2), ex_match.end(2), u'example-tgt', u'dictinterpretation',
                                    entry.fullentry[ex_match.start(2):ex_match.end(2)].lower())
            pos = ex_match.end()


def main(argv):
    bibtex_key = u"pellizaronawech2005"
    
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

        #print "Processing %s - %s dictdata..." %(dictdata.src_language.langcode, dictdata.tgt_language.langcode)

        # manual deletes
        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=154).all()
        for e in entries:
            if e.pos_on_page >= 9 and e.pos_on_page <= 15:
                for a in e.annotations:
                    Session.delete(a)
                Session.delete(e)
        entry = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=218,pos_on_page=31).first()
        if entry:
            for a in entry.annotations:
                Session.delete(a)
            Session.delete(entry)
        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=301).all()
        for e in entries:
            if e.pos_on_page >= 10 and e.pos_on_page <= 15:
                for a in e.annotations:
                    Session.delete(a)
                Session.delete(e)
        Session.commit()


        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=194,pos_on_page=5).all()

        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos_and_crossrefs(e)
            #Session.commit()
            annotate_translations(e)
            #annotate_crossrefs(e)
            #annotate_dialect(e)
            annotate_examples_and_crossrefs(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
    
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
