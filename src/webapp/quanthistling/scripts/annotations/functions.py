# -*- coding: utf8 -*-

import re
from operator import attrgetter
import unicodedata

def print_error_in_entry(entry, error_string = "error in entry"):
    print error_string + ": " + entry.fullentry.encode("utf-8")
    print "   startpage: %i, pos_on_page: %i" % (entry.startpage, entry.pos_on_page)

def get_last_bold_pos_at_start(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    last_bold_end = -1
    at_start = True
    for a in sorted_annotations:
        if at_start and (a.start <= (last_bold_end + 1)):
            last_bold_end = a.end
        else:
            at_start = False
    return last_bold_end

def get_head_end(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='head']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    head_end = -1
    if len(sorted_annotations) > 0:
        head_end = sorted_annotations[-1].end
    return head_end
    
def get_pos_end(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='pos']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    pos_end = -1
    if len(sorted_annotations) > 0:
        pos_end = sorted_annotations[-1].end
    return pos_end

def get_pos_or_head_end(entry):
    end = get_pos_end(entry)
    if end == -1:
        end = get_head_end(entry)
    return end

def get_translation_end(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='translation']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    trans_end = -1
    if len(sorted_annotations) > 0:
        trans_end = sorted_annotations[-1].end
    return trans_end

def get_first_bold_start_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    for a in sorted_annotations:
        if a.start >= s and a.start <=e:
            return a.start

    return -1

def get_first_italic_start_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    for a in sorted_annotations:
        if a.start >= s and a.start <=e:
            return a.start

    return -1

def insert_annotation(entry, s, e, annotation, string = None):
    if not string:
        string = entry.fullentry[start:end]
    entry.append_annotation(s, e, annotation, u"dictinterpretation", string)
    return string

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
        
    return (start, end, string)

def insert_head(entry, s, e, string = None):
    start = s
    end = e
    string_new = string
    if string == None:
        (start, end, string_new) = remove_parts(entry, start, end)
    if not re.match(r" *$", string_new):
        string_new = re.sub(u"ɨ́", u"í̵", string_new.lower())
        return insert_annotation(entry, s, e, u"head", string_new)
    else:
        return None

def insert_translation(entry, s, e, string = None):
    start = s
    end = e
    string_new = string
    if string == None:
        (start, end, string_new) = remove_parts(entry, start, end)
    if not re.match(r" *$", string_new):
        return insert_annotation(entry, s, e, u"translation", string_new.lower())
    else:
        return None
