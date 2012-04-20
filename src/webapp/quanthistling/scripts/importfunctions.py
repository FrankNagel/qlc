# -*- coding: utf8 -*-

import re, os
import unicodedata
from quanthistling import model
from annotations import functions

def normalize_stroke(string_src):
    return functions.normalize_stroke(string_src)

def delete_book_from_db(Session, bibtex_key):
    book_q = Session.query(model.Book)
    book = book_q.filter_by(bibtex_key=bibtex_key).first()

    if book:
        data_array = ()
        if book.type == 'dictionary':
            data_array = book.dictdata
        elif book.type == 'wordlist':
            data_array = book.wordlistdata
            
        for data in data_array:
            for entry in data.entries:
                for a in entry.annotations:
                    Session.delete(a)
                Session.delete(entry)
                Session.commit()
            Session.delete(data)

        for data in book.nondictdata:
            Session.delete(data)
        Session.delete(book)
        Session.commit()

def insert_book_to_db(Session, bookdata):
    book = model.Book()
    book.title = bookdata['title']
    book.author = bookdata['author']
    book.year = bookdata['year']
    book.bibtex_key = bookdata['bibtex_key']
    book.columns = bookdata['columns']
    book.pages = bookdata['pages']
    book.is_ready = bookdata['is_ready']
    book.type = bookdata['type']
    Session.add(book)
    Session.commit()
    return book

def insert_language_to_db(Session, languagedata):
    language = model.Language()
    language.name = languagedata['name']
    language.langcode = languagedata['langcode']
    language.description = languagedata['description']
    language.url = languagedata['url']
    Session.add(language)
    Session.commit()
    return language

def insert_wordlistdata_to_db(Session, data, book):
    wordlistdata = Session.query(model.Wordlistdata).filter_by(book_id=book.id, language_bookname=data['language_bookname'], startpage=data['startpage'], endpage=data['endpage']).first()
    if wordlistdata == None:
        wordlistdata = model.Wordlistdata()
        wordlistdata.startpage = data['startpage']
        wordlistdata.endpage = data['endpage']
        wordlistdata.language_bookname = data['language_bookname']
        wordlistdata.book = book
    
    if data['language_name'] != "":
        language = Session.query(model.Language).filter_by(name=data['language_name']).first()
        if language == None:
            #log.warn("Language " + b['src_language_name'] + " not found, inserting book " + b['title'].encode('ascii', errors='ingore') + " without source language." )
            print("Language %s not found, inserting book without source language." % data['language_name'])
        wordlistdata.language = language
    
    if data['component'] != '':
        component = Session.query(model.Component).filter_by(name=data['component']).first()
        if component == None:
            log.warn("Component not found, inserting dictdata without component." )
        wordlistdata.component = component
    
    Session.add(wordlistdata)
    Session.commit()
    return wordlistdata
    
##
# Parses an entry from text to an entry model
def process_line(text, type="dictionary"):
    
    if type == "dictionary":
        entry = model.Entry()
    elif type == "wordlist":
        entry = model.WordlistEntry()
    else:
        print "unknown type in process_line"
        return None

    # head word is bold at the beginning of the entry
    #entry.head = re.sub(re.compile(r'^\t?\t?<b>(.*?)</b>.*', re.DOTALL), r'\1', text)
    #entry.head = u'dummy'
    
    in_html_entity          = False
    html_entity             = ''
    html_entity_stack       = []
    html_entity_start       = 0
    html_entity_start_stack = []
    fullentry               = ''
    annotations             = []
    prevchar                = ''
    prevchar_special        = False
    for char in text:
        if char == '<':
            in_html_entity = True
        elif char == '>':
            in_html_entity = False
            if re.match(r'^\/', html_entity):
                html_end_entity = re.sub(r'^/', '', html_entity)
                len_html_entity_stack = len(html_entity_stack)
                html_start_entity = ''
                if len(html_entity_stack) > 0:
                    html_start_entity = html_entity_stack.pop()
                if (len_html_entity_stack < 1) or (html_end_entity != html_start_entity):
                    log.warning("html start/end tag mismatch")
                    log.warning("  Start tag: " + html_start_entity)
                    log.warning("  End tag: " + html_end_entity)
                    log.warning("  Full entry: " + text.encode('utf-8'))
                html_entity_start = html_entity_start_stack.pop()
                html_entity_end = len(fullentry)
                if html_end_entity == 'b':
                    annotations.append([html_entity_start, html_entity_end, u'bold', u'formatting'])
                elif html_end_entity == 'i':
                    annotations.append([html_entity_start, html_entity_end, u'italic', u'formatting'])
                elif html_end_entity == 'u':
                    annotations.append([html_entity_start, html_entity_end, u'underline', u'formatting'])
                elif html_end_entity == 'sup':
                    annotations.append([html_entity_start, html_entity_end, u'superscript', u'formatting'])
                elif html_end_entity == 'sc':
                    annotations.append([html_entity_start, html_entity_end, u'smallcaps', u'formatting'])
                html_entity = ''
            else:
                html_entity_start = len(fullentry)
                html_entity_start_stack.append(html_entity_start)
                html_entity_stack.append(html_entity)
                html_entity = ''
        elif char == '\n':
            pos = 0
            if prevchar == '-':
                fullentry = fullentry[:-1]
                pos = len(fullentry)
                for a in annotations:
                    if a[1] == pos + 1:
                        a[1] = pos
                annotations.append([pos, pos, u'hyphen', u'pagelayout'])
            else:
                pos = len(fullentry)
                if fullentry[-1] != " ":
                    fullentry = fullentry + " "
            annotations.append([pos, pos, u'newline', u'pagelayout'])
        elif char == '\t':
            pos = len(fullentry)
            
            if pos >  0 and not prevchar_special:
                #print "inserted space for tab"
                #print text.encode("utf-8")
                #print fullentry.encode("utf-8")
                fullentry = fullentry + " "
            annotations.append([pos, pos, u'tab', u'pagelayout'])
        elif char == '\f':
            pos = len(fullentry)
            annotations.append([pos, pos, u'pagebreak', u'pagelayout'])
        elif in_html_entity:
            html_entity = html_entity + char
        else:
            fullentry = fullentry + char
        if not in_html_entity and char != '>' and char != '\f' and char != '\n' and char != '\t':
            prevchar = char
        if char == '\f' or char == '\n' or char == '\t':
            prevchar_special = True
        else:
            prevchar_special = False
            
    entry.fullentry = fullentry
    #fullentry_search = re.sub(r'[\.\,\!\?\)\(;:¿║¡/\\\[\]]', ' ', entry.fullentry)
    #entry.fullentry_search = re.sub(r'  +', ' ', fullentry_search).lower()
    #print entry.fullentry_search.encode('utf-8')

    for a in annotations:
        entry.append_annotation(a[0], a[1], a[2], a[3])

    return entry


