# -*- coding: utf8 -*-

import sys, os, re, codecs, unicodedata
sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import importfunctions

import quanthistling.dictdata.languages
import quanthistling.dictdata.toolboxfiles
import quanthistling.dictdata.components
import quanthistling.dictdata.annotationtypes

def clean_and_split_translations(fullentry, annotations):
    ret = []
    for a in annotations:
        if a[2] == "translation":
            start = 0
            a_start = a[0]
            a_end = a[1]
            substr = fullentry[a_start:a_end]
            for match_sep in re.finditer("(?:[,;] ?|$)", substr):
                mybreak = False
                # are we in a bracket?
                for m in re.finditer(r'\([^)]*\)', substr):
                    if match_sep.start(0) >= m.start(0) and match_sep.end(0) <= m.end(0):
                        mybreak = True
                for m in re.finditer(r'"[^"]*"', substr):
                    if match_sep.start(0) >= match_sep.start(0) and match_sep.end(0) <= m.end(0):
                        mybreak = True
                        
                if not mybreak:
                    end = match_sep.start(0)

                    match_prefix_garbage = re.search(r'^\s*(?:\([^)]*\)|"[^"]*")\s*', substr[start:end])
                    while match_prefix_garbage:
                        start = start + match_prefix_garbage.end(0)
                        match_prefix_garbage = re.search(r'^\s*(?:\([^)]*\)|"[^"]*")\s*', substr[start:end])
    
                    match_suffix_garbage = re.search(r'\s*(?:\([^)]*\)|"[^"]*")\s*$', substr[start:end])
                    while match_suffix_garbage:
                        end = start + match_suffix_garbage.start(0)
                        match_suffix_garbage = re.search(r'\s*(?:\([^)]*\)|"[^"]*")\s*$', substr[start:end])

                    ret.append([a_start + start, a_start + end, a[2], a[3]])
                    start = match_sep.end(0)
        else:
            ret.append(a)
    return ret
                    

def main(argv):
    if len(argv) < 3:
        print "call: importtoolboxfile.py bibtex_key ini_file"
        exit(1)

    bibtex_key = argv[1]
    ini_file = argv[2]
    dictdata_path = 'quanthistling/dictdata'

    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    if bibtex_key != "all":
        files = [b for b in quanthistling.dictdata.toolboxfiles.list if b['bibtex_key'] == bibtex_key]
    else:
        files = quanthistling.dictdata.toolboxfiles.list
        
        
    for tb in files:
        importfunctions.delete_book_from_db(Session, tb['bibtex_key'])
        book = importfunctions.insert_book_to_db(Session, tb)
        
        for data in tb['dictdata']:
            dictdata = importfunctions.insert_dictdata_to_db(Session, data, book)
    
            print("Processing file {0}.".format(data['file']))
            
            encoding = "utf-8"
            if "encoding" in data:
                encoding = data["encoding"]
                
            with codecs.open(os.path.join(dictdata_path, data['file']), "r", encoding) as f:
                while f.next().strip():
                    pass
                
                entry_string = ""
                i = 1
                for line in f:
                    line = importfunctions.normalize_stroke(line)
                    line = unicodedata.normalize("NFD", line)
                    if line.strip():
                        entry_string += line
                    else:
                        if "charmapping" in data:
                            for a in data["applycharmappingon"]:
                                match_a = re.search("\\\\{0}[^\n]*\n".format(a), entry_string)
                                if match_a:
                                    string = match_a.group(0)
                                    for char_original in data["charmapping"]:
                                        string = re.sub(char_original, data["charmapping"][char_original], string)
                                    entry_string = entry_string[:match_a.start(0)] + string + entry_string[match_a.end(0):]
                        entry = model.Entry()
                        annotations = []
                        annotations_subentry = []
                        fullentry = ""
                        for char in entry_string:
                            if char == '\n':
                                pos = len(fullentry)
                                annotations.append([pos, pos, u'newline', u'pagelayout'])
                            elif char == '\t':
                                pos = len(fullentry)
                                annotations.append([pos, pos, u'tab', u'pagelayout'])
                            elif char == "\r":
                                pass
                            else:
                                fullentry = fullentry + char
                        sorted_newlines = sorted([ a[0] for a in annotations if a[2] == "newline" ])
                        entry.fullentry = fullentry
                        
                        for a in data['annotations']:
                            for match_a in re.finditer("\\\\{0} ".format(a), fullentry):
                                a_start = match_a.end(0)
                                a_end = next(x for x in sorted_newlines if x > a_start)
                                if data['annotations'][a].startswith("subentry-"):
                                    annotations_subentry.append([a_start, a_end, data['annotations'][a][9:], u'dictinterpretation'])
                                else:
                                    annotations.append([a_start, a_end, data['annotations'][a], u'dictinterpretation'])
                                
                        annotations = clean_and_split_translations(fullentry, annotations)
                        for a in annotations:
                            entry.append_annotation(a[0], a[1], a[2], a[3])
                            
                        entry.startpage               = 1
                        entry.endpage                 = 1
                        entry.startcolumn             = 1
                        entry.endcolumn               = 1
                        entry.pos_on_page             = i
                        entry.dictdata                = dictdata
                        entry.book                    = book
                        entry.is_subentry             = False
                        entry.is_subentry_of_entry_id = None
                        Session.add(entry)
                        i += 1
                        
                        if annotations_subentry:
                            annotations_subentry = clean_and_split_translations(fullentry, annotations_subentry)
                            Session.commit()
                            subentry = model.Entry()
                            subentry.fullentry = fullentry
                            for a in annotations_subentry:
                                subentry.append_annotation(a[0], a[1], a[2], a[3])
                            subentry.startpage               = 1
                            subentry.endpage                 = 1
                            subentry.startcolumn             = 1
                            subentry.endcolumn               = 1
                            subentry.pos_on_page             = i
                            subentry.dictdata                = dictdata
                            entry.book                       = book
                            subentry.is_subentry             = True
                            subentry.is_subentry_of_entry_id = entry.id
                            Session.add(subentry)
                            i += 1
                            
                        entry_string = ""
                        
    Session.commit()
    Session.close()

if __name__ == "__main__":
    main(sys.argv)