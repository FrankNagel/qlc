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
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation']
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
        
        pos_spaces = []
        if spaces:
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
        #t_start = p_end + 1
        #t_end = len(entry.fullentry)
        
        num_list = []
        for n in re.finditer(u' \d\.', entry.fullentry):
            num_list.append(n.end())
        
        num_list_bpe = []
        if num_list:
            num_list_bpe = [a for a in num_list if a > p_end]
            
        dot_list = []
        for d in re.finditer(u'\.', entry.fullentry):
            #print d.start()
            dot_list.append(d.start())
        
        if dot_list:
            dot_list_bpe = [a for a in dot_list if a > p_end]
        else:
            print 'Error in dot_list, ', functions.print_error_in_entry(entry)
        
        if dot_list_bpe:
            trans_end = dot_list_bpe[0]
        else:
            trans_end = len(entry.fullentry)
        
        comma_list = []
        for com in re.finditer(r'(,|;)', entry.fullentry):
            comma_list.append(com.start())
        
        comma_list_bpe = []
        if comma_list:
            comma_list_bpe = [a for a in comma_list if a > p_end and a < trans_end]
        
        num_dot_list = []
        if num_list_bpe:
            for v in num_list_bpe:
                if v - 1 in dot_list_bpe:
                    try:
                        num_dot_list.append(dot_list[dot_list.index(v - 1) + 1])
                    except:
                        print functions.print_error_in_entry(entry)
        
        num_comma_list = []
        
        if len(num_list_bpe) != len(num_dot_list):
            print 'number of numbers and dots unequal, ', functions.print_error_in_entry(entry)
            
        try:    
            if num_list_bpe:
                for i in range(len(num_list_bpe)):
                    start = num_list_bpe[i]
                    end = num_dot_list[i]
                    num_comma_list = [ a for a in comma_list if a < end and a > start]
                    if num_comma_list:
                        for j in range(len(num_comma_list)):
                            if j == 0:
                                trans_s = start
                                trans_e = num_comma_list[j]
                                functions.insert_translation(entry, trans_s, trans_e)
                                
                                trans2_s = num_comma_list[0] + 2
                                if j + 1 < len(num_comma_list):
                                    trans2_e = num_comma_list[j+1]
                                    functions.insert_translation(entry, trans2_s, trans2_e)
                                else:
                                    functions.insert_translation(entry, trans2_s, num_dot_list[i])
                                
                            else:
                                trans_s = num_comma_list[j] + 2
                                if j + 1 < len(num_comma_list):
                                    trans_e = num_comma_list[j+1]
                                    functions.insert_translation(entry, trans_s, trans_e)
                                else:
                                    functions.insert_translation(entry, trans_s, num_dot_list[i])
                    else:
                        trans_s = num_list_bpe[i] + 1
                        try:
                            trans_e = num_dot_list[i]
                            functions.insert_translation(entry, trans_s, trans_e)
                        except:
                            print functions.print_error_in_entry(entry)
                        
            
            elif comma_list_bpe and not num_list_bpe:
                for i in range(len(comma_list_bpe)):
                    if i == 0:
                        trans_s = p_end + 1
                        trans_e = comma_list_bpe[i]
                        functions.insert_translation(entry, trans_s, trans_e)
                        
                        trans2_s = comma_list_bpe[0] + 2
                        if i + 1 < len(comma_list_bpe):
                            trans2_e = comma_list_bpe[i+1]
                            functions.insert_translation(entry, trans2_s, trans2_e)
                        else:
                            functions.insert_translation(entry, trans2_s, trans_end)
                    else:
                        trans_s = comma_list_bpe[i] + 2
                        if i + 1 < len(comma_list_bpe):
                            trans_e = comma_list_bpe[i+1]
                            functions.insert_translation(entry, trans_s, trans_e)
                        else:
                            functions.insert_translation(entry, trans_s, trans_end)
            else:
                try:
                    translation = entry.fullentry[p_end + 1:trans_end]
                    functions.insert_translation(entry, p_end + 1, trans_end, translation)   
                except:
                    print 'cannot insert translation, ', functions.print_error_in_entry(entry) 
        except:
            print 'cannot annotate, ', functions.print_error_in_entry(entry)
    except:
        print 'no POS, ', functions.print_error_in_entry(entry)
        
    return heads
 
 
def main(argv):

    bibtex_key = u"ferreira2005"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=129,pos_on_page=17).all()

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
