# -*- coding: utf8 -*-

import re
from operator import attrgetter
import unicodedata

def split_entry_at(entry, regex, start, end, skip_first=False, in_brackets=None):
    local_start = start
    local_end   = end
    if in_brackets is None:
        in_brackets = get_in_brackets_func(entry)
    for match in re.finditer(regex, entry.fullentry[start:end]):
        if in_brackets(start + match.start(), start + match.end()):
            continue
        local_end = start + match.start(0)
        if not ( skip_first and local_start == start and local_end != end ):
            yield (local_start, local_end)
        local_start = start + match.end(0)

def find_brackets(entry, opening_bracket = '(', closing_bracket = ')'):
    result = []
    opening_index = 0
    open_count = 0
    for index, c in enumerate(entry.fullentry):
        if c == opening_bracket:
            if open_count == 0:
                opening_index = index
            open_count += 1
        elif c == closing_bracket:
            if open_count == 1:
                result.append((opening_index, index+1))
            open_count = max(0, open_count-1) #recover from too many ')'
    if open_count > 0: # missing ')' at the end
        result.append((opening_index, index+1))
    return result

def get_in_brackets_func(entry, brackets=None):
    if brackets is None:
        brackets = find_brackets(entry)
    return lambda x, y: next((b for b in brackets if b[0] < x and y < b[1]), None)

def find_first_point(entry, start, end, in_brackets=None):
    return find_first(entry, '.', start, end, in_brackets)

def find_first(entry, substring, start, end, in_brackets=None):
    if in_brackets is None:
        in_brackets = get_in_brackets_func(entry)
    search_start = start
    while True:
        pos = entry.fullentry.find(substring, search_start, end)
        if pos == -1:
            pos = end
            break
        if not in_brackets(pos, pos+len(substring)):
            break
        search_start = pos + 1
    return pos

def normalize_stroke(string_src):
    string_new = ""
    for char in string_src:
        name = ""
        if char != "\n" and char != "\r" and char != " " and char != "\t":
            try:
                name = unicodedata.name(char)
            except ValueError:
                print u"No Unicode name found for character {0}".format(char).encode("utf-8")
        char_new = char
        if name.endswith("WITH STROKE"):
            name_new = name.replace(" WITH STROKE", "")
            try:
                char_new = unicodedata.lookup(name_new)
                char_new += u"̵"
            except KeyError:
                print "Unicode name \"{0}\" not found".format(name_new).encode("utf-8")
        string_new += char_new
    return string_new

def print_error_in_entry(entry, error_string = "error in entry"):
    print error_string + ": " + entry.fullentry.encode("utf-8")
    print "   startpage: %i, pos_on_page: %i" % (entry.startpage, entry.pos_on_page)
    

def get_bold_range(entry, max_from_start = 0):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    if len(sorted_annotations) == 0:
        return -1, -1

    if sorted_annotations[0].start > max_from_start:
        return -1, -1
        
    last_bold_end = sorted_annotations[0].start
    first_bold_start = sorted_annotations[0].start
    at_start = True
    for a in sorted_annotations:
        if at_start and (a.start <= (last_bold_end + 1)):
            last_bold_end = a.end            
        else:
            at_start = False

    return first_bold_start, last_bold_end

def get_dict_bold_ranges(entry):
    dict_br = {}
    for a in sorted(entry.annotations):
        if a.value == 'bold':
            dict_br[int(a.start)] = int(a.end) 
   
    return dict_br

def get_list_ranges_for_annotation(entry, annotation_value, start=0, end=-1):
    if end == -1:
        end = len(entry.fullentry)

    sorted_annotations = [ [a.start, a.end]
        for a in sorted(entry.annotations, key=attrgetter('start'))
        if a.value==annotation_value and a.start >= start and a.end <= end ]
    
    if len(sorted_annotations) == 0:
        return []
        
    return_list = [ sorted_annotations[0] ]
    j = 0
    for i, a in enumerate(sorted_annotations[1:]):
        if sorted_annotations[i][1] == a[0]:
            return_list[j][1] = a[1]
        elif sorted_annotations[i][1] + 1 == a[0]:
            return_list[j][1] = a[1]
        else:
            return_list.append(a)
            j += 1
    
    return return_list


def get_list_bold_ranges(entry, start=0):
    #sorted_annotations = [ a for a in entry.annotations if a.value=='bold' ]
    #sorted_annotations = sorted(sorted_annotations, key=attrgetter('start')
    return get_list_ranges_for_annotation(entry, "bold", start)

