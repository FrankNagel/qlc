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
from manualannotations_for_thiesen1998 import manual_entries

vowels_single = [ u"a", u"á", u"a̱", u"á̱", u"e", u"é", u"e̱", u"é̱", u"i", u"í", u"i̱", u"í̱", u"o", u"ó", u"o̱", u"ó̱", u"u", u"ú", u"u̱", u"ú̱", u"í̵", u"ɨ", u"ɨ̱", u"í̵̱" ]
consonants_single = [ u"b", u"c", u"k", u"d", u"g", u"h", u"j", u"m", u"ñ", u"n", u"p", u"r", u"t", u"v", u"w", u"y" ]
vowels_combined = [ u"a̱?a̱?", u"a̱?́a̱?́", u"e̱?e̱?", u"e̱?́e̱?́", u"i̱?i̱?", u"i̱?́i̱?́", u"o̱?o̱?", u"o̱?́o̱?́", u"u̱?u̱?", u"u̱?́u̱?́", u"ɨ̱?ɨ̱?", u"i̵̱?́i̵̱?́" ]
consonants_combined = [ u"ch", u"ds", u"ll", u"ts", u"ty", u"cy", u"jy", u"vy", u"by", u"my", u"dy", u"py", u"gy", u"wy"]

chars = vowels_single + consonants_single + vowels_combined + consonants_combined
chars = sorted(chars, key=len, reverse=True)
vowels = vowels_single + vowels_combined
vowels = sorted(vowels, key=len, reverse=True)
consonants = consonants_single + consonants_combined
consonants = sorted(consonants, key=len, reverse=True)
#print chars

string_re_chars = u"("
for c in chars:
    string_re_chars = string_re_chars + c + u"|"
string_re_chars = re.sub(u"|$", "", string_re_chars)
string_re_chars = string_re_chars + u")(?=[^\u0335\u0331\u0301]|$)"

re_chars = re.compile(string_re_chars, re.I)

string_re_vowels = '|'.join(vowels)
string_re_consonants = '|'.join(consonants)
string_re_syllable_end = u"((?:" + string_re_vowels + u") ([hj] (?=" + string_re_consonants + "|#))?)"

re_syllable_end= re.compile(string_re_syllable_end, re.I)

