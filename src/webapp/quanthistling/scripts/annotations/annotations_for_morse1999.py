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
    head = entry.fullentry[start:end]
    head = re.sub("[* ]*$", "", head)
    head = functions.insert_head(entry, start, end, head)
    return head


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
    match = re.match(u'(\w+.*)\d+\.', head_tmp)
      
    # remove numbers at end of head
    if match:
        head_tmp = match.group(1)
        head_end_tmp = head_end_tmp - 3
    
    sep_list = []
    for c in re.finditer(r',', head_tmp):
        sep_list.append(c.start())
    
    if sep_list:
        for i in range(len(sep_list)):
            if i == 0:
                head_start = 0
                head_end = sep_list[i]
                head = insert_head(entry, head_start, head_end)
                
                head2_start = sep_list[0] + 2
                if i + 1 < len(sep_list):
                    head2_end = sep_list[1]
                    head = insert_head(entry, head2_start, head2_end)
                    i += 1
                else:
                    head = insert_head(entry, head2_start, head_end_tmp)
            else:
                head_start = sep_list[i] + 2
                if i + 1 < len(sep_list):
                    head_end = sep_list[i+1]
                    head = insert_head(entry, head_start, head_end)
                    i += 1
                else:
                    head = insert_head(entry, head_start, head_end_tmp)   
    else:
        head = insert_head(entry, 0, head_end_tmp)
        heads.append(head)  
    
    
    # parts of speech
    pos_se = functions.get_first_italic_range(entry)
    pos = entry.fullentry[pos_se[0]:pos_se[1]]
    functions.insert_pos(entry, pos_se[0], pos_se[1], pos)   
  
    # translations
    num_list = []
    for n in re.finditer(u' \d\.', entry.fullentry):
        num_list.append(n.end())
    
    dot_list = []
    for d in re.finditer(u'\.', entry.fullentry):
        #print d.start()
        dot_list.append(d.start())
    
    comma_list = []
    for com in re.finditer(r'(,|;)', entry.fullentry):
        is_in_bracket = False
        for bracket in re.finditer("\([^)]*\)", entry.fullentry):
            if bracket.start(0) < com.start(0) and bracket.end(0) > com.start(0):
                is_in_bracket = True
        if not is_in_bracket:
            comma_list.append(com.start())
    
    num_comma_list = []
    num_dot_list = []
    
    match_clas = re.search(u'\(clas\. \-(\W|\w)+?\) ', entry.fullentry, re.U)
    if match_clas:
        #print match_clas.group()
        t_start = match_clas.end()
        #print t_start
        
        num_list_clas = []
        if num_list:
            num_list_clas = [a for a in num_list if a > t_start]
            
        dot_list_clas = [a for a in dot_list if a > t_start]
        
        comma_list_clas = [a for a in comma_list if a > t_start and a < dot_list_clas[0]]
        
        if num_list_clas:
            for v in num_list_clas:
                if v - 1 in dot_list_clas:
                    try:
                        num_dot_list.append(dot_list[dot_list.index(v - 1) + 1])
                    except:
                        print functions.print_error_in_entry(entry)
    
        if num_list_clas:
            for i in range(len(num_list_clas)):
                start = num_list_clas[i]
                end = num_dot_list[i]
                num_comma_list = [ a for a in comma_list if a < end and a > start]
                if num_comma_list:
                    for j in range(len(num_comma_list)):
                        if j == 0:
                            trans_s = start
                            trans_e = num_comma_list[j]
                            translation = functions.insert_translation(entry, trans_s, trans_e)
                            
                            trans2_s = num_comma_list[0] + 2
                            if j + 1 < len(num_comma_list):
                                trans2_e = num_comma_list[j+1]
                                translation = functions.insert_translation(entry, trans2_s, trans2_e)
                            else:
                                translation = functions.insert_translation(entry, trans2_s, num_dot_list[i])
                            
                        else:
                            trans_s = num_comma_list[j] + 2
                            if j + 1 < len(num_comma_list):
                                trans_e = num_comma_list[j+1]
                                translation = functions.insert_translation(entry, trans_s, trans_e)
                            else:
                                translation = functions.insert_translation(entry, trans_s, num_dot_list[i])
                else:
                    trans_s = num_list_clas[i] + 1
                    try:
                        trans_e = num_dot_list[i]
                        translation = functions.insert_translation(entry, trans_s, trans_e)
                    except:
                        print functions.print_error_in_entry(entry)
                    
        
        elif comma_list_clas and not num_list_clas:
            for i in range(len(comma_list_clas)):
                if i == 0:
                    trans_s = t_start
                    trans_e = comma_list_clas[i]
                    translation = functions.insert_translation(entry, trans_s, trans_e)
                    
                    trans2_s = comma_list_clas[0] + 2
                    if i + 1 < len(comma_list_clas):
                        trans2_e = comma_list_clas[i+1]
                        translation = functions.insert_translation(entry, trans2_s, trans2_e)
                    else:
                        translation = functions.insert_translation(entry, trans2_s, dot_list_clas[0])
                else:
                    trans_s = comma_list_clas[i] + 2
                    if i + 1 < len(comma_list_clas):
                        trans_e = comma_list_clas[i+1]
                        translation = functions.insert_translation(entry, trans_s, trans_e)
                    else:
                        translation = functions.insert_translation(entry, trans_s, dot_list_clas[0])
        else:    
            translation = entry.fullentry[t_start:dot_list_clas[0]]
            functions.insert_translation(entry, t_start, dot_list_clas[0], translation)
        
    else:
        num_list_bpe = []
        if num_list:
            num_list_bpe = [a for a in num_list if a > pos_se[1]]
            
        dot_list_bpe = [a for a in dot_list if a > pos_se[1]]
        
        comma_list_bpe = [a for a in comma_list if a > pos_se[1] and a < dot_list_bpe[0]]
        
        if num_list_bpe:
            for v in num_list_bpe:
                if v - 1 in dot_list_bpe:
                    try:
                        num_dot_list.append(dot_list[dot_list.index(v - 1) + 1])
                    except:
                        print functions.print_error_in_entry(entry)
    
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
                            translation = functions.insert_translation(entry, trans_s, trans_e)
                            
                            trans2_s = num_comma_list[0] + 2
                            if j + 1 < len(num_comma_list):
                                trans2_e = num_comma_list[j+1]
                                translation = functions.insert_translation(entry, trans2_s, trans2_e)
                            else:
                                translation = functions.insert_translation(entry, trans2_s, num_dot_list[i])
                            
                        else:
                            trans_s = num_comma_list[j] + 2
                            if j + 1 < len(num_comma_list):
                                trans_e = num_comma_list[j+1]
                                translation = functions.insert_translation(entry, trans_s, trans_e)
                            else:
                                translation = functions.insert_translation(entry, trans_s, num_dot_list[i])
                else:
                    trans_s = num_list_bpe[i] + 1
                    try:
                        trans_e = num_dot_list[i]
                        translation = functions.insert_translation(entry, trans_s, trans_e)
                    except:
                        print functions.print_error_in_entry(entry)
                    
        
        elif comma_list_bpe and not num_list_bpe:
            for i in range(len(comma_list_bpe)):
                if i == 0:
                    trans_s = pos_se[1] + 1
                    trans_e = comma_list_bpe[i]
                    translation = functions.insert_translation(entry, trans_s, trans_e)
                    
                    trans2_s = comma_list_bpe[0] + 2
                    if i + 1 < len(comma_list_bpe):
                        trans2_e = comma_list_bpe[i+1]
                        translation = functions.insert_translation(entry, trans2_s, trans2_e)
                    else:
                        translation = functions.insert_translation(entry, trans2_s, dot_list_bpe[0])
                else:
                    trans_s = comma_list_bpe[i] + 2
                    if i + 1 < len(comma_list_bpe):
                        trans_e = comma_list_bpe[i+1]
                        translation = functions.insert_translation(entry, trans_s, trans_e)
                    else:
                        translation = functions.insert_translation(entry, trans_s, dot_list_bpe[0])
        else:    
            translation = entry.fullentry[pos_se[1] + 1:dot_list_bpe[0]]
            functions.insert_translation(entry, pos_se[1] + 1, dot_list_bpe[0], translation)
    

    return heads

def main(argv):

    bibtex_key = u"morse1999"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=12).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_dialect(e)
            #annotate_pos(e)
            #annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
