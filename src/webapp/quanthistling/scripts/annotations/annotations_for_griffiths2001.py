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
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    tab_annotations = sorted(tab_annotations, key=attrgetter('start'))
    
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
    newline_annotations = sorted(newline_annotations, key=attrgetter('start')) 
    
    heads = []
    c_list = []
    
    if len(tab_annotations) != 2:
        print "not 2 tabs in entry ", functions.print_error_in_entry(entry)
    else:
        h_start = 0
        h_end = tab_annotations[0].start
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
        
        if len(newline_annotations) == 1:
            t_starts = []
            t_ends = []
            t_lang = []
            
            spa_t_start = h_end + 1
            spa_t_end = newline_annotations[0].start
            
            #eng_t_start = tab_annotations[1].end + 1 # this should actually give the right position, but is causing the first character of the translation to be missing (?) 
            eng_t_start = tab_annotations[1].end
            eng_t_end = len(entry.fullentry)
            
            t_starts.append(spa_t_start)
            t_starts.append(eng_t_start)
            t_ends.append(spa_t_end)
            t_ends.append(eng_t_end)
            t_lang = [
                ('spa', 'Español'),
                ('eng', 'Inglés')
            ]
            
            for x in range(len(t_starts)):
                substr = entry.fullentry[t_starts[x]:t_ends[x]]
                lang = t_lang[x]
                
                for m in re.finditer(u'(,|;|(\d+\.) ?)', substr):
                    comma = True                
                    for match_bracket in re.finditer(u'\(.*?\)', substr):
                        if m.start() > match_bracket.start() and m.start() < match_bracket.end():
                            comma = False
                
                    if comma:
                        c_list.append(m.start() + t_starts[x])
                
                if c_list:
                    for i in range(len(c_list)):
                        if i == 0:
                            trans_e = c_list[i]
                            functions.insert_translation(entry, t_starts[x], trans_e, lang_iso = lang[0], lang_doculect = lang[1])
                        
                            trans2_s = c_list[0] + 2
                            if i + 1 < len(c_list):
                                trans2_e = c_list[i+1]
                                functions.insert_translation(entry, trans2_s, trans2_e, lang_iso = lang[0], lang_doculect = lang[1])
                            else:
                                functions.insert_translation(entry, trans2_s, t_ends[x], lang_iso = lang[0], lang_doculect = lang[1])
                                c_list = []
                        else:
                            trans_s = c_list[i] + 2
                            if i + 1 < len(c_list):
                                trans_e = c_list[i+1]
                                functions.insert_translation(entry, trans_s, trans_e, lang_iso = lang[0], lang_doculect = lang[1])
                            else:
                                functions.insert_translation(entry, trans_s, t_ends[x], lang_iso = lang[0], lang_doculect = lang[1])
                                c_list = []
                else:
                    functions.insert_translation(entry, t_starts[x], t_ends[x], lang_iso = lang[0], lang_doculect = lang[1])
   
    return heads

    
 
def main(argv):

    bibtex_key = u"griffiths2001"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=81,pos_on_page=1).all()

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
