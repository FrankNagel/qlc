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

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
  
    #translation_end = len(entry.fullentry)

    heads = []
    head_start = 0
    head_end = functions.get_last_bold_pos_at_start(entry)

    com_heads = []
    for com in re.finditer(r'(,|;)', entry.fullentry):
        com_heads.append(com.start())
    
    comma_heads = [ a for a in com_heads if a < head_end ] 
    
    if comma_heads:
        for i in range(len(comma_heads)):
            if i == 0:
                h_s = 0
                h_e = comma_heads[i]
                h1 = functions.insert_head(entry, h_s, h_e)
                
                h2_s = comma_heads[0] + 2
                if i + 1 < len(comma_heads):
                    h2_e = comma_heads[i+1]
                    h2 = functions.insert_head(entry, h2_s, h2_e)
                else:
                    h2 = functions.insert_head(entry, h2_s, head_end)
            else:
                h_s = comma_heads[i] + 2
                if i + 1 < len(comma_heads):
                    h_e = comma_heads[i+1]
                    head = functions.insert_head(entry, h_s, h_e)
                else:
                    head = functions.insert_head(entry, h_s, head_end)
    else:
        functions.insert_head(entry, head_start, head_end)
    
    # pos
    ir = functions.get_first_italic_range(entry)
    try:
        p_start = ir[0]
        p_end = ir[1]
        pos_tmp = entry.fullentry[p_start:p_end]
        spaces = []
        for s in re.finditer(u' ', entry.fullentry):
            spaces.append(s.start())
        
        pos_spaces = [a for a in spaces if a > p_start and a < p_end]
        
        if pos_spaces:
            for i in range(len(pos_spaces)):
                if i == 0:
                    p_s = p_start
                    p_e = pos_spaces[i]
                    p1 = functions.insert_pos(entry, p_s, p_e)
                    
                    p2_s = pos_spaces[0] + 1
                    if i + 1 < len(pos_spaces):
                        p2_e = pos_spaces[i+1]
                        p2 = functions.insert_pos(entry, p2_s, p2_e)
                    else:
                        p2 = functions.insert_pos(entry, p2_s, p_end)
                else:
                    p_s = pos_spaces[i] + 1
                    if i + 1 < len(pos_spaces):
                        p_e = pos_spaces[i+1]
                        head = functions.insert_head(entry, p_s, p_e)
                    else:
                        head = functions.insert_head(entry, p_s, p_end)
        else:
            functions.insert_pos(entry, p_start, p_end)
            
        
        # translations
        t_start = p_end + 1
        t_end = len(entry.fullentry)
        
        comma_list = []
        for com in re.finditer(r'(,|;)', entry.fullentry):
            comma_list.append(com.start())
        
        comma_list_ap = [ a for a in comma_list if a > p_end ] 
    
        if comma_list_ap:
            for i in range(len(comma_list_ap)):
                    if i == 0:
                        trans_e = comma_list_ap[i]
                        functions.insert_translation(entry, t_start, trans_e)
                        
                        trans2_s = comma_list_ap[0] + 2
                        if i + 1 < len(comma_list_ap):
                            trans2_e = comma_list_ap[i+1]
                            functions.insert_translation(entry, trans2_s, trans2_e)
                        else:
                            functions.insert_translation(entry, trans2_s, t_end)
                    else:
                        trans_s = comma_list_ap[i] + 2
                        if i + 1 < len(comma_list_ap):
                            trans_e = comma_list_ap[i+1]
                            functions.insert_translation(entry, trans_s, trans_e)
                        else:
                            functions.insert_translation(entry, trans_s, t_end)    
        else:
            functions.insert_translation(entry, t_start, t_end)
    except:
        print 'no POS or POS not italic, ', functions.print_error_in_entry(entry)
    
    return heads
 
def main(argv):

    bibtex_key = u"yagkug1998"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=25,pos_on_page=20).all()

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
