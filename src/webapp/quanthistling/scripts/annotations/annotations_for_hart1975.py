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
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='translation' or a.value=='doculect' or a.value=='iso-639-3']
    for a in annotations:
        Session.delete(a)
    
    heads = []
    c_list = []
    
    match_hyphen = re.search(u'(-|–)', entry.fullentry)
    
    if match_hyphen:
        h_start = 0
        h_end = match_hyphen.start() - 1
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
                        head_entry = functions.insert_head(entry, head2_start, head2_end)
                        heads.append(head_entry)
                    else:
                        head_entry = functions.insert_head(entry, head2_start, h_end)
                        heads.append(head_entry)
                        c_list = []
                else:
                    head_start = c_list[i] + 2
                    if i + 1 < len(c_list):
                        head_end = c_list[i+1]
                        head_entry = functions.insert_head(entry, head_start, head_end)
                        heads.append(head_entry)
                    else:
                        head_entry = functions.insert_head(entry, head_start, h_end)
                        heads.append(head_entry)
                        c_list = []
        else:
            head_entry = functions.insert_head(entry, h_start, h_end, head)
            heads.append(head_entry)
        
        # translations
        
        t_start = match_hyphen.end() + 1
        t_end = len(entry.fullentry)
        
        substr = entry.fullentry[t_start:t_end]
            
        for m in re.finditer(u',', substr):
            comma = True                
            for match_bracket in re.finditer(u'\(.*?\)', substr):
                if m.start() > match_bracket.start() and m.start() < match_bracket.end():
                    comma = False
        
            if comma:
                c_list.append(m.start() + t_start)
        
        if c_list:
            for i in range(len(c_list)):
                if i == 0:
                    trans_e = c_list[i]
                    functions.insert_translation(entry, t_start, trans_e)
                
                    trans2_s = c_list[0] + 2
                    if i + 1 < len(c_list):
                        trans2_e = c_list[i+1]
                        functions.insert_translation(entry, trans2_s, trans2_e)
                    else:
                        functions.insert_translation(entry, trans2_s, t_end)
                        c_list = []
                else:
                    trans_s = c_list[i] + 2
                    if i + 1 < len(c_list):
                        trans_e = c_list[i+1]
                        functions.insert_translation(entry, trans_s, trans_e)
                    else:
                        functions.insert_translation(entry, trans_s, t_end)
                        c_list = []
        else:
            functions.insert_translation(entry, t_start, t_end)
    else:
        print 'No hyphen found in entry', functions.print_error_in_entry(entry)
       
    return heads

    
 
def main(argv):

    bibtex_key = u"hart1975"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=47,pos_on_page=23).all()

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
