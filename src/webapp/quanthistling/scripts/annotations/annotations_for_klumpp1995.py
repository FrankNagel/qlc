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
    # delete annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)
        
    # heads
    head = None
    heads = []
    
    head_end_tmp = functions.get_last_bold_pos_at_start(entry)
    head_tmp = entry.fullentry[:head_end_tmp]
               
    sep_list = []
    for c in re.finditer(r',', head_tmp):
        comma = True
        for mb in re.finditer(u'\(.*?\)', head_tmp):
            if c.start() > mb.start() and c.start() < mb.end():
                comma = False
        if comma:
            sep_list.append(c.start())
    
    if sep_list:
        for i in range(len(sep_list)):
            if i == 0:
                head_start = 0
                head_end = sep_list[i]
                functions.insert_head(entry, head_start, head_end)
                
                head2_start = sep_list[0] + 2
                if i + 1 < len(sep_list):
                    head2_end = sep_list[1]
                    functions.insert_head(entry, head2_start, head2_end)
                    i += 1
                else:
                    functions.insert_head(entry, head2_start, head_end_tmp)
            else:
                head_start = sep_list[i] + 2
                if i + 1 < len(sep_list):
                    head_end = sep_list[i+1]
                    functions.insert_head(entry, head_start, head_end)
                    i += 1
                else:
                    functions.insert_head(entry, head_start, head_end_tmp)   
    else:
        functions.insert_head(entry, 0, head_end_tmp) 
    
    # parts of speech
    pos_se = functions.get_first_italic_range(entry)
    if pos_se:
        pos = entry.fullentry[pos_se[0]:pos_se[1]]
        functions.insert_pos(entry, pos_se[0], pos_se[1], pos)
        t_start = pos_se[1] + 1
    else:
        t_start = head_end_tmp + 1
      
    # translations
    dot_list = []
    for d in re.finditer(u'\.(?!\.|\w)', entry.fullentry):
        dot = True
        for match_bracket in re.finditer(u'\(.*?\)', entry.fullentry):
            if d.start() > match_bracket.start() and d.start() < match_bracket.end():
                dot = False
        if dot:
            dot_list.append(d.start())
    
    dot_list_bpe = []
    if dot_list:
        dot_list_bpe = [a for a in dot_list if a > t_start]
    
    if dot_list_bpe:
        t_end_tmp = dot_list_bpe[0]
    else:
        t_end_tmp = len(entry.fullentry)
    
    comma_list = []
    for com in re.finditer(r'(,|;)', entry.fullentry):
        comma = True
        for match_bracket in re.finditer(u'\(.*?\)', entry.fullentry):
            if com.start() > match_bracket.start() and com.start() < match_bracket.end():
                comma = False
        if comma:
            comma_list.append(com.start())
    
    comma_list_bpe = []
    if comma_list:
        comma_list_bpe = [a for a in comma_list if a > t_start and a < t_end_tmp]
    
    num_list = []
    for n in re.finditer(r' \d.', entry.fullentry):
        num_list.append(n.end())
    
    num_list_bpe = []
    if num_list:
        num_list_bpe = [a for a in num_list if a > t_start]

    num_dot_list = []
    if num_list_bpe:
        for v in num_list_bpe:
            if v - 1 in dot_list_bpe:
                try:
                    num_dot_list.append(dot_list[dot_list.index(v - 1) + 1])
                except:
                    print 'Cannot make numbers dot list', functions.print_error_in_entry(entry)
        
        if len(num_list_bpe) != len(num_dot_list):
            print 'number of numbers and dots unequal, ', functions.print_error_in_entry(entry)
        else:
            for i in range(len(num_list_bpe)):
                start = num_list_bpe[i] + 1
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
                    trans_e = num_dot_list[i]
                    functions.insert_translation(entry, trans_s, trans_e)
              
        
    elif comma_list_bpe and not num_list_bpe:
        for i in range(len(comma_list_bpe)):
            if i == 0:
                trans_e = comma_list_bpe[i]
                functions.insert_translation(entry, t_start, trans_e)
                
                trans2_s = comma_list_bpe[0] + 2
                if i + 1 < len(comma_list_bpe):
                    trans2_e = comma_list_bpe[i+1]
                    functions.insert_translation(entry, trans2_s, trans2_e)
                else:
                    functions.insert_translation(entry, trans2_s, t_end_tmp)
                    
            else:
                trans_s = comma_list_bpe[i] + 2
                if i + 1 < len(comma_list_bpe):
                    trans_e = comma_list_bpe[i+1]
                    functions.insert_translation(entry, trans_s, trans_e)
                else:
                    functions.insert_translation(entry, trans_s, t_end_tmp)  
    else:
        functions.insert_translation(entry, t_start, t_end_tmp)
            
    return heads

def main(argv):

    bibtex_key = u"klumpp1995"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=4,pos_on_page=18).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_pos(e)
            #annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
