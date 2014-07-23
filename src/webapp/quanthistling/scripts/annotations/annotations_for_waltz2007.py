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

def find_brackets(entry):
    result = []
    for match in re.finditer('\([^\)]*\)', entry.fullentry):
        result.append( (match.start(), match.end()) )
    return lambda x: bool( [1 for y in result if y[0] < x and  x < y[1]-1] )

def is_number_string(s):
    try:
        _ = int(s)
        return True
    except ValueError:
        return False

def annotate_heads(entry):
    heads = []
    #collect all bold parts up to the first italic part
    bold = functions.get_list_bold_ranges(entry)
    italic = functions.get_first_italic_range(entry)
    bold = [x for x in bold if x[1]<=italic[0]]

    #split bold parts on ',' and insert heads
    for start, end in bold:
        part = entry.fullentry[start:end]
        for match in re.finditer('([^,]*)(,|$)', part):
            #skip bold numbers
            if is_number_string(match.group(1)):
                continue
            head = functions.insert_head(entry, start+match.start(1), start+match.end(1))
            if head:
                heads.append(head)
    return heads

def remove_parts(entry, s, e):
    start = s
    end = e
    string = entry.fullentry[start:end]
    # remove whitespaces
    while re.match(r" ", string):
        start = start + 1
        string = entry.fullentry[start:end]

    match_period = re.search(r"\.? *$", string)
    if match_period:
        end = end - len(match_period.group(0))
        string = entry.fullentry[start:end]

    if re.match(u"[¿¡]", string):
        start = start + 1
        string = entry.fullentry[start:end]

    if re.search(u"[!?]$", string):
        end = end - 1
        string = entry.fullentry[start:end]

    if re.match(u"\(", string) and re.search(u"\)$", string) and not re.search(u"[\(\)]", string[1:-1]):
        start = start + 1
        end = end - 1        
        string = entry.fullentry[start:end]

    string = string.replace('!', '')
    string = string.replace('?', '')
    return (start, end, string)

trans_end_regex = re.compile(u'sino\u0301n|ej\.')
def search_translation_end(entry, start, end):
    match = trans_end_regex.search(entry.fullentry, start)
    if match is None or match.start() >= end:
        return end
    return match.start()

def insert_translation(entry, start, end):
    #print entry.fullentry[start:end]
    end = search_translation_end(entry, start, end)
    start, end, string = remove_parts(entry, start, end)
    #print string
    functions.insert_translation(entry, start, end, string)
    
def annotate_everything(entry):
    # delete annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)

    in_brackets = find_brackets(entry)
    
    heads = annotate_heads(entry)
        
    # parts of speech    
    pos_se = functions.get_first_italic_range(entry)
    if pos_se:
        pos = entry.fullentry[pos_se[0]:pos_se[1]]
        functions.insert_pos(entry, pos_se[0], pos_se[1], pos)
    else:
        functions.print_error_in_entry(entry, "No part of speech (1)")
  
    # translations
    num_list = []
    for n in re.finditer(u' \d ', entry.fullentry):
        num_list.append(n.end())
    
    num_list_bpe = []
    if num_list:
        num_list_bpe = [a for a in num_list if a > pos_se[1]]
        
    dot_list = []
    for d in re.finditer(u'\.', entry.fullentry):
        #print d.start()
        dot_list.append(d.start())
    
    dot_list_bpe = []
    if dot_list:
        try:
            dot_list_bpe = [a for a in dot_list if a > pos_se[1]]
        except:
            functions.print_error_in_entry(entry, "No part of speech (2)")
            
    comma_list = []
    for com in re.finditer(r'(,|;)', entry.fullentry):
        if not in_brackets(com.start()):
            comma_list.append(com.start())
    
    comma_list_bpe = []
    if comma_list:
        try:
            comma_list_bpe = [a for a in comma_list if a > pos_se[1] and a < dot_list_bpe[0]]
        except:
            functions.print_error_in_entry(entry, "No part of speech (3)")
    
    num_dot_list = []
 
    if num_list_bpe:
        num_dot_list.append(dot_list_bpe[0])
        prev = 0
        for x in num_list_bpe[1:]:
            for y in dot_list_bpe[1:]:
                if x < y and x > prev:
                    prev = y
                    num_dot_list.append(prev) 
    
    num_comma_list = []
        
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
                        insert_translation(entry, trans_s, trans_e)
                        
                        trans2_s = num_comma_list[0] + 2
                        if j + 1 < len(num_comma_list):
                            trans2_e = num_comma_list[j+1]
                            insert_translation(entry, trans2_s, trans2_e)
                        else:
                            insert_translation(entry, trans2_s, num_dot_list[i])
                        
                    else:
                        trans_s = num_comma_list[j] + 2
                        if j + 1 < len(num_comma_list):
                            trans_e = num_comma_list[j+1]
                            insert_translation(entry, trans_s, trans_e)
                        else:
                            insert_translation(entry, trans_s, num_dot_list[i])
            else:
                trans_s = num_list_bpe[i]
                try:
                    trans_e = num_dot_list[i]
                    insert_translation(entry, trans_s, trans_e)
                except Exception, e:
                    functions.print_error_in_entry(entry, e)
                
    
    elif comma_list_bpe and not num_list_bpe:
        for i in range(len(comma_list_bpe)):
            if i == 0:
                trans_s = pos_se[1] + 1
                trans_e = comma_list_bpe[i]
                insert_translation(entry, trans_s, trans_e)
                
                trans2_s = comma_list_bpe[0] + 2
                if i + 1 < len(comma_list_bpe):
                    trans2_e = comma_list_bpe[i+1]
                    insert_translation(entry, trans2_s, trans2_e)
                else:
                    insert_translation(entry, trans2_s, dot_list_bpe[0])
            else:
                trans_s = comma_list_bpe[i] + 2
                if i + 1 < len(comma_list_bpe):
                    trans_e = comma_list_bpe[i+1]
                    insert_translation(entry, trans_s, trans_e)
                else:
                    insert_translation(entry, trans_s, dot_list_bpe[0])
    else:
        try:
            insert_translation(entry, pos_se[1] + 1, dot_list_bpe[0])
        except:
            functions.print_error_in_entry(entry, "No translation found")

    return heads


def main(argv):

    bibtex_key = u"waltz2007"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=26,pos_on_page=1).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=13,pos_on_page=1).all()

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
