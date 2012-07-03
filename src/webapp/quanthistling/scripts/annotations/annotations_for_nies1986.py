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
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=='crossreference' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)
    
    heads = []
    c_list = []
    
    h_start = 0
    h_end = functions.get_last_bold_pos_at_start(entry)
    head = entry.fullentry[h_start:h_end]
    for m in re.finditer(u',', head):
        c_list.append(m.start())
        
    if c_list:
        for i in range(len(c_list)):
            if i == 0:
                head_end = c_list[i]
                functions.insert_head(entry, h_start, head_end)
            
                head2_start = c_list[0] + 2
                if i + 1 < len(c_list):
                    head2_end = c_list[i+1]
                    functions.insert_head(entry, head2_start, head2_end)
                else:
                    functions.insert_head(entry, head2_start, h_end)
                    c_list = []
            else:
                head_start = c_list[i] + 2
                if i + 1 < len(c_list):
                    head_end = c_list[i+1]
                    functions.insert_head(entry, head_start, head_end)
                else:
                    functions.insert_head(entry, head_start, h_end)
                    c_list = []
    else:
        functions.insert_head(entry, h_start, h_end, head)
   
    # pos
    pos = False
    p_start_tmp = h_end + 1
    substr = entry.fullentry[p_start_tmp:]
    match_pos = re.search(u'\((.*?)\)', substr)
    if match_pos:
        if not re.search(u'Vea ', match_pos.group(1)):
            pos = True
    if pos:
        p_start = match_pos.start(1) + p_start_tmp
        p_end = match_pos.end(1) + p_start_tmp
        substr = entry.fullentry[p_start:p_end]
        match_c = re.search(u',', substr)
        if match_c:
            p1_end = match_c.start() + p_start_tmp + 1
            substr = entry.fullentry[p_start:p1_end]
            match_dot = re.search(u'(\.|\d)$', substr)
            if match_dot:
                functions.insert_pos(entry, p_start, p1_end)
            p2_start = p1_end + 1
            substr = entry.fullentry[p2_start:p_end]
            match_dot = re.search(u'(\.|\d)$', substr)
            if match_dot:
                functions.insert_pos(entry, p2_start, p_end)
        else:
            match_dot = re.search(u'(\.|\d)$', substr)
            if match_dot:
                functions.insert_pos(entry, p_start, p_end)
        
        t_start = p_end +  2
    else:
        t_start = h_end + 1
        pos = False
    
    # cross-references
    crossref = False
    substr = entry.fullentry[t_start:]
    if re.search(u'\(Vea .*?\)', substr):
        crossref = True
        for match_vea in re.finditer(u'\(Vea (.*?)\)', substr):
            cref_start = match_vea.start(1) + t_start
            cref_end = match_vea.end(1) + t_start
            substr = entry.fullentry[cref_start:cref_end]
            for match in re.finditer(u', ?', substr):
                end = match.start(0) + cref_start
                entry.append_annotation(cref_start, end, u'crossreference', u'dictinterpretation')
                cref_start = match.end(0) + cref_start
            entry.append_annotation(cref_start, cref_end, u'crossreference', u'dictinterpretation')
    
    # translations
    if not crossref:
        substr = entry.fullentry[t_start:]
        
        # Any numbers in front of translations?
        numbers = []
        for n in re.finditer(u'(?<!\(\w\. )\d\)', substr):
            numbers.append(n.end() + t_start)
        
        dot_list = []
        for d in re.finditer(u'\.(?!\.|\w)', substr):
            dot = True
            for match_bracket in re.finditer(u'\(.*?\)', substr):
                if d.start() > match_bracket.start() and d.start() < match_bracket.end():
                    dot = False
            if dot:
                dot_list.append(d.start() + t_start)
        
        if dot_list:
            t_end = dot_list[0]
        else:
            t_end = len(entry.fullentry)
        
        substr = entry.fullentry[t_start:t_end]
        comma_list = []
        for com in re.finditer(r'(,|;)', substr):
            comma = True
            for match_bracket in re.finditer(u'\(.*?\)', substr):
                if com.start() > match_bracket.start() and com.start() < match_bracket.end():
                    comma = False
            if comma:
                comma_list.append(com.start() + t_start)
        
        num_dot_list = []
        if numbers:
            prev = 0
            for x in numbers:
                for y in dot_list:
                    if x < y and x > prev:
                        prev = y
                        num_dot_list.append(prev) 
        
        if len(numbers) != len(num_dot_list):
            print 'Number of numbers and dots unequal, ', functions.print_error_in_entry(entry)
        
        elif numbers:
            for i in range(len(numbers)):
                start = numbers[i]
                end = num_dot_list[i]
                substr = entry.fullentry[start:end]
                num_comma_list = []
                for com in re.finditer(r'(,|;)', substr):
                    comma = True
                    for match_bracket in re.finditer(u'\(.*?\)', substr):
                        if com.start() > match_bracket.start() and com.start() < match_bracket.end():
                            comma = False
                    if comma:
                        num_comma_list.append(com.start() + start)
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
                    trans_s = numbers[i] + 1
                    trans_e = num_dot_list[i]
                    functions.insert_translation(entry, trans_s, trans_e)
                      
        elif comma_list and not numbers:
            for i in range(len(comma_list)):
                if i == 0:
                    trans_e = comma_list[i]
                    functions.insert_translation(entry, t_start, trans_e)
                    
                    trans2_s = comma_list[0] + 2
                    if i + 1 < len(comma_list):
                        trans2_e = comma_list[i+1]
                        functions.insert_translation(entry, trans2_s, trans2_e)
                    else:
                        functions.insert_translation(entry, trans2_s, t_end)
                else:
                    trans_s = comma_list[i] + 2
                    if i + 1 < len(comma_list):
                        trans_e = comma_list[i+1]
                        functions.insert_translation(entry, trans_s, trans_e)
                    else:
                        functions.insert_translation(entry, trans_s, t_end)
        else:
            functions.insert_translation(entry, t_start, t_end)
          
    return heads
 
def main(argv):

    bibtex_key = u"nies1986"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=200,pos_on_page=10).all()

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
