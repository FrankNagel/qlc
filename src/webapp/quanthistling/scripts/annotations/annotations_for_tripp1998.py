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


rm_regex_period = re.compile(r"\.?\s*$")
rm_regex_q_start = re.compile(ur"[¿¡]")
rm_regex_q_end = re.compile(ur"[!?¡]$")
rm_regex_brackets = re.compile(ur"[\(\)]")

#copy from functions.py
#additionally remove ¡ from end
#and left/right double quotation marks
def remove_parts(entry, start, end):
    string = entry.fullentry[start:end]
    
    # remove whitespaces
    try:
        while string[0].isspace():
            start = start + 1
            string = entry.fullentry[start:end]
        while string[-1].isspace():
            end = end - 1
            string = entry.fullentry[start:end]
    except IndexError: # only whitespace
        return 0, 0, u""
    
    match_period = rm_regex_period.search(string)
    if match_period:
        end = end - len(match_period.group(0))
        string = entry.fullentry[start:end]

    if rm_regex_q_start.match(string):
        start = start + 1
        string = entry.fullentry[start:end]

    if rm_regex_q_end.search(string):
        end = end - 1
        string = entry.fullentry[start:end]

    if string.startswith(u"(") and string.endswith(u")") and not rm_regex_brackets.search(string[1:-1]):
        start = start + 1
        end = end - 1
        string = entry.fullentry[start:end]

    if string.startswith(u'\u201C') and string.endswith(u'\u201D'):
        start = start + 1
        end = end - 1
        string = entry.fullentry[start:end]
    return start, end, string


#parts are devided by ǁ 
part_regex = re.compile(u'\u01c1|$')

def annotate_parts(entry):
    # delete annotations
    annotations = [ a for a in entry.annotations
                    if a.value in ['head', 'pos', 'translation', 'crossreference', 'iso-639-3', 'doculect']]
    for a in annotations:
        Session.delete(a)
        
    heads = []
    start = 0
    for match in part_regex.finditer(entry.fullentry):
        end = match.start()
        start = annotate_head(entry, start, end, heads)
        start_cr = annotate_crossref(entry, start, end)
        if not start_cr:
            start = annotate_pos(entry, start, end)
            annotate_translation(entry, start, end)
        start = match.end()
    return heads

#heads are bold and divided by ',' or ';'
head_regex = re.compile(',|;|$')

def annotate_head(entry, start, end, heads):
    bold = functions.get_list_ranges_for_annotation(entry, 'bold', start, end)
    if not bold:
        return start
    head_end = min(bold[0][1], end) #head entry is always bold
    for match in head_regex.finditer(entry.fullentry, start, head_end):
        hstart, hend, head = remove_parts(entry, start, match.start(0))
        functions.insert_head(entry, hstart, hend, head)
        heads.append(head)
        start = match.end(0)
    return head_end


#crossrefs start with '(Véase'
crossref_regex = re.compile(ur'\s*\(Véase (.*?)\)\s*')
#crossrefs are seperated by ','
crossref_div_regex = re.compile(r',|$')
#sometimes they contain a POS; they 're removed
crossref_pos_regex = re.compile(r'\s*([a-z]+\.,)*([a-z]+\.)')

def annotate_crossref(entry, start, end):
    match = crossref_regex.match(entry.fullentry, start, end)
    if not match:
        return None
    cstart = match.start(1)
    for match2 in crossref_div_regex.finditer(entry.fullentry, match.start(1), match.end(1)):
        pos = crossref_pos_regex.search(entry.fullentry, cstart, match2.start())
        if pos:
            cend = pos.start()
        else:
            cend = match2.start()
        cstart, cend, crossref = remove_parts(entry, cstart, cend)
        if crossref:
            entry.append_annotation(cstart, cend, u'crossreference', u'dictinterpretation', crossref)
        cstart = match2.end()
    return match.end(0)


pos_div_regex = re.compile(r',|\+|$')

def annotate_pos(entry, start, end):
    #pos are formatted in italic
    pos_se = functions.get_list_ranges_for_annotation(entry, 'italic', start, end)
    #use only italic entries at the start (incl. <i>pos</i> + <i>pos</i>)
    for i in xrange(1, len(pos_se)):
        if pos_se[i][0] - pos_se[i-1][1] > 5:
            pos_se[i:] = []
            break
    match = None
    for pstart, pend in pos_se:
        for match in pos_div_regex.finditer(entry.fullentry, pstart, pend):
            pstart, pend, pos = remove_parts(entry, pstart, match.start())
            entry.append_annotation(pstart, pend, u'pos', u'dictinterpretation', pos)
            pstart = match.end()
    if match:
        return match.end()
    else:
        return start

def find_brackets(entry):
    result = []
    for match in re.finditer(r'\([^\)]*\)', entry.fullentry):
        result.append( (match.start(), match.end()) )
    return lambda x: bool( [1 for y in result if y[0] < x and  x < y[1]-1] )

def find_free_point(entry, start, end, in_brackets):
    while True:
        i = entry.fullentry.find('.', start, end)
        if i == -1:
            return -1
        if not in_brackets(i):
            return i
        start = i + 1

#translations are sometimes numbered
regex_numbered_trans = re.compile(ur"[0-9]+\.|$")
#divided by ',' or ';'
regex_div_trans = re.compile(ur",|;|$")

def annotate_translation(entry, start, end):
    in_brackets = find_brackets(entry)
    bold = functions.get_list_ranges_for_annotation(entry, 'bold', start, end)
    nstart = start
    for match in regex_numbered_trans.finditer(entry.fullentry, start, end):
        #find end of translation: Either start of bold region, or a point
        bold_starts = [b[0] for b in bold if b[0] >= nstart and b[0] <= match.start()]
        tend = bold_starts and bold_starts[0] or match.start()
        first_point = find_free_point(entry, nstart, tend, in_brackets)
        if first_point != -1:
            tend = first_point
        tstart = nstart
        for match2 in regex_div_trans.finditer(entry.fullentry, nstart, tend):
            if in_brackets(match2.start()):
                continue
            tstart, tend, trans = remove_parts(entry, tstart, match2.start())
            functions.insert_translation(entry, tstart, tend, trans)
            tstart = match2.end()
        nstart = match.end()

        
def main(argv):
    bibtex_key = u"tripp1998"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=66,pos_on_page=10).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_parts(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()
        
if __name__ == "__main__":
    main(sys.argv)
