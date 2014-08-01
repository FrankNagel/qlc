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

def annotate_heads(entry):
    heads = []
    c_list = []
    
    h_start = 0
    h_end = functions.get_last_bold_pos_at_start(entry)
    head = entry.fullentry[h_start:h_end]

    #first try to find infinitive form in round brackets
    #inf_match = re.search('\((.*?)\)', head)
    inf_match = re.search('(,\s+-[a-zA-Z]*\s+)?\((.*?)\)', head)
    if inf_match:
        infinitive = inf_match.group(2)
        if head.startswith(infinitive) or inf_match.group(1):
            start, end, head = functions.remove_parts(entry,  inf_match.start(2), inf_match.end(2))
            head = head.replace('-', '')
            head = functions.insert_head(entry, start, end, head)
            if head:
                heads.append(head)
            return heads
        else:
            functions.print_error_in_entry(entry, "Suspicious entry in brackets (..)")
    
    #try the rest
    for m in re.finditer(u',', head):
        c_list.append(m.start())
        
    if c_list:
        for i in range(len(c_list)):
            if i == 0:
                head_end = c_list[i]
                head = check_insert_head(entry, h_start, head_end)
            
                head2_start = c_list[0] + 2
                if i + 1 < len(c_list):
                    head2_end = c_list[i+1]
                    head = check_insert_head(entry, head2_start, head2_end)
                else:
                    head = check_insert_head(entry, head2_start, h_end)
                    c_list = []
            else:
                head_start = c_list[i] + 2
                if i + 1 < len(c_list):
                    head_end = c_list[i+1]
                    head = check_insert_head(entry, head_start, head_end)
                else:
                    head = check_insert_head(entry, head_start, h_end)
                    c_list = []
            if head:
                heads.append(head)

    else:
        head = check_insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)
    return heads


suffix_pattern = re.compile('\s*-[a-zA-Z]\s*')
def check_insert_head(entry, start, end):
    snip = entry.fullentry[start:end]
    match = suffix_pattern.match(snip)
    if match:
        return None
    index = snip.find('(')
    if index != -1:
        end = index
    start, end, head = functions.remove_parts(entry, start, end)
    head = head.replace('-', '')
    return functions.insert_head(entry, start, end, head)


#after head get all brackets and its content
def get_pos_end(entry, p_start):
    s = entry.fullentry
    end = len(s)
    index = s.find('(', p_start)
    if index ==-1:
        return p_start
    state = 0 # 0: outside brackets; 1: in brackets

    pos_end = p_start
    while index < end:
        c = s[index]
        if state == 0:
            if c == '(':
                state = 1
            elif not c.isspace():
                break
        else:
            if c == ')':
                pos_end = index + 1
                state = 0
        index += 1
    return pos_end

pos_regex = re.compile('\(\s*([^)]*)\s*\)')
def annotate_pos(entry, p_start):
    p_end = get_pos_end(entry, p_start)
    real_p_end = p_start
    for match in pos_regex.finditer(entry.fullentry, p_start, p_end):
        if entry.fullentry.find('Vea ', match.start(1), match.end(1)) != -1:
            continue # skip crossref
        for start, end in iter_parts(entry, '\s*,\s*|\s*$', match.start(1), match.end(1)):
            if entry.fullentry[end-1].isdigit() or entry.fullentry[end-1] == '.':
                functions.insert_pos(entry, start, end)
                real_p_end = match.end(1) + 1
    return real_p_end

def annotate_everything(entry):
    # delete annotations
    for a in entry.annotations:
        if a.value in ['head', 'pos', 'translation', 'crossreference', 'iso-639-3', 'doculect']:
            Session.delete(a)

    heads = annotate_heads(entry)
    
    h_end = functions.get_last_bold_pos_at_start(entry)
    t_start = annotate_pos(entry, h_end)
    
    substr = entry.fullentry[t_start:]
    if re.search(u'\(Vea .*?\)', substr): # cross-references
        for match_vea in re.finditer(u'\(Vea (.*?)\)', substr):
            cref_start = match_vea.start(1) + t_start
            cref_end = match_vea.end(1) + t_start
            substr = entry.fullentry[cref_start:cref_end]
            for match in re.finditer(u', ?', substr):
                end = match.start(0) + cref_start
                entry.append_annotation(cref_start, end, u'crossreference', u'dictinterpretation')
                cref_start = match.end(0) + cref_start
            entry.append_annotation(cref_start, cref_end, u'crossreference', u'dictinterpretation')
    else: # translations
        annotate_translation(entry, t_start)
    return heads

def find_brackets(entry):
    result = []
    for match in re.finditer(r'\([^\)]*\)', entry.fullentry):
        result.append( (match.start(), match.end()) )
    return lambda x: bool( [1 for y in result if y[0] < x and  x < y[1]-1] )

def iter_parts(entry, sep_regex, start, end, skip_first=False, process_all=True, skip_func = None):
    if isinstance(sep_regex, str):
        sep_regex = re.compile(sep_regex)
    firstrun = True
    p_start = start
    match = None
    for match in sep_regex.finditer(entry.fullentry, start, end):
        if firstrun:
            firstrun = False
            if skip_first:
                p_start = match.end()
                match = None
                continue
        if skip_func is None or not skip_func(match.start()):            
            yield p_start, match.start()
            p_start = match.end()
    if match is None and process_all:
        yield start, end

def find_translation_end(entry, start, end, in_brackets, bold):
    """either the next '.' not in brackets, or start of bold text"""
    search_start = start
    while True:
        t_end = entry.fullentry.find('.', search_start, end)
        if t_end == -1:
            t_end = end
            break
        if not in_brackets(t_end):
            break
        search_start = t_end + 1
    #bold alone is not enough to end translations: before that a '!' or '?' has to occur
    bold_starts = [b[0] for b in bold if b[0] >= start and b[0] <= t_end]
    if bold_starts and not in_brackets(bold_starts[0]):
        index = bold_starts[0] - 1
        while entry.fullentry[index].isspace():
            index -= 1
        if entry.fullentry[index] in "!?":
            t_end = bold_starts[0]
    return t_end

def annotate_translation(entry, t_start):
    in_brackets = find_brackets(entry)
    bold = functions.get_list_ranges_for_annotation(entry, 'bold', t_start)
    # translations may be numbered: '1)', '2)' etc.
    for p_start, p_end in iter_parts(entry, '((?<!\(\w\. )\d\))|$', t_start, len(entry.fullentry), True):
        p_end = find_translation_end(entry, p_start, p_end, in_brackets, bold)
        for t_start, t_end in iter_parts(entry, ', |; |! |$', p_start, p_end, skip_func=in_brackets):
            bracket_start = entry.fullentry.find('(', t_start, t_end)
            if bracket_start != -1:
                t_end = bracket_start
            t_start, t_end, string = remove_parts(entry, t_start, t_end)
            functions.insert_translation(entry, t_start, t_end, string)
 
def main(argv):
    bibtex_key = u"nies1986"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=200,pos_on_page=10).all()

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
