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
    
def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
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
        s = start
        for match in re.finditer(u"(?:\)?[,;] ?| ?\(|\)? ?$)", entry.fullentry[start:end]):
            e = start + match.start(0)
            # remove brackets
            string = entry.fullentry[s:e]
            if re.match(u"\(", string) and re.search(u"\)$", string) and not re.search(u"[\(\)]", string[1:-1]):
                s = s + 1
                e = e - 1
                
            # remove hyphens
            head = re.sub(u"[\-\-]", u"", entry.fullentry[s:e])
            inserted_head = functions.insert_head(entry, s, e, head)
            if inserted_head != None:
                heads.append(inserted_head)
            s = start + match.end(0)

    if len(heads) == 0:
        print "no head found for entry: " + entry.fullentry.encode('utf-8')
        
    return heads

def annotate_pos_and_crossrefs(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos' or a.value=="crossref"]
    for a in pos_annotations:
        Session.delete(a)
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    if len(sorted_annotations) > 0:
        head_end = functions.get_head_end(entry)
        if sorted_annotations[0].start <= head_end + 3:
            italic_annotation = sorted_annotations[0]
            match_crossref = re.match(u" ?[Ii]s\. ", entry.fullentry[italic_annotation.start:italic_annotation.end])
            if match_crossref:
                start = italic_annotation.start + len(match_crossref.group(0))
                for match in re.finditer(u"(?:[;,] ?|$)", entry.fullentry[start:italic_annotation.end]):
                    end = italic_annotation.start + len(match_crossref.group(0)) + match.start(0)
                    if entry.fullentry[end-1] == ".":
                        end = end - 1
                    entry.append_annotation(start, end, u'crossref', u'dictinterpretation')
                    start = italic_annotation.start + len(match_crossref.group(0)) + match.end(0)                    
            else:
                end = italic_annotation.end
                match_bracket = re.search(u"\([^)]*\) ?$", entry.fullentry[italic_annotation.start:end])
                if match_bracket:
                    end = end - len(match_bracket.group(0))
                entry.append_annotation(italic_annotation.start, end, u'pos', u'dictinterpretation')
    else:
        return

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
            functions.insert_translation(entry, start, end, translation)
            start = match.end(0) + trans_start

def annotate_examples(entry): 
    # delete pos annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    trans_end = functions.get_translation_end(entry)
    re_ex = re.compile(r'[.!?] ?(.*?) ?\= ?(.*?)(?=[.?!])')
    
    for match in re_ex.finditer(entry.fullentry, trans_end):
        entry.append_annotation(match.start(1), match.end(1), u'example-src', u'dictinterpretation', entry.fullentry[match.start(1):match.end(1)].lower())
        entry.append_annotation(match.start(2), match.end(2), u'example-tgt', u'dictinterpretation', entry.fullentry[match.start(2):match.end(2)].lower())       


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

        print "Processing %s - %s dictdata..." %(dictdata.src_language.langcode, dictdata.tgt_language.langcode)

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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=380,pos_on_page=4).all()
        
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
            annotate_examples(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
    
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)