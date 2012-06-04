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
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value== 'pos' or a.value=='translation']
    for a in annotations:
        Session.delete(a)
    
    heads = []
    c_list = []
    s_list = []
    
    #for match_es in re.finditer(u'=', entry.fullentry):
    match_es = re.search(u'=', entry.fullentry)
    if match_es:
        es = True
        for match_bracket in re.finditer(u'\(.*?\)|\[.*?\]', entry.fullentry):
            if match_es.start() > match_bracket.start() and match_es.start() < match_bracket.end():
                es = False
        if es:
            h_end = match_es.start() - 1
        
            h_tmp = entry.fullentry[0:h_end]
            match_pre = re.match(u'.*?- / ', h_tmp)
            if match_pre:
                h_start = match_pre.end()
            else:
                h_start = 0
            
            head = entry.fullentry[h_start:h_end]
            for m in re.finditer(u';|(?<!itr)/(?=tr)|(?<!tr)/(?=itr)', head):
                c_list.append(m.start() + h_start)
        
            if c_list:
                for i in range(len(c_list)):
                    if i == 0:
                        head_end = c_list[i]
                        match_pos = re.search(u'\((tr|itr|itr/tr|tr/itr)\)', head)
                        if match_pos:
                            head_end = match_pos.start(1) - 1 + h_start
                            functions.insert_head(entry, h_start, head_end)
                            
                            p_start = match_pos.start(1) + h_start
                            p_end = match_pos.end(1) + h_start
                            subpos = entry.fullentry[p_start:p_end]
                        
                            for s in re.finditer(u'/', subpos):
                                s_list.append(s.start() + p_start)
                            
                            if s_list:
                                for s in s_list:
                                    # only pos after slash is relevant because first part of head is ignored
                                    p_start = s + 1
                                    functions.insert_pos(entry, p_start, p_end)
                                    s_list = []
                            else:    
                                functions.insert_pos(entry, p_start, p_end)
                        else:
                            functions.insert_head(entry, h_start, head_end)
                    
                        head2_start = c_list[0] + 2
                        if i + 1 < len(c_list):
                            head2_end = c_list[i+1]
                            head2 = entry.fullentry[head2_start:head2_end]
                            match_pos = re.search(u'\((tr|itr)\)', head2)
                            if match_pos:
                                head_end = match_pos.start(1) - 1 + head2_start
                                functions.insert_head(entry, head2_start, head_end)
                                
                                p_start = match_pos.start(1) + head2_start
                                p_end = match_pos.end(1) + head2_start
                                subpos = entry.fullentry[p_start:p_end]
                            
                                for s in re.finditer(u'/', subpos):
                                    s_list.append(s.start() + p_start)
                                
                                if s_list:
                                    for s in s_list:
                                        # only pos after slash is relevant because first part of head is ignored
                                        p_start = s + 1
                                        functions.insert_pos(entry, p_start, p_end)
                                        s_list = []
                                else:
                                    functions.insert_pos(entry, p_start, p_end)    
                                
                            else:    
                                functions.insert_head(entry, head2_start, head2_end)
                        else:
                            head2 = entry.fullentry[head2_start:h_end]
                            match_pos = re.search(u'\((tr|itr)\)', head2)
                            if match_pos:
                                head_end = match_pos.start(1) - 1 + head2_start
                                functions.insert_head(entry, head2_start, head_end)
                                
                                p_start = match_pos.start(1) + head2_start
                                p_end = match_pos.end(1) + head2_start
                                subpos = entry.fullentry[p_start:p_end]
                            
                                for s in re.finditer(u'/', subpos):
                                    s_list.append(s.start() + p_start)
                                
                                if s_list:
                                    for s in s_list:
                                        # only pos after slash is relevant because first part of head is ignored
                                        p_start = s + 1
                                        functions.insert_pos(entry, p_start, p_end)
                                        s_list = []
                                else:
                                    functions.insert_pos(entry, p_start, p_end)
                            else:
                                functions.insert_head(entry, head2_start, h_end)
                    else:
                        head_start = c_list[i] + 2
                        if i + 1 < len(c_list):
                            head_end = c_list[i+1]
                            head_n = entry.fullentry[head_start:head_end]
                            match_pos = re.search(u'\((tr|itr)\)', head_n)
                            if match_pos:
                                head_end = match_pos.start(1) - 1 + head_start
                                functions.insert_head(entry, head_start, head_end)
                                
                                p_start = match_pos.start(1) + head_start
                                p_end = match_pos.end(1) + head_start
                                subpos = entry.fullentry[p_start:p_end]
                            
                                for s in re.finditer(u'/', subpos):
                                    s_list.append(s.start() + p_start)
                                
                                if s_list:
                                    for s in s_list:
                                        # only pos after slash is relevant because first part of head is ignored
                                        p_start = s + 1
                                        functions.insert_pos(entry, p_start, p_end)
                                        s_list = []
                                else:
                                    functions.insert_pos(entry, p_start, p_end)   
                            else:
                                functions.insert_head(entry, head_start, head_end)
                        else:
                            head_n = entry.fullentry[head_start:h_end]
                            match_pos = re.search(u'\((tr|itr)\)', head_n)
                            if match_pos:
                                head_end = match_pos.start(1) - 1 + head_start
                                functions.insert_head(entry, head_start, head_end)
                                
                                p_start = match_pos.start(1) + head_start
                                p_end = match_pos.end(1) + head_start
                                subpos = entry.fullentry[p_start:p_end]
                            
                                for s in re.finditer(u'/', subpos):
                                    s_list.append(s.start() + p_start)
                                
                                if s_list:
                                    for s in s_list:
                                        # only pos after slash is relevant because first part of head is ignored
                                        p_start = s + 1
                                        functions.insert_pos(entry, p_start, p_end)
                                        s_list = []
                                else:
                                    functions.insert_pos(entry, p_start, p_end)
                            else:
                                functions.insert_head(entry, head_start, h_end)
                                #c_list = []
            else:
                # if pos: change head end and get pos
                match_pos = re.search(u'\((tr|itr|itr/tr|tr/itr)\)', head)
                if match_pos:
                    h_end = match_pos.start(1) - 1 + h_start
                    functions.insert_head(entry, h_start, h_end)
                    
                    p_start = match_pos.start(1) + h_start
                    p_end = match_pos.end(1) + h_start
                    subpos = entry.fullentry[p_start:p_end]
                
                    for s in re.finditer(u'/', subpos):
                        s_list.append(s.start() + h_start)
                    
                    if s_list:
                        for s in s_list:
                            #p1_end = s.start() + p_start
                            p1_end = s + p_start
                            functions.insert_pos(entry, p_start, p1_end)
                               
                            #p2_start = s.start() + 1 + p_start
                            p2_start = s + 1 + p_start
                            functions.insert_pos(entry, p2_start, p_end)
                    else:    
                        functions.insert_pos(entry, p_start, p_end)
                else:
                    functions.insert_head(entry, h_start, h_end, head)
            
            # reset comma list
            c_list = []
    
            # translations
            t_start = match_es.end() + 1
            t_end = len(entry.fullentry)
            substr = entry.fullentry[t_start:t_end]
            #print substr
        
            for m in re.finditer(u',|;', substr):
                comma = True                
                for match_bracket in re.finditer(u'\(.*?\)|\[.*?\]', substr):
                    if m.start() > match_bracket.start() and m.start() < match_bracket.end():
                        comma = False
                if comma:
                    c_list.append(m.start() + t_start)
            
            if c_list:
                for i in range(len(c_list)):
                    if i == 0:
                        trans_e = c_list[i]
                        functions.insert_translation(entry, t_start, trans_e)
                        
                        # check for = in front of trans
                        trans2_s = c_list[0] + 2
                        substr1 = entry.fullentry[c_list[0] + 1:]
                        #print substr1
                        match_ess = re.match(u'( = ?)', substr1)
                        if match_ess:
                            trans2_s = match_ess.end(1) + c_list[i] + 1
                        if i + 1 < len(c_list):
                            trans2_e = c_list[i+1]
                            functions.insert_translation(entry, trans2_s, trans2_e)
                        else:
                            functions.insert_translation(entry, trans2_s, t_end)
                            c_list = []
                    else:
                        trans_s = c_list[i] + 2
                        substr2 = entry.fullentry[c_list[i] + 1:]
                        match_ess = re.match(u'( = ?)', substr2)
                        if match_ess:
                            trans_s = match_ess.end(1) + c_list[i] + 1
                            #c_list[0] + 4
                            #print '3', trans_s
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
            print 'No equal sign found in entry', functions.print_error_in_entry(entry)
   
    return heads

    
 
def main(argv):

    bibtex_key = u"zingg1998"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=46,pos_on_page=2).all()

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
