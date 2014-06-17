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

def insert_head(entry, head_s, head_e):
#    if entry.is_subentry:
#        match_dashes = re.match(u" ?[—-]+ ?", entry.fullentry[head_s:head_e])
#        if match_dashes:
#            head_s += len(match_dashes.group(0))
    head = entry.fullentry[head_s:head_e]
    if not entry.is_subentry:
        for m in re.finditer("-", head):
            entry.append_annotation(head_s + m.start(0), head_s + m.end(0), u'boundary', u'dictinterpretation', u"morpheme boundary")

    head = re.sub("-", "", head).strip()
    return functions.insert_head(entry, head_s, head_e, head)

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    tab_annotations = sorted(tab_annotations, key=attrgetter('start'))

    if entry.is_subentry:
        tab_annotations.pop(0)
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
  
    #translation_end = len(entry.fullentry)

    heads = []
    
    if tab_annotations:
        head_end = tab_annotations[0].start

        for (s, e) in functions.split_entry_at(entry, r"(?: ~ |$)", 0, head_end):
            head = insert_head(entry, s, e)
            heads.append(head)

        # head = entry.fullentry[0:tab_annotations[0].start]
        # head_end_tmp = tab_annotations[0].start
        
        # tildes = []
        # for t in re.finditer(' ~ ', head):
        #     tildes.append(t.start())
        #     tildes.append(t.end())
        
        # if tildes:
        #     for i in range((len(tildes)/2)):
        #         if i == 0:
        #             head1_end = tildes[i]
        #             head_str = process_head(entry, 0, head1_end)
        #             inserted_head = functions.insert_head(entry, 0, head1_end, head_str)
        #             heads.append(inserted_head)
                
        #             head2_start = tildes[i + 1]
        #             if i + 1 < len(tildes)/2:
        #                 head2_end = tildes[i + 2]
        #                 head_str = process_head(entry, head2_start, head2_end)
        #                 inserted_head = functions.insert_head(entry, head2_start, head2_end, head_str)
        #                 heads.append(inserted_head)
        #             else:
        #                 head_str = process_head(entry, head2_start, head_end_tmp)
        #                 inserted_head = functions.insert_head(entry, head2_start, head_end_tmp, head_str)
        #                 heads.append(inserted_head)
        #         else:
        #             head_s = tildes[i + 2]
        #             if i + 1 < len(tildes)/2:
        #                 head_e = tildes[i + 3]
        #                 head_str = process_head(entry, head_s, head_e)
        #                 inserted_head = functions.insert_head(entry, head_s, head_e, head_str)
        #                 heads.append(inserted_head)
        #             else:
        #                 head_str = process_head(entry, head_s, head_end_tmp)                        
        #                 inserted_head = functions.insert_head(entry, head_s, head_end_tmp, head_str)
        #                 heads.append(inserted_head)
        # else:
        #     head_str = process_head(entry, 0, tab_annotations[0].start)
        #     inserted_head = functions.insert_head(entry, 0, tab_annotations[0].start, head_str)
        #     heads.append(inserted_head)
    else:
        functions.print_error_in_entry(entry, "error in tabs")
        return
    
    # pos & trans
    dot_list = []
    for d in re.finditer(u'[\.?!]', entry.fullentry):
        dot_list.append(d.start())
    
    dot_list_ah = [ a for a in dot_list if a > head_end]
    
    if len(dot_list_ah) < 2:
        print(head_end)
        functions.print_error_in_entry(entry, "error in dot_list")
    else:
        # pos
        pos_s = tab_annotations[0].end
        pos_e = dot_list_ah[0]
        functions.insert_pos(entry, pos_s, pos_e)
        
        # translation(s)
        comma_list = []
        for com in re.finditer(r'(,|;)', entry.fullentry):
            comma_list.append(com.start())
        
        comma_list_ap = [ a for a in comma_list if a > dot_list_ah[0] ] 
        
        tr_s = dot_list_ah[0] + 1
        
        if comma_list_ap:
            for i in range(len(comma_list_ap)):
                    if i == 0:
                        trans_e = comma_list_ap[i]
                        translation = functions.insert_translation(entry, tr_s, trans_e)
                        
                        trans2_s = comma_list_ap[0] + 2
                        if i + 1 < len(comma_list_ap):
                            trans2_e = comma_list_ap[i+1]
                            translation = functions.insert_translation(entry, trans2_s, trans2_e)
                        else:
                            translation = functions.insert_translation(entry, trans2_s, dot_list_ah[1])
                    else:
                        trans_s = comma_list_ap[i] + 2
                        if i + 1 < len(comma_list_ap):
                            trans_e = comma_list_ap[i+1]
                            translation = functions.insert_translation(entry, trans_s, trans_e)
                        else:
                            translation = functions.insert_translation(entry, trans_s, dot_list_ah[1])    
        else:
            tr_e = dot_list_ah[1]
            functions.insert_translation(entry, tr_s, tr_e)
        
    return heads

 
def main(argv):

    bibtex_key = u"mori1981"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=11).all()

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
