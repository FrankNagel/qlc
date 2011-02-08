# -*- coding: utf8 -*-

import re
from quanthistling import model

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

def insert_wordlistdata_to_db(Session, data, book):
    wordlistdata = model.Wordlistdata()
    wordlistdata.startpage = data['startpage']
    wordlistdata.endpage = data['endpage']
    wordlistdata.language_bookname = data['language_bookname']
    wordlistdata.book = book
    
    if data['language_name'] != "":
        language = Session.query(model.Language).filter_by(name=data['language_name']).first()
        if language == None:
            #log.warn("Language " + b['src_language_name'] + " not found, inserting book " + b['title'].encode('ascii', errors='ingore') + " without source language." )
            print("Language %s not found, inserting book  without source language." % data['language_name'])
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
            
    entry.fullentry = fullentry
    #fullentry_search = re.sub(r'[\.\,\!\?\)\(;:¿║¡/\\\[\]]', ' ', entry.fullentry)
    #entry.fullentry_search = re.sub(r'  +', ' ', fullentry_search).lower()
    #print entry.fullentry_search.encode('utf-8')

    for a in annotations:
        entry.append_annotation(a[0], a[1], a[2], a[3])

    return entry