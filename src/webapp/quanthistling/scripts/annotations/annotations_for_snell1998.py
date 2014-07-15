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


#this is a copy from functions.py with some additions:
#1. strip {..} from the end
#2. strip numbers from the end
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

    match_brackets = re.search('\s*{[^}]*}\s*$', string)
    if match_brackets:
        end = end - len(match_brackets.group(0))
        string = entry.fullentry[start:end]

    match_numbers = re.search('[0-9]+$', string)
    if match_numbers:
        end = end - len(match_numbers.group(0))
        string = entry.fullentry[start:end]

    return (start, end, string)

def find_brackets(entry):
    result = []
    for match in re.finditer(r'\([^\)]*\)', entry.fullentry):
        result.append( (match.start(), match.end()) )
    for match in re.finditer(r'\[[^\]]*\]', entry.fullentry):
        result.append( (match.start(), match.end()) )
    result.sort()
    return lambda x: bool( [1 for y in result if y[0] < x and  x < y[1]-1] )

def find_free_point(entry, start, end, in_brackets):
    while True:
        i = entry.fullentry.find('.', start, end)
        if i == -1:
            return -1
        if not in_brackets(i):
            return i
        start = i + 1
    
def annotate_translation_part(entry, part_start, part_end, bold, in_brackets):
    bold_starts = [b[0] for b in bold if b[0] >= part_start and b[0] <= part_end]
    if bold_starts:
        part_end = bold_starts[0]
    first_point = find_free_point(entry, part_start, part_end, in_brackets)
    if first_point != -1:
        part_end = first_point
    part = entry.fullentry[part_start:part_end]
    translation_start = part_start
    for translation in re.finditer('(.+?)(; |, |$)', part):
        if not in_brackets(part_start + translation.start(2)):
            #print 'part', part, translation_start, part_start+translation.end(1)
            functions.insert_translation(entry, translation_start, part_start+translation.end(1))
            translation_start = part_start + translation.end(2)

def annotate_translations(entry, t_start):
    bold = functions.get_list_ranges_for_annotation(entry, 'bold', t_start)
    in_brackets = find_brackets(entry)
    part = None
    for part in re.finditer('[1-9][0-9]*\. (.*?)(?=[1-9][0-9]*\.|$)', entry.fullentry):
        if part.start() < t_start:
            continue
        #print 'num_trans', part.start(1), part.end(1)
        annotate_translation_part(entry, part.start(1), part.end(1), bold, in_brackets)
    if part is None:
        #print 'trans', t_start, len(entry.fullentry)
        annotate_translation_part(entry, t_start, len(entry.fullentry), bold, in_brackets)

def annotate_everything(entry):
    # delete annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation' or a.value=='crossreference' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in annotations:
        Session.delete(a)
        
    # heads
    head = None
    heads = []
    
    head_end_tmp = functions.get_last_bold_pos_at_start(entry)
    head_tmp = entry.fullentry[:head_end_tmp]
       
    sep_list = []
    for c in re.finditer(u',', head_tmp):
        comma = True
        for mb in re.finditer(u'\{.*?\}', head_tmp):
            #print mb.start()
            if c.start() > mb.start() and c.start() < mb.end():
                comma = False
        if comma:
            sep_list.append(c.start())
    
    if sep_list:
        for i in range(len(sep_list)):
            if i == 0:
                head_start = 0
                head_end = sep_list[i]
                functions.insert_head(entry, *remove_parts(entry, head_start, head_end))
                
                head2_start = sep_list[0] + 2
                if i + 1 < len(sep_list):
                    head2_end = sep_list[1]
                    functions.insert_head(entry, *remove_parts(entry, head2_start, head2_end))
                    i += 1
                else:
                    functions.insert_head(entry, *remove_parts(entry, head2_start, head_end_tmp))
            else:
                head_start = sep_list[i] + 2
                if i + 1 < len(sep_list):
                    head_end = sep_list[i+1]
                    functions.insert_head(entry, *remove_parts(entry, head_start, head_end))
                    i += 1
                else:
                    functions.insert_head(entry, *remove_parts(entry, head_start, head_end_tmp))
    else:
        functions.insert_head(entry, *remove_parts(entry, 0, head_end_tmp))
    
    # part of speech or cross-reference
    crossref = False
    pos_se = functions.get_first_italic_range(entry)
    if pos_se != -1:
        pos = entry.fullentry[pos_se[0]:pos_se[1]]
        if re.match(u'Vea', pos):
            crossref = True
            for match_vea in re.finditer(u'.*? Vea (.*)', entry.fullentry):
                cref_start = match_vea.start(1)
                cref_end = match_vea.end(1)
                substr = entry.fullentry[cref_start:cref_end]
                for match in re.finditer(u', ?', substr):
                    end = match.start(0) + cref_start
                    if end > 0 and entry.fullentry[end-1] == '.':
                        end -= 1
                    entry.append_annotation(cref_start, end, u'crossreference', u'dictinterpretation')
                    cref_start = match.end(0) + cref_start
                if cref_end > 0 and entry.fullentry[cref_end-1] == '.':
                    cref_end -= 1
                entry.append_annotation(cref_start, cref_end, u'crossreference', u'dictinterpretation')
        else:    
            functions.insert_pos(entry, pos_se[0], pos_se[1], pos)
            t_start = pos_se[1] + 1
    else:
        t_start = head_end_tmp + 1
      
    if not crossref:
        annotate_translations(entry, t_start)

    return heads


def main(argv):
    bibtex_key = u"snell1998"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=103,pos_on_page=2).all()

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
