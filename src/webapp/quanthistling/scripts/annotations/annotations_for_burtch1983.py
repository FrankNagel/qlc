# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re
import codecs, unicodedata

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
#from manualannotations_for_burtch1983 import manual_entries


def find_head_end(entry, valid_pos_arr):
    start = -1
    end = -1
    for match_bracket in re.finditer(u"(?:\d\. )?\(([^)]*)\)", entry.fullentry):
        pos = match_bracket.group(0)
        #print pos.encode("utf-8")
        is_pos = False
        for p in valid_pos_arr:
            #print ("[\(,;\. ]%s[\),;\. ]"%p).encode("utf-8")
            re_pos = re.compile(u"[\(,;\./ ]%s[\),;\./ ]"%p)
            if re_pos.search(pos):
                #print "match"
                start = match_bracket.start(0)
                end = match_bracket.end(0)
                return (start, end)
    return (start, end)


def find_pos(entry, valid_pos_arr):
    starts = set()
    ends = set()
    for match_bracket in re.finditer(u"\(([^)]*)\)", entry.fullentry):
        pos = match_bracket.group(0)
        #print pos.encode("utf-8")
        is_pos = False
        for p in valid_pos_arr:
            #print ("[\(,;\. ]%s[\),;\. ]"%p).encode("utf-8")
            re_pos = re.compile(u"[\(,;\./ ]%s[\),;\./ ]"%p)
            if re_pos.search(pos):
                start = match_bracket.start(1)
                end = match_bracket.end(1)
                starts.add(start)
                ends.add(end)
    return (starts, ends)

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    for match_vea in re.finditer(u'\(Vea (.*?)\.?\)', entry.fullentry):
        #entry.append_annotation(match.start(1), match.end(1), u'crossreference', u'dictinterpretation')
        crossref_start = match_vea.start(1)
        crossref_end = match_vea.end(1)
        substr = entry.fullentry[crossref_start:crossref_end]
        start = crossref_start
        for match in re.finditer(r'[,;] ?', substr):
            end = match.start(0) + crossref_start
            entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
            start = match.end(0) + crossref_start
        end = crossref_end
        entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')

def annotate_dialect(entry):
    # delete head annotations
    dialect_annotations = [ a for a in entry.annotations if a.value=='dialectidentification']
    for a in dialect_annotations:
        Session.delete(a)
    
    match = re.search(u'(?:DME|DCP|DMU|DMƗ)', entry.fullentry)
    if match:
        if match.group(0) == u'DME':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto meneca (mɨní̵ca o mí̵nɨca para los huitoto)')
        elif match.group(0) == u'DCP':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto murui del río Cara-Paraná')
        elif match.group(0) == u'DMU':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto muinane (muìnánɨ para los huitoto muinane)')
        elif match.group(0) == u'DMƗ':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto mɨca del río Cara-Paraná')        

def annotate_head(entry, manual_heads_dict, valid_pos_arr):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='boundary' or a.value=='doculect' or a.value=='iso-639-3']
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []
    
    (pos_start, pos_end) = find_head_end(entry, valid_pos_arr)
    if pos_start > -1:
        head = entry.fullentry[:pos_start].strip()
        head = re.sub(r"\.$", "", head)
        
    if head == None:
        match = re.search(u"(?:!? ¡|\?? ¿|\d\.)", entry.fullentry)
        if match:
            tmp = entry.fullentry[:match.start(0)]
            if not re.match(u"(?:lit\.|Vea)", tmp):
                head = tmp.strip()
                head = re.sub(u' ?(?:DME|DCP|DMU|DMƗ) ?$', "", head)

    if head != None and re.search(r'\.', head):
        head = None

    if head == None:
        if (entry.startpage, entry.pos_on_page) in manual_heads_dict:
            head, rest = manual_heads_dict[(entry.startpage, entry.pos_on_page)].split("#", 1)

    if head != None:
        head_start = 0
        head_end = len(head)
        start = head_start
        substr = entry.fullentry[head_start:head_end]
        for match in re.finditer(u'(?:,|;|\? ¿|! ¡|/|$) ?', substr):
            
            end = match.start(0)
            head = entry.fullentry[start:end]
            for match_boundary in re.finditer(u"^-", head):
                entry.append_annotation(start, start + len(match_boundary.group(0)), u'boundary', u'dictinterpretation', u"morpheme boundary")
                head = re.sub("^-", "", head)
                #print head, '1'
                #functions.insert_head(entry, start, end, head)
                
    
            for match_boundaries in re.finditer(u"-$", head):
                entry.append_annotation(start + match_boundaries.start(0), start + match_boundaries.end(0), u'boundary', u'dictinterpretation', u"morpheme boundary")
                head = re.sub("-$", "", head)
                #print head, '2'
                #functions.insert_head(entry, start, end, head)
                
            #else:
            end = match.start(0)
            inserted_head = functions.insert_head(entry, start, end, head)
            if inserted_head != None:
                heads.append(inserted_head)
            else:
                print "empty head in entry: " + entry.fullentry.encode("utf-8")
            start = match.end(0)

          
        #end = head_end
        #inserted_head = functions.insert_head(entry, start, end)
        
        #if inserted_head != None:
        #    heads.append(inserted_head)
        #else:
        #    print "empty head in entry: " + entry.fullentry.encode("utf-8")
    
    else:
        print "%s\t%i\t%i" % (entry.fullentry.encode("utf-8"), entry.startpage, entry.pos_on_page)

    return heads


