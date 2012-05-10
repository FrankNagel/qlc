# -*- coding: utf8 -*-

languages = {
    'B 1': 'Sinsauru',
    'B 2': 'Asas',
    'B 3': 'Sausi',
    'B 4': 'Kesawai',
    'B 5': 'Dumpu',
    'B 6': 'Arawum',
    'B 7': 'Kolom',
    'B 8': 'Suroi',
    'B 9': 'Lemio',
    'B10': 'Pulabu',
    'B11': 'Yabong',
    'B12': 'Ganglau',
    'B13': 'Saep',
    'B14': 'Usino',
    'B15': 'Sumau',
    'B16': 'Urigina',
    'B17': 'Danaru',
    'B18': 'Usu',
    'B19': 'Erima',
    'B20': 'Duduela',
    'B21': 'Kwato',
    'B22': 'Rerau',
    'B23': 'Jilim',
    'B24': 'Yangulam',
    'B25': 'Bom',
    'B26': 'Male',
    'B27': 'Bongu',
    'B28': 'Songum',

    'C 1': 'Kare',

    'C 2': 'Girawa',
    'C 3': 'Munit',
    'C 4': 'Bemal',
    'C 5': 'Sihan',
    'C 6': 'Gumalu',
    'C 7': 'Isebe',
    'C 8': 'Amele',
    'C 9': 'Bau',
    'C10': 'Panim',

    'C11': 'Rapting',
    'C12': 'Wamas',
    'C13': 'Samosa',
    'C14': 'Murupi',
    'C15': 'Saruga',
    'C16': 'Nake',
    'C17': 'Mosimo',
    'C18': 'Garus',
    'C19': 'Yoidik',
    'C20': 'Rempi',
    'C21': 'Bagupi',
    'C22': 'Silopi',
    'C23': 'Utu',
    'C24': 'Mawan',
    'C25': 'Baimak',
    'C26': 'Matepi',
    'C27': 'Gal',
    'C28': 'Garuh',
    'C29': 'Kamba',

    'D 1': 'Mugil',

    'E 1': 'Dimir',
    'E 2': 'Malas',
    'E 3': 'Bunabun',
    'E 4': 'Korak',
    'E 5': 'Waskia',

    'F 1': 'Pay',
    'F 2': 'Pila',
    'F 3': 'Saki',
    'F 4': 'Tani',
    'F 5': 'Ulingan',
    'F 6': 'Bepour',
    'F 7': 'Moere',
    'F 8': 'Kowaki',
    'F 9': 'Mawak',
    'F10': 'Hinihon',
    'F11': 'Musar',
    'F12': 'Wanambre',
    'F13': 'Koguman',
    'F14': 'Abasakur',
    'F15': 'Wanuma',
    'F16': 'Yaben',
    'F17': 'Yarawata',
    'F18': 'Bilakura',
    'F19': 'Parawen',
    'F20': 'Ukuriguma',
    'F21': 'Amaimon',

    'G1': 'Sileibi',
    'G2': 'Katiati',
    'G3': 'Osum',
    'G4': 'Pondoma',
    'G5': 'Ikundun',
    'G6': 'Moresada',
    'G7': 'Wadaginam',

    'H1': 'Atemple',
    'H2': 'Angaua',
    'H3': 'Emerum',
    'H4': 'Musak',
    'H5': 'Paynamar',

    'I1': 'Isabi',
    'I2': 'Biyom',
    'I3': 'Tauya',
    'I4': 'Faita',

    'English': 'English'
}

languages_list = languages.values()

import sys, os, re
import collections
import codecs

sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.wordlistbooks

from paste.deploy import appconfig

import importfunctions

dictdata_path = 'quanthistling/dictdata'

def create_concepts_mapping():
    f = codecs.open("scripts/zgraggen_concepts.txt", "r", "utf-8")
    concepts_mapping = dict()
    book = None
    for l in f:
        if re.match("Parsing", l):
            match_book = re.match("Parsing ([^\.]*)\.\.\.", l)
            book = match_book.group(1)
        elif re.match("%%%", l):
            l = l.rstrip()
            match_parts = re.search("^%%%([^:]*): ([^-]*)->(.*)$", l)
            line = match_parts.group(1)
            concept = match_parts.group(3)
            #print line.encode("utf-8")
            #print u"  {0}".format(concept).encode("utf-8")
            if line == None or concept == None or book == None:
                print u"Error while parsing concept mapping: {0}".format(l).encode("utf-8")
                sys.exit(1)
            concepts_mapping[(book, line)] = concept
            
    return concepts_mapping

