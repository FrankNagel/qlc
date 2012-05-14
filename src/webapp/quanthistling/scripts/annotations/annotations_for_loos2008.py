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
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='translation']
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    tab_annotations = sorted(tab_annotations, key=attrgetter('start'))
    
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
    newline_annotations = sorted(newline_annotations, key=attrgetter('start'))
    
    heads = []    
    slashes = []
    
    if len (tab_annotations) < 2:
        print 'less than 2 tabs in entry: ', functions.print_error_in_entry(entry)
    
    # number of tabs has to be even
    elif len(tab_annotations) % 2 != 0:
        print 'number of tabs odd ', functions.print_error_in_entry(entry)
    
    elif newline_annotations:
        i = 0
        for j in range(0, len(tab_annotations) - 1, 2):
            h_start = tab_annotations[j].end
            h_end = tab_annotations[j + 1].start
            head = entry.fullentry[h_start:h_end]
            functions.insert_head(entry, h_start, h_end)
            
            t_start = tab_annotations[j+1].start + 1
            if j + 2 < len(tab_annotations):
                t_end = newline_annotations[i].start
                substr = entry.fullentry[t_start:t_end]
                i += 1
            else:
                t_end = len(entry.fullentry)
                substr = entry.fullentry[t_start:t_end]
            
            match_slash = re.finditer(u'(/|,)', substr)
            if match_slash:
                for m in match_slash:
                    slashes.append(m.start() + t_start)
            
            if slashes:                        
                for i in range(len(slashes)):
                    if i == 0:
                        trans_e = slashes[i]
                        functions.insert_translation(entry, t_start, trans_e)
                    
                        trans2_s = slashes[0] + 2
                        if i + 1 < len(slashes):
                            trans2_e = slashes[i+1]
                            functions.insert_translation(entry, trans2_s, trans2_e)
                        else:
                            functions.insert_translation(entry, trans2_s, t_end)
                    else:
                        trans_s = slashes[i] + 2
                        if i + 1 < len(slashes):
                            trans_e = slashes[i+1]
                            functions.insert_translation(entry, trans_s, trans_e)
                        else:
                            functions.insert_translation(entry, trans_s, t_end)
            else:
                functions.insert_translation(entry, t_start, t_end)
    else:
        #head
        h_start = tab_annotations[0].start + 1
        h_end = tab_annotations[1].start
        functions.insert_head(entry, h_start, h_end)
        
        # translation(s)
        t_start = tab_annotations[1].start + 1
        t_end = len(entry.fullentry)
        substr = entry.fullentry[t_start:t_end]

        match_slash = re.finditer(u'(/|,)', substr)
        if match_slash:
            for m in match_slash:
                slashes.append(m.start() + t_start)
        
        if slashes:                        
            for i in range(len(slashes)):
                if i == 0:
                    trans_e = slashes[i]
                    functions.insert_translation(entry, t_start, trans_e)
                
                    trans2_s = slashes[0] + 2
                    if i + 1 < len(slashes):
                        trans2_e = slashes[i+1]
                        functions.insert_translation(entry, trans2_s, trans2_e)
                    else:
                        functions.insert_translation(entry, trans2_s, t_end)
                else:
                    trans_s = slashes[i] + 2
                    if i + 1 < len(slashes):
                        trans_e = slashes[i+1]
                        functions.insert_translation(entry, trans_s, trans_e)
                    else:
                        functions.insert_translation(entry, trans_s, t_end)
        else:
            functions.insert_translation(entry, t_start, t_end)
        
    return heads

    
 
def main(argv):

    bibtex_key = u"loos2008"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=3,pos_on_page=19).all()

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
