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

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=="boundary" or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)
    heads = []
    
    match = re.search(u' ?- (Suf[nv]|CIN): ?([^;]*;)', entry.fullentry)

    head_starts = []
    head_ends = []
    translation_starts = []
    translation_ends = []
    
    if match:
        s = 0
        if entry.fullentry[0] == "{":
            s = 1

        e = match.start(0)
        if entry.fullentry[match.start(0)-1] == "}":
            e = match.start(0) - 1


        start = s
        for match_head in re.finditer(r" ?(?:,|/|$) ?", entry.fullentry[s:e]):
            end = s + match_head.start(0)
            head_starts.append(start)
            head_ends.append(end)
            start = s + match_head.end(0)
            head_starts.append(start)
            head_ends.append(end)
        
#        if re.match(u"CIN:", match.group(1)):
        translation_starts.append(match.start(2))
        translation_ends.append(match.end(2))            
        
        trans_start = 0
        trans_end = 0
        for a in entry.annotations:
            if a.value == "bold" and a.start > e:
                trans_end = a.start
                if trans_start > 0:
                    translation_starts.append(trans_start)
                    translation_ends.append(trans_end)
                
                
                head_starts.append(a.start)
                head_ends.append(a.end)
                trans_start = a.end
        if trans_start > 0:
            translation_starts.append(trans_start)
            translation_ends.append(len(entry.fullentry))
        entry.append_annotation(match.start(1), match.end(1), u'pos', u'dictinterpretation')
    else:
        match = re.search(u"([^-]*)- ?([^,]{0,6}),? ?(.*?; ?(?=también|sinón|cf\.)|[^/]*(?=/)|[^;]*(?=;)|.*$)", entry.fullentry)
        if match:
            start = match.start(1)
            for match_head in re.finditer(r" ?(?:\(|,|/|\)? ?$)", entry.fullentry[match.start(1):match.end(1)]):
                end = match.start(1) + match_head.start(0)
                head_starts.append(start)
                head_ends.append(end)
                start = match.start(1) + match_head.end(0)
            
            #Match position on translations
            start = match.start(3)
            print start, match.end(3)
            match_sc = re.search(u';', entry.fullentry[match.start(3):match.end(3)])
            if match_sc:
                t_end = match_sc.end() + start
                print t_end
                for match_trans in re.finditer(r"(?:, ?|$)", entry.fullentry[match.start(3):t_end]):
                    end = match.start(3) + match_trans.start(0)
                    translation_starts.append(start)
                    translation_ends.append(end)
                    start = match.start(3) + match_trans.end(0)
            else:
                for match_trans in re.finditer(r"(?:, ?|$)", entry.fullentry[match.start(3):match.end(3)]):
                    end = match.start(3) + match_trans.start(0)
                    translation_starts.append(start)
                    translation_ends.append(end)
                    start = match.start(3) + match_trans.end(0)
            if len(match.group(2)) > 0:
                entry.append_annotation(match.start(2), match.end(2), u'pos', u'dictinterpretation')
        else:
            functions.print_error_in_entry(entry, "could not parse entry")
            

    for i in range(len(head_starts)):
        head = entry.fullentry[head_starts[i]:head_ends[i]]
        match_boundary = re.match("- ?", head)
        if match_boundary:
            entry.append_annotation(head_starts[i], head_starts[i] + len(match_boundary.group(0)), u'boundary', u'dictinterpretation', u"morpheme boundary")
            head = re.sub("^- ?", "", head)
        inserted_head = functions.insert_head(entry, head_starts[i], head_ends[i], head)
        if inserted_head != None:
            heads.append(inserted_head)
        
    for i in range(len(translation_starts)):
        s = translation_starts[i]
        e = translation_ends[i]
        match_parts = re.search(r"[,;.] ?", entry.fullentry[s:e])
        if match_parts:
            e = e - len(match_parts.group(0))
        translation = entry.fullentry[s:e]
        translation = re.sub(u"[‘’'!¡¿?]", u"", translation)
        functions.insert_translation(entry, s, e, translation)

    return heads

def main(argv):
    bibtex_key = u"preuss1994"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=797,pos_on_page=20).all()

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