# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter, itemgetter
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
   
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_all = entry.fullentry[:head_end]
    head_all = head_all.rstrip()
    
    # get all heads
    #for s, e in functions.get_list_bold_ranges(entry):
    #    head_all = entry.fullentry[s:e]

    list_csc = []
    
    for c in re.finditer(';|:', head_all):
        list_csc.append(c.start())

    i = 0
    j = 0

    if list_csc != 0:
        head_all_split = re.split(r'[;|:]', head_all)
        
        for head in head_all_split:
            if i == 0:
                s = 0
            else:
                s = list_csc[j] + 2
                j += 1
            
            if i < len(list_csc):
                e = list_csc[i]
            else:
                e = head_end
        
            i += 1
        
            head = functions.insert_head(entry, s, e, head)
            heads.append(head)
    else:
        head = functions.insert_head(entry, 0, head_end)
        heads.append(head)
    
    # annotation of translation
    trans_start = head_end + 1
    trans_all = entry.fullentry[trans_start:]
    trans_end = len(entry.fullentry)
        
    re_sc = re.compile(";")
    match_sct = re_sc.search(trans_all)
    match_scf = re_sc.search(entry.fullentry)
    
    more_bold = -1
    more_bold = functions.get_first_bold_start_in_range(entry, trans_start, trans_end)
    
    list_sc = []
    for sc in re.finditer(';', entry.fullentry):
        list_sc.append(sc.start())
    
    list_sc_bhe = [a for a in list_sc if a > head_end]
    
    match_trans_7_21 = re.compile(u'onpás̈hcon \(agua en depósito\); jene \(cosa líquida\)')
    match_trans_25_12 = re.compile(u'jabonbira noshicanqui \(romper tela\); jabonbira huas̈hacanqui \(romper madera\)')
    
    if more_bold != -1:
        if match_trans_7_21.search(trans_all):
            if match_sct:
                #trans1
                trans1_end = list_sc_bhe[0]
                translation1 = entry.fullentry[trans_start:trans1_end]
                functions.insert_translation(entry, trans_start, trans1_end, translation1)
                #trans2
                trans2_end = more_bold - 2
                translation2 = entry.fullentry[list_sc_bhe[0] + 2 :trans2_end]
                functions.insert_translation(entry, list_sc_bhe[0] + 2, trans2_end, translation2)
        else:
            trans_end = more_bold - 2
            translation = entry.fullentry[trans_start:trans_end]
            functions.insert_translation(entry, trans_start, trans_end, translation)
    else:
        if match_trans_25_12.search(trans_all):
            if match_sct:
                #trans1
                trans1_end = list_sc_bhe[0]
                translation1 = entry.fullentry[trans_start:trans1_end]
                functions.insert_translation(entry, trans_start, trans1_end, translation1)
                #trans2
                translation2 = entry.fullentry[list_sc_bhe[0] + 2 :trans_end]
                functions.insert_translation(entry, list_sc_bhe[0] + 2, trans_end, translation2)
        else:
            translation = trans_all[:trans_end]
            functions.insert_translation(entry, trans_start, trans_end, translation)
   
    return heads

def main(argv):

    bibtex_key = u"parker1992"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=25,pos_on_page=12).all()

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