def main(argv):
    #book_bibtex_key = u"zgraggen1980"
    bibtex_keys_in_file = [ 'zgraggen1980', 'zgraggen1980b', 'zgraggen1980c', 'zgraggen1980d' ]
    combined_bibtex_key = 'zgraggen1980'
    
    if len(argv) < 2:
        print "call: importzgraggen1980.py ini_file"
        exit(1)
    
    ini_file = argv[1]
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)
    
    concepts_mapping = create_concepts_mapping()

    for b in quanthistling.dictdata.wordlistbooks.list:
        if b['bibtex_key'] == bibtex_keys_in_file[0]:
            wordlistbookdata = b

    importfunctions.delete_book_from_db(Session, combined_bibtex_key)
    book = importfunctions.insert_book_to_db(Session, wordlistbookdata)

    poses_on_page = collections.defaultdict(int)
    concept_ids = collections.defaultdict(int)
    

    wordlistdata = {}
    for book_bibtex_key in bibtex_keys_in_file:
        print "Parsing {0}...".format(book_bibtex_key)
        wordlistbook = {}
        #book_bibtex_key = argv[1].decode("utf-8")
    
        for b in quanthistling.dictdata.wordlistbooks.list:
            if b['bibtex_key'] == book_bibtex_key:
                wordlistbookdata = b

        for data in wordlistbookdata['wordlistdata']:
            #print data['language_bookname']
            #print wordlistdata.keys()
            if data['language_bookname'] in wordlistdata.keys():
                #print "Is here"
                d = wordlistdata[data['language_bookname']]
            else:
                #print "is not here"
                d = importfunctions.insert_wordlistdata_to_db(Session, data, book)
                wordlistdata[data['language_bookname']] = d
    
    
        wordlistfile = open(os.path.join(dictdata_path, wordlistbookdata['file']), 'r')
        
        page                        = 0
        page_new                    = 0
        column                      = 0
        column_new                  = 0
        pos_on_page                 = 1
        current_entry_text          = ''
        concept_id                  = 0
        annotation                  = {}
        entry                       = {}
        
        re_page = re.compile(u"\[Seite (\d+)\]$")
        re_column = re.compile(u"\[Spalte (\d+)\]$")
        re_english = re.compile(u"<i>([^<]*)</i>")
        re_html = re.compile(u"</?\w{1,2}>")
        re_singledash = re.compile(u"(?<!-)-(?!-)")
    
        for line in wordlistfile:        
            
            l = line.strip()
            #l = unescape(l)
            l = l.decode('utf-8')
            
            l = re.sub(u"̧", u"̩", l)
            l = re.sub(u"ӕ", u"æ", l)
            l = re.sub(u"[ǝә]", u"ə", l)
            l = re.sub(u"ε", u"ɛ", l)
            l = re.sub(u"ι", u"ɩ", l)
            l = re.sub(u"O̵", u"o̵", l)
            l = re.sub(u"ͥ", u"\u2071", l)
            l = re.sub(u"\?", u"ˀ", l)
            #re.sub(u"abʌ:ni, oυ-, on-", u"abʌ:ni, ou-, on-", l)
    
            if re.search(u'^<p>', l):
                l = re.sub(u'</?p>', '', l)
                #print l.encode("utf-8")
                
                # parse page and line number
                if re_page.match(l):
                    poses_on_page[page] = pos_on_page
                    match_page = re_page.match(l)
                    page_new = int(match_page.group(1))
                    pos_on_page = poses_on_page[page_new] + 1
                    print "Parsing page {0}".format(page_new)
                #if page_new != 39:
                #    continue
                if re_column.match(l):
                    match_column = re_column.match(l)
                    column_new =  int(match_column.group(1))
                    print "Column {0}".format(column)
                elif re_english.match(l):
                    if entry != {}:
                        if book_bibtex_key != "zgraggen1980":
                            del(entry['English'])
                            if entry.has_key('Spanish'):
                                del(entry['Spanish'])
                        importfunctions.insert_wordlistentry_to_db(Session, entry, annotation, page, column, concept_id, wordlistdata, languages)
                    annotation = {}
                    entry = {}
                    page = page_new
                    column = column_new
                    match_english = re_english.match(l)
                    meaning_english = match_english.group(1)
                    meaning_english = re.sub("(?:\d?\d|\*) ?$", "", meaning_english)
                    meaning_english = re.sub("^\*", "", meaning_english)
                    print "  English: %s" % meaning_english.encode("utf-8")
                    entry['English'] = {}
                    entry['English']['fullentry'] = meaning_english
                    entry['English']['pos_on_page'] = pos_on_page
                    annotation['English'] = []
                    
                    if concepts_mapping.has_key((book_bibtex_key, l)):
                        concept_id = concepts_mapping[(book_bibtex_key, l)]
                        print "used modified concept ID."
                    else:
                        concept = meaning_english.upper()
                        concept = re.sub(u"^\* ?", u"", concept)
                        concept = re.sub(u" ?\(", u"_", concept)
                        concept = re.sub(u"\) ?", u"_", concept)
                        concept = re.sub(u", ?", u"_", concept)
                        concept = re.sub(u" +$", u"", concept)
                        concept = re.sub(u" ", u"_", concept)
                        concept = re.sub(u"_$", "", concept)
                        concept = re.sub(u"^_", "", concept)
                        concept_id = u"{0}".format(concept)
    
                    start = 0
                    end = len(meaning_english)
                    match_bracket = re.search(" ?\([^)]*\) ?$", meaning_english)
    
                    if match_bracket:
                        end = end - len(match_bracket.group(0))
    
                    match_star = re.match("\*", meaning_english)
                    if match_star:
                        start = 1
                        
                    meaning_english = meaning_english[start:end]
                    
                    start_new = 0
                    for match in re.finditer(u"(?:, |$)", meaning_english):
                        end_new = match.start(0)
                        a = {}
                        a['start'] = start + start_new
                        a['end'] = start + end_new
                        a['value'] = 'counterpart'
                        a['type'] = 'dictinterpretation'
                        a['string'] = meaning_english[start_new:end_new]
                        annotation['English'].append(a)
                        start_new = match.end(0)
                    
                    pos_on_page = pos_on_page + 1
                else:
                    parts = l.split("\t")
                    language = parts[0]
                    
                    if language not in languages:
                        continue
                    
                    if len(parts) == 3:
                        fullentry = parts[2]
                    elif len(parts) == 2:
                        if parts[1] in languages_list:
                            fullentry = ""
                        else:
                            fullentry = parts[1]
                        
                    else:
                        continue

                    fullentry = re.sub("^-- ", "", fullentry)
                    
                    entry[parts[0]] = {}
                    annotation[parts[0]] = []
                    entry[parts[0]]['fullentry'] = l
                    entry[parts[0]]['pos_on_page'] = pos_on_page
                    start_entry = len(l) - len(fullentry)
                    end_entry = len(l)
                    start_new = 0
                    if len(fullentry) > 0:
                        for match in re.finditer(u"(?:[,;] |$)", fullentry):
                            mybreak = False
                            # are we in a bracket?
                            for m in re.finditer(r'\(.*?\)', fullentry):
                                if match.start(0) > m.start(0) and match.end(0) < m.end(0):
                                    mybreak = True
                                
                            if not mybreak:
                                end_new = match.start(0)
                                
                                match_bracket = re.search(" ?\(([^)]*)\) ?$", fullentry[start_new:end_new])
                                if match_bracket:
                                    # if there is a number in the bracket then remove it
                                    if re.search("(?:[\dmfv]|pl)", match_bracket.group(1)):
                                        end_new = end_new - len(match_bracket.group(0))
            
                                match_dashes1 = re.search("^--? ?", fullentry[start_new:end_new])
                                if match_dashes1:
                                    start_new = start_new + len(match_dashes1.group(0))
                                    
                                match_dashes2 = re.search("--?,?$", fullentry[start_new:end_new])
                                if match_dashes2:
                                    end_new = end_new - len(match_dashes2.group(0))
                                    
                                match_bracket2 = re.search("\(([^)]*)\)", fullentry[start_new:end_new])

                                #if concept == 'TAIL' and parts[0] == 'C25':
                                #    print
                                #    print fullentry[start_new:end_new].encode("utf-8")
                                #    print annotation[parts[0]]
                                #    print
                                    
                                if match_bracket2:
                                    a = {}
                                    a['start'] = start_entry + start_new
                                    a['end'] = start_entry + end_new
                                    a['value'] = 'counterpart'
                                    a['type'] = 'dictinterpretation'
                                    annotation_string = fullentry[start_new:start_new+match_bracket2.start(0)] + match_bracket2.group(1) + fullentry[start_new + match_bracket2.end(0):end_new]
                                    annotation_string = re_html.sub("", annotation_string)
                                    annotation_string = re_singledash.sub("", annotation_string)
                                    #if concept == 'TAIL' and parts[0] == 'C25':
                                    #    print annotation_string

                                    a['string'] = annotation_string
                                    annotation[parts[0]].append(a)
        
                                    a2 = {}
                                    a2['start'] = start_entry + start_new
                                    a2['end'] = start_entry + end_new
                                    a2['value'] = 'counterpart'
                                    a2['type'] = 'dictinterpretation'
                                    #annotation_string = fullentry[start_new+len(match_bracket2.group(0)):end_new]
                                    annotation_string = fullentry[start_new:start_new+match_bracket2.start(0)] + fullentry[start_new+match_bracket2.end(0):end_new]
                                    annotation_string = re_html.sub("", annotation_string)
                                    annotation_string = re_singledash.sub("", annotation_string)
                                    #if concept == 'TAIL' and parts[0] == 'C25':
                                    #    print annotation_string
                                    
                                    a2['string'] = annotation_string
                                    annotation[parts[0]].append(a2)
                                                                        
                                #match_bracket3 = re.search("\(([^)]*)\) ?$", fullentry[start_new:end_new])
                                #if match_bracket3:
                                #    a = {}
                                #    a['start'] = start_entry + start_new
                                #    a['end'] = start_entry + end_new
                                #    a['value'] = 'counterpart'
                                #    a['type'] = 'dictinterpretation'
                                #    annotation_string =  fullentry[start_new:start_new+match_bracket3.start(0)] + match_bracket3.group(1)
                                #    annotation_string = re_html.sub("", annotation_string)
                                #    annotation_string = re_singledash.sub("", annotation_string)
                                #    a['string'] = annotation_string
                                #    annotation[parts[0]].append(a)
                                #
                                #    a2 = {}
                                #    a2['start'] = start_entry + start_new
                                #    a2['end'] = start_entry + end_new
                                #    a2['value'] = 'counterpart'
                                #    a2['type'] = 'dictinterpretation'
                                #    annotation_string = fullentry[start_new:start_new+match_bracket3.start(0)]
                                #    annotation_string = re_html.sub("", annotation_string)
                                #    annotation_string = re_singledash.sub("", annotation_string)
                                #    a2['string'] = annotation_string
                                #    annotation[parts[0]].append(a2)

                                else:
                                    a = {}
                                    a['start'] = start_entry + start_new
                                    a['end'] = start_entry + end_new
                                    a['value'] = 'counterpart'
                                    a['type'] = 'dictinterpretation'
                                    annotation_string = fullentry[start_new:end_new]
                                    annotation_string = re_html.sub("", annotation_string)
                                    annotation_string = re_singledash.sub("", annotation_string)
                                    a['string'] = annotation_string
                                    annotation[parts[0]].append(a)
        
                                #if concept == 'TAIL' and parts[0] == 'C25':
                                #    print annotation[parts[0]]

                                start_new = match.end(0)
                    
                    
                    pos_on_page += 1
    
        
        Session.commit()
        wordlistfile.close()   

    Session.close()

if __name__ == "__main__":
    main(sys.argv)
