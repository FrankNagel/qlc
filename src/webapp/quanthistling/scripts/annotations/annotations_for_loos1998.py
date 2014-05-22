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
    str_head = entry.fullentry[start:end]
    if str_head.startswith(" "):
        start += 1
    if str_head.endswith(" "):
        end -= 1

    str_head = entry.fullentry[start:end]
    if str_head.startswith("-"):
        entry.append_annotation(start, start+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
        start += 1
    if str_head.endswith("-"):
        entry.append_annotation(end-1, end, u'boundary', u'dictinterpretation', u"morpheme boundary")
        end -= 1

    return functions.insert_head(entry, start, end)


def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
    
    heads = []
    head_start = 0
    head_end = functions.get_last_bold_pos_at_start(entry)

    com_heads = []
    for com in re.finditer(r'(,|;| )', entry.fullentry):
        com_heads.append(com.start())
    
    comma_heads = [ a for a in com_heads if a < head_end ] 
    
    if comma_heads:
        for i in range(len(comma_heads)):
            if i == 0:
                h_s = 0
                h_e = comma_heads[i]
                h1 = insert_head(entry, h_s, h_e)
                
                h2_s = comma_heads[0] + 1
                if i + 1 < len(comma_heads):
                    h2_e = comma_heads[i+1]
                    h2 = insert_head(entry, h2_s, h2_e)
                else:
                    h2 = insert_head(entry, h2_s, head_end)
            else:
                h_s = comma_heads[i] + 1
                if i + 1 < len(comma_heads):
                    h_e = comma_heads[i+1]
                    head = insert_head(entry, h_s, h_e)
                else:
                    head = insert_head(entry, h_s, head_end)
    else:
        insert_head(entry, head_start, head_end)
    
    # pos
    match_cr = re.search(u' Véase (.*)', entry.fullentry)
    if match_cr:
        pass
    else:
        try:
            match_pos = re.search(u'( (adj\.|adv\.|interj\.|interr\.|part\.|posp\.|pref\.|pron\.|pron\.pos\.|s\.|suf\.(adv\.|adj\.|pron\.|n(\.)?|v\.(n\.)?gr\.\d(\.)?)|v\.a\.|v\.n\.|v\.r\.)+? ?)', entry.fullentry)
            if match_pos:
                functions.insert_pos(entry, match_pos.start(2), match_pos.end(2))
                tr_start = match_pos.end(2) + 1
            else:
                tr_start = head_end + 1
            
            # translations
            italic_ranges = [ a for a in entry.annotations if a.value=='italic']
            italic_ranges = sorted(italic_ranges, key=attrgetter('start'))
            
            c_list = []
        
            if len(italic_ranges) > 1:
                for s in italic_ranges:
                    if s.start > tr_start:
                        tr_start = s.start
                        tr_end = s.end
                        tr_tmp = entry.fullentry[tr_start:tr_end]
                        for com in re.finditer(u'(,|;)', tr_tmp):
                            comma = True
                            # comma between brackets?
                            for match_bracket in re.finditer(u'\(.*?\)', tr_tmp):
                                if com.start() > match_bracket.start() and com.start() < match_bracket.end():
                                    comma = False
                            
                            if comma:
                                c_list.append(com.start() + tr_start)
                        
                        if c_list:
                            for i in range(len(c_list)):
                                if i == 0:
                                    trans_e = c_list[i]
                                    functions.insert_translation(entry, tr_start, trans_e)
                                
                                    trans2_s = c_list[0] + 2
                                    if i + 1 < len(c_list):
                                        trans2_e = c_list[i+1]
                                        functions.insert_translation(entry, trans2_s, trans2_e)
                                    else:
                                        functions.insert_translation(entry, trans2_s, tr_end)
                                        c_list = []
                                else:
                                    trans_s = c_list[i] + 2
                                    if i + 1 < len(c_list):
                                        trans_e = c_list[i+1]
                                        functions.insert_translation(entry, trans_s, trans_e)
                                    else:
                                        functions.insert_translation(entry, trans_s, tr_end)
                                        c_list = []
                        else:
                            functions.insert_translation(entry, tr_start, tr_end)
        
            elif len(italic_ranges) == 1:
                tr_end = italic_ranges[0].end
                tr_tmp = entry.fullentry[tr_start:tr_end]
                for com in re.finditer(u'(;|,)', tr_tmp):            
                    comma = True
                    # comma between brackets?
                    for match_bracket in re.finditer(u'\(.*?\)', tr_tmp):
                        if com.start() > match_bracket.start() and com.start() < match_bracket.end():
                            comma = False
                    
                    if comma:
                        c_list.append(com.start() + tr_start)
                    
                if c_list:                        
                    for i in range(len(c_list)):
                        if i == 0:
                            trans_e = c_list[i]
                            functions.insert_translation(entry, tr_start, trans_e)
                        
                            trans2_s = c_list[0] + 2
                            if i + 1 < len(c_list):
                                trans2_e = c_list[i+1]
                                functions.insert_translation(entry, trans2_s, trans2_e)
                            else:
                                functions.insert_translation(entry, trans2_s, tr_end)
                        else:
                            trans_s = c_list[i] + 2
                            if i + 1 < len(c_list):
                                trans_e = c_list[i+1]
                                functions.insert_translation(entry, trans_s, trans_e)
                            else:
                                functions.insert_translation(entry, trans_s, tr_end)
                else:
                    functions.insert_translation(entry, tr_start, tr_end)
        except:
            functions.print_error_in_entry(entry)
    
    return heads

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    for match_vea in re.finditer(u' Véase (.*)', entry.fullentry):
        #entry.append_annotation(match.start(1), match.end(1), u'crossreference', u'dictinterpretation')
        crossref_start = match_vea.start(1)
        crossref_end = match_vea.end(1)
        #print crossref_start, crossref_end
        substr = entry.fullentry[crossref_start:crossref_end]
        start = crossref_start
        for match in re.finditer(r'[,] ?', substr):
            end = match.start(0) + crossref_start
            entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
            start = match.end(0) + crossref_start
        end = crossref_end
        entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
 
def main(argv):

    bibtex_key = u"loos1998"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=72,pos_on_page=8).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_crossrefs(e)    
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