def annotate_pos(entry, valid_pos_arr):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    (pos_starts, pos_ends) = find_pos(entry, valid_pos_arr)
    if len(pos_starts) > 0:
        for pos_start, pos_end in zip(pos_starts, pos_ends):
            substr = entry.fullentry[pos_start:pos_end]
            start = pos_start
            for match_comma in re.finditer(r', ?', substr):
                end = match_comma.start(0) + pos_start
                entry.append_annotation(start, end, u'pos', u'dictinterpretation')
                start = match_comma.end(0) + pos_start
            end = pos_end
            entry.append_annotation(start, end, u'pos', u'dictinterpretation')
            

def annotate_translations_and_examples(entry, manual_examples_dict):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    translation_starts = []
    translation_ends = []

    if re.search(r'\d\.', entry.fullentry):
        for match in re.finditer(r'(?:\d\.(?: \([^)]*\))?|#)(.*?)(?=\d\.|$)', entry.fullentry):
            end = match.end(1)
            start = match.start(1)
            translation_starts.append(start)
            translation_ends.append(end)
            #entry.append_annotation(start, end, u'translation', u'dictinterpretation')
    else:
        pos_end = functions.get_pos_or_head_end(entry)
        if pos_end > 0:
            translation_starts.append(pos_end+1)
            translation_ends.append(len(entry.fullentry))
            #entry.append_annotation(match.start(1), match.end(1), u'translation', u'dictinterpretation')

    for i in range(len(translation_starts)):
        match_first_dot = False
        translation_ends_dot = translation_ends[i]
        for match_dot in re.finditer(r'\. ?[^)(]', entry.fullentry[translation_starts[i]:translation_ends[i]]):
            inbracket = False
            for m in re.finditer(r'\(.*?\)', entry.fullentry[translation_starts[i]:translation_ends[i]]):
                if match_dot.start(0) > m.start(0) and match_dot.end(0) < m.end(0):
                    inbracket = True
            if not inbracket and not match_first_dot:
                match_first_dot = match_dot
        if match_first_dot:
            translation_ends_dot = translation_starts[i]+match_first_dot.start(0)

        substr = entry.fullentry[translation_starts[i]:translation_ends_dot]

        start = translation_starts[i]
        end = 0

        for match in re.finditer(u'(?:,|;|\? ¿|! ¡|$) ?', substr):
            mybreak = False
            # are we in a bracket?
            for m in re.finditer(r'\(.*?\)', substr):
                if match.start(0) > m.start(0) and match.end(0) < m.end(0):
                    mybreak = True
                
            if not mybreak:
                end = match.start(0) + translation_starts[i]
    
                substr = entry.fullentry[start:end]
                match_vea = re.search(r'\([Vv]ea[^)]*\) ?$', substr)
                if match_vea:
                    end = end - len(match_vea.group(0))
                    #entry.append_annotation(start + match_vea.start(0), start + match_vea.end(0), u'crossreference', u'dictinterpretation', substr[match_vea.start(1):match_vea.end(0)])
    
                substr = entry.fullentry[start:end]
                match_dialect = re.search(u' ?(?:DME|DCP|DMU|DMƗ) ?\.? ?$', substr)
                if match_dialect:
                    end = end - len(match_dialect.group(0))                
    
                substr = entry.fullentry[start:end]
                match_dialect = re.match(u' ?(?:DME|DCP|DMU|DMƗ) ?', substr)
                if match_dialect:
                    start = start + len(match_dialect.group(0))                
    
                functions.insert_translation(entry, start, end)
                start = match.end(0) + translation_starts[i]

        #end = translation_ends_dot

        #substr = entry.fullentry[start:end]
        #match_vea = re.search(r'\(Vea ?(.*?)\) ?$', substr)
        #if match_vea:
        #    end = end - len(match_vea.group(0))

        #substr = entry.fullentry[start:end]
        #match_dialect = re.search(u' ?(?:DME|DCP|DMU|DMƗ) ?\.? ?$', substr)
        #if match_dialect:
        #    end = end - len(match_dialect.group(0))                
        #substr = entry.fullentry[start:end]
        
        #match_dialect = re.match(u' ?(?:DME|DCP|DMU|DMƗ) ?', substr)
        #if match_dialect:
        #    start = start + len(match_dialect.group(0))                

        #functions.insert_translation(entry, start, end)

        # insert examples
        if not (entry.startpage, entry.pos_on_page) in manual_examples_dict:
            if match_first_dot:
                #re_ex = re.compile(r'(?<=\.) ?(.*?[\.\!\?]) ?(.*?[\.\!\?])')
                ex_start = translation_starts[i]+match_first_dot.start(0) + 1
                dots = []
                for match_dot in re.finditer(r'[\.\!\?]', entry.fullentry[ex_start:translation_ends[i]]):
                #for match_ex in re_ex.finditer(entry.fullentry, translation_starts[i]+match_first_dot.start(0), translation_ends[i]):
                    mybreak = False
                    # are we in a bracket?
                    for m in re.finditer(r'\(.*?\)', entry.fullentry[ex_start:translation_ends[i]]):
                        if match_dot.start(0) > m.start(0) and match_dot.end(0) < m.end(0):
                            mybreak = True
                        
                    if not mybreak:
                        dots.append(match_dot.end(0))
                        
                if len(dots)%2 == 0:
                    start = ex_start
                    for j, dot in enumerate(dots):
                        if j%2 == 0:
                            entry.append_annotation(start, ex_start + dot, u'example-src', u'dictinterpretation')
                        else:
                            entry.append_annotation(start, ex_start + dot, u'example-tgt', u'dictinterpretation')
                        start = ex_start + dot
                else:
                    functions.print_error_in_entry(entry, "could not parse examples")

    if (entry.startpage, entry.pos_on_page) in manual_examples_dict:
        re_hashes = re.compile("#([^#]*)#")
        fullentry = manual_examples_dict[(entry.startpage, entry.pos_on_page)]
        examples = []
        examples_starts = []
        examples_ends = []
        offset = 1
        last_end = 0
        for m in re_hashes.finditer(fullentry, last_end):
            examples.append(m.group(1))
            examples_starts.append(m.start(1) - offset)
            examples_ends.append(m.end(1) - offset)
            last_end = m.end(1) + 1
            offset += 2
            
        if (len(examples) % 2) != 0:
            print(u"Error in manual example: {0}".format(fullentry).encode("utf-8"))
        else:
            for i in range(len(examples)/2):
                entry.append_annotation(examples_starts[i*2], examples_ends[i*2], u'example-src', u'dictinterpretation')
                entry.append_annotation(examples_starts[i*2+1], examples_ends[i*2+1], u'example-tgt', u'dictinterpretation')       
                
 