def get_list_italic_ranges(entry, start=0):
    #sorted_annotations = [ a for a in entry.annotations if a.value=='bold' ]
    #sorted_annotations = sorted(sorted_annotations, key=attrgetter('start')
    return get_list_ranges_for_annotation(entry, "italic", start)

def get_last_bold_pos_at_start(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' ]
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

def get_head_ends(entry):
    head_ends = []
    for a in sorted(entry.annotations):
        if a.value == 'head':
            head_ends.append(int(a.end))
   
    return head_ends
    
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

def get_first_italic_glued_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    last_italic_end = None
    last_italic_start = None
    at_start = True
    for a in sorted_annotations:
        if a.end >= s and a.start <= e:
            if at_start and ( (last_italic_end is None) or (a.start <= (last_italic_end + 1)) ):
                last_italic_end = a.end
                last_italic_start = a.start
            else:
                at_start = False

    return (last_italic_start, last_italic_end)

def get_first_italic_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    for a in sorted_annotations:
        if a.start >= s and a.start <=e:
            return (a.start, a.end)
            
    return -1

def get_first_bold_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    for a in sorted_annotations:
        if a.start >= s and a.start <=e:
            return (a.start, a.end)
            
    return -1

def get_last_bold_end_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    for a in sorted_annotations:
        if a.end >= s and a.end <=e:
            return a.end

    return -1

def get_first_italic_range(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    if len(sorted_annotations) != 0:
        return (sorted_annotations[0].start, sorted_annotations[0].end)

    return -1

def get_last_italic_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('end'))
    
    for a in sorted_annotations:
        if a.end >= s and a.end <=e:
            return a.end

    return -1

def insert_annotation(entry, s, e, annotation, string = None):
    if not string:
        string = entry.fullentry[s:e]
    entry.append_annotation(s, e, annotation, u"dictinterpretation", string)
    return string

def lstrip(entry, s, e, chars=None):
    if chars is None:
        do_strip = lambda x: x.isspace()
    else:
        do_strip = lambda x: x in chars
    while s < e and do_strip(entry.fullentry[s]):
        s += 1
    return s

def rstrip(entry, s, e, chars=None):
    if chars is None:
        do_strip = lambda x: x.isspace()
    else:
        do_strip = lambda x: x in chars
    while e > s and do_strip(entry.fullentry[e-1]):
        e -= 1
    return e

def strip(entry, s, e, lchars=None, rchars=None):
    if rchars is None:
        rchars = lchars
    s = lstrip(entry, s, e, lchars)
    e = rstrip(entry, s, e, rchars)
    return s, e
    
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

def insert_head(entry, s, e, string = None, lang_iso = None, lang_doculect = None):
    start = s
    end = e
    string_new = string
    if string == None:
        (start, end, string_new) = remove_parts(entry, start, end)
    if not string_new.strip():
        return None

    string_new = re.sub(u"ɨ́", u"í̵", string_new.lower())

    src_languages = entry.dictdata.src_languages
    if lang_iso == None:
        if len(src_languages) == 1:
            if src_languages[0].language_iso:
                lang_iso = src_languages[0].language_iso.langcode
    if lang_iso != None:
        insert_annotation(entry, start, end, u"iso-639-3", lang_iso)

    if lang_doculect == None:
        if len(src_languages) == 1:
            if src_languages[0].language_bookname:
                lang_doculect = src_languages[0].language_bookname.name
    if lang_doculect != None:
        insert_annotation(entry, start, end, u"doculect", lang_doculect)

    return insert_annotation(entry, start, end, u"head", string_new)

def insert_translation(entry, s, e, string = None, lang_iso = None, lang_doculect = None):
    start = s
    end = e
    string_new = string
    if string == None:
        (start, end, string_new) = remove_parts(entry, start, end)
    if not string_new.strip():
        return None
 
    tgt_languages = entry.dictdata.tgt_languages
    if lang_iso == None:
        if len(tgt_languages) == 1:
            lang_iso = tgt_languages[0].language_iso.langcode
    if lang_iso != None:
        insert_annotation(entry, start, end, u"iso-639-3", lang_iso)

    if lang_doculect == None:
        if len(tgt_languages) == 1:
            lang_doculect = tgt_languages[0].language_bookname.name
    if lang_doculect != None:
        insert_annotation(entry, start, end, u"doculect", lang_doculect)

    return insert_annotation(entry, start, end, u"translation", string_new.lower())
    
def insert_pos(entry, s, e, string = None):
    start = s
    end = e
    string_new = string
    if string == None:
        (start, end, string_new) = remove_parts(entry, start, end)
    if string_new.strip():
        return insert_annotation(entry, start, end, u"pos", string_new.lower())
    else:
        return None