def insert_nondictdata_to_db(Session, data, book, filename):
    nondictdata = model.Nondictdata()
    nondictdata.startpage = data['startpage']
    nondictdata.endpage = data['endpage']
    nondictdata.title = data['title']
    file = open(filename, 'r')
    text = file.read()
    file.close()

    if re.search(u"<meta http-equiv=Content-Type content=\"text/html; charset=windows-1252\">", text):
        html = text.decode('windows-1252')
    elif re.search(u"<meta http-equiv=Content-Type content=\"text/html; charset=utf-8\">", text):
        html = text.decode('utf-8')
        
    if book.bibtex_key == 'burtch1983':
        html = re.sub(u"#001", u"ɨ", html)
        html = re.sub(u"#002", u"Ɨ", html)
    elif book.bibtex_key == 'thiesen1998':
        html = re.sub(u"#003", u"-̀", html)
        html = re.sub(u"#004", u"-́", html)
    html = unicodedata.normalize("NFD", html)
    nondictdata.data = html
    nondictdata.book = book

    component = Session.query(model.Component).filter_by(name=data['component']).first()
    if component == None:
        log.warn("Component not found, inserting nondictdata without component." )
    nondictdata.component = component

    Session.add(nondictdata)
    Session.commit()
    return nondictdata

def insert_dictdata_to_db(Session, data, book):
    dictdata = model.Dictdata()
    dictdata.startpage = data['startpage']
    dictdata.endpage = data['endpage']
    dictdata.src_language_bookname = data['src_language_bookname']
    dictdata.tgt_language_bookname = data['tgt_language_bookname']
    dictdata.book = book
    
    srclanguage = Session.query(model.Language).filter_by(name=data['src_language_name']).first()
    if srclanguage == None:
        #log.warn("Language " + b['src_language_name'] + " not found, inserting book " + b['title'].encode('ascii', errors='ingore') + " without source language." )
        print("Language %s not found, inserting book  without source language." % data['src_language_name'])
    dictdata.src_language = srclanguage
    
    tgtlanguage = Session.query(model.Language).filter_by(name=data['tgt_language_name']).first()
    if tgtlanguage == None:
        #log.warn("Language " + b['tgt_language_name'] + " not found, inserting book " + b['title'] + " without target language." )
        print("Language %s not found, inserting book without target language." % data['tgt_language_name'])
    dictdata.tgt_language = tgtlanguage

    component = Session.query(model.Component).filter_by(name=data['component']).first()
    if component == None:
        print("Component not found, inserting dictdata without component.")
    dictdata.component = component
    
    Session.add(dictdata)
    Session.commit()
    return dictdata

def insert_wordlistentry_to_db(Session, entry, annotation, page, column, concept_id, wordlistdata, languages):
    for lang in iter(entry):
        #entry_db = model.WordlistEntry()
        entry_db = process_line(entry[lang]["fullentry"], "wordlist")
        
        language_bookname = languages[lang]
        entry_db.wordlistdata = wordlistdata[language_bookname]
        entry_db.language = wordlistdata[language_bookname].language
        #entry_db.fullentry = entry[lang]['fullentry']
        entry_db.pos_on_page = entry[lang]['pos_on_page']
        entry_db.startpage = page
        entry_db.endpage = page
        entry_db.startcolumn = column
        entry_db.endcolumn = column
        
        concept_db =  model.meta.Session.query(model.WordlistConcept).filter_by(concept=concept_id).first()
        if concept_db == None:
            concept_db = model.WordlistConcept()
            concept_db.concept = concept_id
        
        entry_db.concept = concept_db
        
        #print entry_db.id
        #print entry_db.fullentry.encode("utf-8")
        
        if lang in annotation:
            inserted = []
            for a in annotation[lang]:
                if a['string'] not in inserted:
                    entry_db.append_annotation(a['start'], a['end'], a['value'], a['type'], a['string'])
                    inserted.append(a['string'])
                
        
        Session.add(entry_db)
        Session.commit()