def main(argv):

    bibtex_key = u"burtch1983"
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    manual_heads = open("scripts/annotations/txt/burtch1983_entries_without_bracket.txt", 'r')
    manual_heads_dict = {}
    for l in manual_heads:
        l = l.strip()
        fullentry, startpage, pos_on_page = l.split("\t")
        manual_heads_dict[(int(startpage), int(pos_on_page))] = fullentry.decode("utf-8")
    manual_heads.close()
    
    manual_examples = codecs.open("scripts/annotations/txt/burtch1983_two_examples_or_more.txt", 'r', "utf-8")
    manual_examples_dict = {}
    for l in manual_examples:
        if not '#' in l:
            continue
        l = l.strip()
        l = functions.normalize_stroke(l)
        l = unicodedata.normalize("NFD", l)
        fullentry, url = l.split("|")
        match_url_parts = re.search("/source/burtch1983/(\d{1,3})/(\d{1,3})/index.html", l)
        if match_url_parts:
            startpage = match_url_parts.group(1)
            pos_on_page = match_url_parts.group(2)
            manual_examples_dict[(int(startpage), int(pos_on_page))] = fullentry
        else:
            print("Couldn't match URL: {0}".format(url))
    manual_examples.close()

    pos_file = open("scripts/annotations/txt/burtch1983_valid_pos.txt", 'r')
    valid_pos_arr = []
    for l in pos_file:
        pos = l.strip().decode("utf-8")
        if len(pos) > 0:
            valid_pos_arr.append(pos)
    pos_file.close()

    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=233,pos_on_page=12).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e, manual_heads_dict, valid_pos_arr)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e, valid_pos_arr)
            annotate_translations_and_examples(e, manual_examples_dict)
            #annotate_examples(e)
            annotate_dialect(e)
            annotate_crossrefs(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)