def get_head_end(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    italic_annotations = [ a for a in entry.annotations if a.value=='italic']
    italic_annotations = sorted(italic_annotations, key=attrgetter('start'))
    
    if len(italic_annotations) > 0:
        sorted_annotations.append(italic_annotations[0])

    current_pos = 0
    head_end = -1
    at_start = True
    for a in sorted_annotations:
        if at_start and re.match(u'(?:^[ ,/\[\]\(\)]*| ?\(forma poseída\)\]?,? ?| ?\(con clas.\)\]?,? ?)$', entry.fullentry[current_pos:a.start]):
            if a.value == 'italic':
                head_end = a.start
                at_start = False
            else:
                head_end = a.end
                current_pos = a.end
        else:
            at_start = False

    return head_end    

def insert_translation(entry, s, e):
    start = s
    end = e
    string = entry.fullentry[start:end]
    if re.match(u" ?(?:acción de|efecto de|estado de|acción y efecto de|acción y estado de) ?$", string):
        return
    #if re.match(r"ser o estar", string):
    #    entry.append_annotation(start, end, u'translation', u'dictinterpretation', "ser" + string[len("ser o estar"):])
    #    entry.append_annotation(start, end, u'translation', u'dictinterpretation', "estar" + string[len("ser o estar"):])
    #else:
    functions.insert_translation(entry, start, end)
    
def remove_parts_translation(str, s, e):
    start = s
    end = e
    subsubstr = str
    match_pipes = re.search(u" ?║.*$", subsubstr)
    if match_pipes:
        end = end - len(match_pipes.group(0))
        subsubstr = subsubstr[:-len(match_pipes.group(0))]
    match_col = re.match(r"\((?:Col.|fig.)\) ?", subsubstr)
    if match_col:
        start = start + len(match_col.group(0))
        subsubstr = subsubstr[len(match_col.group(0)):]
    match_bracket_end = re.search(u"\((?:[vV]er .*?|imp\.sg\..*?|múlt\..*?|sinón\..*?)\) ?$", subsubstr)
    if match_bracket_end:
        end = end - len(match_bracket_end.group(0))
        subsubstr = subsubstr[:-len(match_bracket_end.group(0))]
    match_bracket_start = re.match(u" ?\((?:[vV]er .*?|imp\.sg\..*?|múlt\..*?|sinón\..*?|fig\.)\)", subsubstr)
    if match_bracket_start:
        start = start + len(match_bracket_start.group(0))
        subsubstr = subsubstr[len(match_bracket_start.group(0)):]
    match_period = re.search(r"\.+ ?$", subsubstr)
    if match_period:
        end = end - len(match_period.group(0))
    return [start, end]

def annotate_orthography(entry, o_parser):
    # delete pos annotations
    headorth_annotations = [ a for a in entry.annotations if a.annotationtype.type=='orthographicinterpretation']
    for a in headorth_annotations:
        Session.delete(a)
                
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    
    for a in head_annotations:
        h = a.string
        o = o_parser.parse_string_to_graphemes_string(h)
        
        entry.append_annotation(a.start, a.end, u'headorthographic', u'orthographicinterpretation', o)
    
def annotate_orthography_old(entry):
    # delete pos annotations
    headorth_annotations = [ a for a in entry.annotations if a.annotationtype.type=='orthographicinterpretation']
    for a in headorth_annotations:
        Session.delete(a)
                
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        h = a.string
        h = re.sub(u"-$", "", h)
        h = re.sub(u"-", " ", h)
        #h = re.sub(u"k", "c", h)
        h = re.sub(u" ", u" # ", h)
        h = re_chars.sub(r"\1 ", h)
        #print h.encode("utf-8")
        h = "# " + h + " #"
        h = re.sub(u" +", u" ", h)
        
        # add syllable boundaries
        h = re_syllable_end.sub(r"\1. ", h)
        h = re.sub(u". #", "#", h)
        
        entry.append_annotation(a.start, a.end, u'headorthographic', u'orthographicinterpretation', h)

def annotate_head(entry):
    # delete pos annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    head_end_pos = get_head_end(entry)

    head_start_pos = 0

    substr = entry.fullentry[head_start_pos:head_end_pos]

    while entry.fullentry[head_start_pos] == " ":
        head_start_pos = head_start_pos + 1
        substr = entry.fullentry[head_start_pos:head_end_pos]
    while entry.fullentry[head_end_pos-1] == " ":
        head_end_pos = head_end_pos - 1
        substr = entry.fullentry[head_start_pos:head_end_pos]
    if entry.fullentry[head_start_pos] == "[" and entry.fullentry[head_end_pos-1] == "]":
        head_start_pos = head_start_pos + 1
        head_end_pos = head_end_pos - 1
        substr = entry.fullentry[head_start_pos:head_end_pos]
    match_possession = re.search(u' \(forma poseída\)\]$', substr)
    if match_possession:
        head_end_pos = head_end_pos - len(match_possession.group(0))
        substr = entry.fullentry[head_start_pos:head_end_pos]
    head_starts = []
    head_ends = []

    if re.search(r'(?:/(?!\()|,|\.|\[j) ?', substr):
        start = head_start_pos
        if re.match(u'j', entry.fullentry):
            re_seperator = re.compile(r'(?:/(?!\()|,|\.) ?')
        else:
            re_seperator = re.compile(r'(?:/(?!\()|,|\.|\[j) ?')
        for match in re_seperator.finditer(substr):
            mybreak = False
            # are we in a bracket?
            for m in re.finditer(r'\(.*?\)', substr):
                if match.start(0) >= m.start(0) and match.end(0) <= m.end(0):
                    mybreak = True
                    
            if not mybreak:
                head_starts.append(start)
                head_ends.append(match.start(0)+ head_start_pos)
                start = match.end(0) + head_start_pos
        head_starts.append(start)
        head_ends.append(head_end_pos)
    else:
        head_starts.append(head_start_pos)
        head_ends.append(head_end_pos)

    for i in range(len(head_starts)):
        subsubstr = entry.fullentry[head_starts[i]:head_ends[i]]
        if len(subsubstr) > 0:
            if subsubstr[0] == "[":
                head_starts[i] = head_starts[i] + 1
                subsubstr = entry.fullentry[head_starts[i]:head_ends[i]]
            if subsubstr[-1] == "]":
                head_ends[i] = head_ends[i] - 1
                subsubstr = entry.fullentry[head_starts[i]:head_ends[i]]                
            match = re.search(r" \(.*?\)", subsubstr)
            if match:
                head_ends[i] = head_starts[i] + match.start(0)
                subsubstr = entry.fullentry[head_starts[i]:head_ends[i]]
            match = re.search(r"(?! )(/?\()(.*?)\)", subsubstr)
            if match:
                #head = entry.fullentry[head_starts[i]:head_starts[i]+match.start(1)]
                #entry.append_annotation(head_starts[i], head_starts[i]+match.start(1), u'head', u'dictinterpretation')
                head = functions.insert_head(entry, head_starts[i], head_starts[i]+match.start(1))
                heads.append(head)
                start_sub = head_starts[i]+match.start(2)
                for match_slash in re.finditer(r'/', match.group(2)):
                    end_sub = head_starts[i]+match.start(2)+match_slash.start(0)
                    offset = 0
                    if re.match(r'-', entry.fullentry[start_sub:end_sub]):
                        start_sub = start_sub + 1
                        #offset = start_sub - end_sub
                        head_base = head[:(start_sub-end_sub)]
                    else:
                        head_base = head
                    entry.append_annotation(head_starts[i], head_ends[i], u'head', u'dictinterpretation', head_base + entry.fullentry[start_sub:end_sub])
                    heads.append(head_base + entry.fullentry[start_sub:end_sub])
                    start_sub = head_starts[i]+match.start(2)+match_slash.end(0)
                end_sub = head_starts[i]+match.end(2)
                if re.match(r'-', entry.fullentry[start_sub:head_starts[i]+match.end(2)]):
                    start_sub = start_sub + 1
                    #offset = start_sub - end_sub
                    head_base = head[:(start_sub-end_sub)]
                else:
                    head_base = head
                entry.append_annotation(head_starts[i], head_ends[i], u'head', u'dictinterpretation', head_base + entry.fullentry[start_sub:end_sub])
                heads.append(head_base + entry.fullentry[start_sub:end_sub])
            else:
                #entry.append_annotation(head_starts[i], head_ends[i], u'head', u'dictinterpretation')
                head = functions.insert_head(entry, head_starts[i], head_ends[i])
                heads.append(head)
    return heads
            
def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    if len(sorted_annotations) > 0:
        italic_annotation = sorted_annotations[0]
    else:
        return
    
    # get end of bold
    bold_end_pos = get_head_end(entry)
    if (italic_annotation.start == (bold_end_pos+1)) or (italic_annotation.start == bold_end_pos):
        entry.append_annotation(italic_annotation.start, italic_annotation.end, u'pos', u'dictinterpretation')
        #print entry.fullentry[italic_annotation.start:italic_annotation.end]
        
def annotate_translations(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    translation_starts = []
    translation_ends = []

    if re.search(r'\d\.', entry.fullentry):
        for match in re.finditer(r'(?<=\d\.)(.*?)(?:\d\.|$)', entry.fullentry):
            end = match.end(1)
            start = match.start(1)
            # is there an italic annotation in
            found_first_italic = False
            for a in sorted_annotations:
                if a.start > start and a.start < end and not found_first_italic:
                    end = a.start
                    found_first_italic = True
            #entry.append_annotation(start, end, u'translation', u'dictinterpretation')
            translation_starts.append(start)
            translation_ends.append(end)
    else:        
        bold_end_pos = get_head_end(entry)
        if len(sorted_annotations) == 0:
            # translation is everyting after bold
            if len(entry.fullentry) > bold_end_pos:
                #entry.append_annotation(bold_end_pos, len(entry.fullentry), u'translation', u'dictinterpretation')
                translation_starts.append(bold_end_pos)
                translation_ends.append(len(entry.fullentry))
        else:
            # is first italic not part-of-speech (directly after bold)?
            # translation is everything between bold and italic
            if (sorted_annotations[0].start != (bold_end_pos+1)) and (sorted_annotations[0].start != bold_end_pos):
                #entry.append_annotation(bold_end_pos, sorted_annotations[0].start, u'translation', u'dictinterpretation')
                translation_starts.append(bold_end_pos)
                translation_ends.append(sorted_annotations[0].start)    
            # first italic is part-of-speech
            elif len(sorted_annotations) == 1:
                # translation is everyting after italic
                if len(entry.fullentry) > (sorted_annotations[0].end):
                    #entry.append_annotation(sorted_annotations[0].end+1, len(entry.fullentry), u'translation', u'dictinterpretation')
                    translation_starts.append(sorted_annotations[0].end)
                    translation_ends.append(len(entry.fullentry))    
            else:
                # translation is everything between first and second italic
                #entry.append_annotation(sorted_annotations[0].end+1, sorted_annotations[1].start, u'translation', u'dictinterpretation')
                translation_starts.append(sorted_annotations[0].end)
                translation_ends.append(sorted_annotations[1].start)    

    for i in range(len(translation_starts)):
        substr = entry.fullentry[translation_starts[i]:translation_ends[i]]
        #print "before post: " + substr.encode('utf-8')
        start = translation_starts[i]
        end = 0

        for match in re.finditer(r'(?:;|,|. –) ?', substr):
            mybreak = False
            # are we in a bracket?
            for m in re.finditer(r'\(.*?\)', substr):
                if match.start(0) >= m.start(0) and match.end(0) <= m.end(0):
                    mybreak = True
                
            if not mybreak:
                end = match.start(0) + translation_starts[i]
                subsubstr = entry.fullentry[start:end]
                a = remove_parts_translation(subsubstr, start, end)
                subsubstr = entry.fullentry[a[0]:a[1]]
                #print "after post: " + subsubstr.encode('utf-8')
                if (a[0] < a[1]) and not(re.match(r"\s*$", subsubstr)):
                    insert_translation(entry, a[0], a[1])
                    
                start = match.end(0) + translation_starts[i]
        end = translation_ends[i]           
        subsubstr = entry.fullentry[start:end]
        a = remove_parts_translation(subsubstr, start, end)
        subsubstr = entry.fullentry[a[0]:a[1]]
        #print "after post: " + subsubstr.encode('utf-8')
        if (a[0] < a[1]) and not(re.match(r"\s*$", subsubstr)):
            #entry.append_annotation(a[0], a[1], u'translation', u'dictinterpretation')
            insert_translation(entry, a[0], a[1])
            
   
def annotate_examples(entry): 
    # delete pos annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    if len(sorted_annotations) > 0:
        i = 0
        bold_end_pos = get_head_end(entry)

        # is first italic part-of-speech (directly after bold)?
        if (sorted_annotations[0].start == (bold_end_pos+1)) or (sorted_annotations[0].start == bold_end_pos):
            i = 1
            
        # is dot before italic?
        #while (i < len(sorted_annotations)) and not (entry.fullentry[sorted_annotations[i].start-1] == "." or entry.fullentry[sorted_annotations[i].start-2] == "."):
        #    i = i + 1

        start_annotation = i
        end_annotation = i
        while i < len(sorted_annotations):
            # concat successive italic annotations
            next = False
            if (i < (len(sorted_annotations)-1)):
                if ((sorted_annotations[i].end == sorted_annotations[i+1].start) or (sorted_annotations[i].end == (sorted_annotations[i+1].start-1)) or (re.match(u'(?:ɨ́|ɨ)$', entry.fullentry[sorted_annotations[i].end:sorted_annotations[i+1].start]))):
                    end_annotation = i + 1
                    next = True
            if not next:
                # test if italic is until end of entry: some entry have a second part-of-speech at the end
                if (not len(entry.fullentry) == sorted_annotations[end_annotation].end) and (not len(entry.fullentry) == (sorted_annotations[end_annotation].end+1)):
                    # is there another italic annotation after this one?
                    if end_annotation < (len(sorted_annotations)-1):
                        string = entry.fullentry[sorted_annotations[start_annotation].start:sorted_annotations[end_annotation].end]
                        string = re.sub(u'[—‘’]', '', string)
                        entry.append_annotation(sorted_annotations[start_annotation].start, sorted_annotations[end_annotation].end, u'example-src', u'dictinterpretation', string)
                        # is there numbering in the entry? Then the example's translation ends before the numbering
                        number = re.search(r'\d\.', entry.fullentry[sorted_annotations[end_annotation].end:sorted_annotations[end_annotation+1].start])
                        if number:
                            string = entry.fullentry[sorted_annotations[end_annotation].end:sorted_annotations[end_annotation].end+number.start()]
                            string = re.sub(u'[—‘’]', '', string)
                            entry.append_annotation(sorted_annotations[end_annotation].end, sorted_annotations[end_annotation].end+number.start(), u'example-tgt', u'dictinterpretation', string)
                        else:
                            string = entry.fullentry[sorted_annotations[end_annotation].end:sorted_annotations[end_annotation+1].start]
                            string = re.sub(u'[—‘’]', '', string)
                            entry.append_annotation(sorted_annotations[end_annotation].end, sorted_annotations[end_annotation+1].start, u'example-tgt', u'dictinterpretation', string)
                    else:
                        number = re.search(r'\d\.', entry.fullentry[sorted_annotations[end_annotation].end:len(entry.fullentry)])
                        string = entry.fullentry[sorted_annotations[start_annotation].start:sorted_annotations[end_annotation].end]
                        string = re.sub(u'[—‘’]', '', string)
                        entry.append_annotation(sorted_annotations[start_annotation].start, sorted_annotations[end_annotation].end, u'example-src', u'dictinterpretation', string)
                        if number:
                            string = entry.fullentry[sorted_annotations[end_annotation].end:sorted_annotations[end_annotation].end+number.start()]
                            string = re.sub(u'[—‘’]', '', string)
                            entry.append_annotation(sorted_annotations[end_annotation].end, sorted_annotations[end_annotation].end+number.start(), u'example-tgt', u'dictinterpretation', string)
                        else:
                            string = entry.fullentry[sorted_annotations[end_annotation].end:len(entry.fullentry)]
                            string = re.sub(u'[—‘’]', '', string)
                            entry.append_annotation(sorted_annotations[end_annotation].end, len(entry.fullentry), u'example-tgt', u'dictinterpretation', string)
                start_annotation = i + 1
                end_annotation = i + 1
                #while (i < len(sorted_annotations)) and not (entry.fullentry[sorted_annotations[i].start-1] == "." or entry.fullentry[sorted_annotations[i].start-2] == "."):
                #    i = i + 1
                
            i = i + 1

def main(argv):
    bibtex_key = u"thiesen1998"
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    # create orthography parser
    base_qlc_path = "/media/Daten/Projects/git-github/qlc"
    sys.path.append(os.path.join(base_qlc_path, "src"))
    import qlc.OrthographyProfile
    
    orthography_profile_location = os.path.join(base_qlc_path, "data", "orthography_profiles", "{0}.txt".format(bibtex_key))
    o_parser = qlc.OrthographyProfile.OrthographyProfile(orthography_profile_location)

    # load dictionary data for this book
    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()        
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=128,pos_on_page=18).all()
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
            annotate_examples(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
    
        Session.commit()
# , u"aa", u"áá", u"ee", u"éé", u"ii", u"íí", u"oo", u"óó", u"uu", u"úú", u"í̵í̵", u"ɨɨ"
        #chars = [ u"ch", u"ds", u"ll", u"ts", u"ty", u"cy", u"jy", u"vy", u"by", u"my", u"dy", u"py", u"gy", u"wy", u"a̱?a̱?", u"a̱?́a̱?́", u"e̱?e̱?", u"e̱?́e̱?́", u"i̱?i̱?", u"i̱?́i̱?́", u"o̱?o̱?", u"o̱?́o̱?́", u"u̱?u̱?", u"u̱?́u̱?́", u"ɨ̱?ɨ̱?", u"i̵̱?́i̵̱?́"]
        #chars = chars + [ u"b", u"c", u"k", u"d", u"g", u"h", u"j", u"m", u"ñ", u"n", u"p", u"r", u"t", u"v", u"w", u"y", u"a", u"á", u"a̱", u"á̱", u"e", u"é", u"e̱", u"é̱", u"i", u"í", u"i̱", u"í̱", u"o", u"ó", u"o̱", u"ó̱", u"u", u"ú", u"u̱", u"ú̱", u"í̵", u"ɨ", u"ɨ̱", u"í̵̱" ]
        
        for e in entries:
            annotate_orthography(e, o_parser)

        Session.commit()
            

if __name__ == "__main__":
    main(sys.argv)