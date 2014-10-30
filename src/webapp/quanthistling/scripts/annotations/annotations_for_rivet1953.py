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

def find_language(entry, start):
    match_lang = re.search(r"\(([ONW]).?\)", entry.fullentry[start:])
    if match_lang:
        if match_lang.group(1) == "O":
            return (u"oca", u"Okáina")
        elif match_lang.group(1) == "W":
            return (u"huu", u"Witóto")
        elif match_lang.group(1) == "N":
            return (u"noj", u"Nonuya")
    return None
            
def insert_translation(entry, start, end):
    if not re.match("^ *$", entry.fullentry[start:end]):
        lang = find_language(entry, start)
        match_lang = re.search("\([ONW].?\) *$", entry.fullentry[start:end])
        if match_lang:
            end = end - len(match_lang.group(0))
        cf_start = entry.fullentry.find('[cf.', start, end)
        if cf_start != -1:
            end = cf_start
        start, end, translation = functions.remove_parts(entry, start, end)
        translation = translation.translate(dict((ord(c),None) for c in u'()-?_'))
        if lang:
            functions.insert_translation(entry, start, end, translation, lang_iso = lang[0], lang_doculect = lang[1])
        else:
            functions.print_error_in_entry(entry, "could not find language")
            functions.insert_translation(entry, start, end, translation)
    

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)
    
    italic_annotations = [ a for a in entry.annotations if a.value=='italic' ]
    italic_annotations = sorted(italic_annotations, key=attrgetter('start'))
    italic_ranges = []
    for s in italic_annotations:
        italic_ranges.append(s.start)
        italic_ranges.append(s.end)
        
    italic_len = len(italic_ranges)
    
    heads = []
    c_list = []
      
    h_start = 0
    match_sc = re.search(u':', entry.fullentry)  
    match_c = re.search(u',', entry.fullentry)  
    if match_sc:
        h_end = match_sc.start()
    elif match_c:
        h_end = match_c.start()
    
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
    
    # translations
    
    t_start = h_end + 2
    t_end = len(entry.fullentry)
    substr = entry.fullentry[t_start:t_end]

    for m in re.finditer(u',|!', substr):
        comma = True                
        for match_bracket in re.finditer(u'\(.*?\)|\[cf. .*?\]', substr):
            if m.start() > match_bracket.start() and m.start() < match_bracket.end():
                comma = False
    
        if comma:
            c_list.append(m.start() + t_start)
    
    if c_list:
        for i in range(len(c_list)):
            if i == 0:
                trans_e = c_list[i]
                substr1 =  entry.fullentry[t_start:trans_e]
                italic = False
                for x in range(0, italic_len, 2):
                    for y in range(len(substr1)):
                        val = y + t_start
                        if italic_ranges[x] <= val <= italic_ranges[x+1]:
                            italic = True
                            break
                if italic:
                    insert_translation(entry, t_start, trans_e)
                else:            
                    functions.insert_head(entry, t_start, trans_e)
                        
                trans2_s = c_list[0] + 2
                italic = False
                if i + 1 < len(c_list):
                    trans2_e = c_list[i+1]
                    substr2 = entry.fullentry[trans2_s:trans2_e]
                    for x in range(0, italic_len, 2):
                        for y in range(len(substr2)):
                            val2 = y + trans2_s
                            if italic_ranges[x] <= val2 <= italic_ranges[x+1]:
                                italic = True
                                break
                    if italic:
                        insert_translation(entry, trans2_s, trans2_e)
                    else:            
                        functions.insert_head(entry, trans2_s, trans2_e)
                else:
                    insert_translation(entry, trans2_s, t_end)
                    c_list = []
            else:
                trans_s = c_list[i] + 2
                italic = False
                if i + 1 < len(c_list):
                    trans_e = c_list[i+1]
                    substr3 = entry.fullentry[trans_s:trans_e]
                    for x in range(0, italic_len, 2):
                        for y in range(len(substr3)):
                            val3 = y + trans_s
                            if italic_ranges[x] <= val3 <= italic_ranges[x+1]:
                                italic = True
                                break
                    if italic:
                        insert_translation(entry, trans_s, trans_e)
                    else:
                        functions.insert_head(entry, trans_s, trans_e)
                else:
                    insert_translation(entry, trans_s, t_end)
                    c_list = []
    else:
        insert_translation(entry, t_start, t_end)
   
    return heads

    
 
def main(argv):

    bibtex_key = u"rivet1953"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=338,pos_on_page=10).all()

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
