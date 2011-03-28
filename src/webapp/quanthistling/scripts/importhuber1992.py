# -*- coding: utf8 -*-

languages = {
    'AC' : u'achagua',
    'AW' : u'awa',
    'BA' : u'epena basurudó',
    'giacone' : u'giacone',
    'BI' : u'barí',
    'BN' : u'baniva',
    'BO' : u'bora',
    'BR' : u'bará',
    'BS' : u'barasana',
    'CA' : u'cabiyarí',
    'CH' : u'cha\'palaachi',
    'CI' : u'cuiba',
    'CJ' : u'carijona',
    'CL' : u'chimila',
    'CM' : u'embera chamí',
    'CP' : u'carapana',
    'CR' : u'curripaco',
    'CT' : u'catío',
    'CU' : u'cubeo',
    'DE' : u'desano',
    'DM' : u'dí̵mɨna',
    'DR' : u'embera Darién',
    'EP' : u'epena Saija',
    'GH' : u'guahibo',
    'GU' : u'guambiano',
    'GY' : u'guayabero',
    'IK' : u'ika',
    'IN' : u'inga',
    'JU' : u'jupda',
    'JT' : u'jitnu',
    'KG' : u'koreguaje',
    'KK' : u'kakua',
    'KO' : u'kogui',
    'KS' : u'kamsá',
    'MA' : u'macuna',
    'NK' : u'nukak',
    'MN' : u'witoto mɨnɨca',
    u'MÑ' : u'miraña',
    'MR' : u'witoto murui',
    'MU' : u'muinane',
    'NP' : u'witoto nɨpode',
    'OC' : u'ocaina',
    'OR' : u'orejón',
    'PA' : u'páez',
    'PL' : u'playero',
    'PP' : u'piapoco',
    'PU' : u'puinave',
    'PY' : u'piratapuyo',
    'RE' : u'resígaro',
    'SE' : u'secoya',
    'SI' : u'siona',
    'SL' : u'sáliba',
    'SR' : u'siriano',
    'TA' : u'tatuyo',
    'TC' : u'tucano',
    'TD' : u'embera Tadó',
    'TM' : u'tanimuca',
    'TN' : u'tunebo central',
    'TO' : u'tariano',
    'TP' : u'tsafiqui pila',
    'TR' : u'totoró',
    'TY' : u'tuyuca',
    'WA' : u'waimaja',
    'WM' : u'wounaan',
    'WN' : u'wanano',
    'WY' : u'wayuu',
    'YC' : u'yucuna',
    'YK' : u'yukpa',
    'YR' : u'yurutí',
    'English' : 'English',
    'INGLES' : 'English',
    u'Español' : u'Español',
    u'ESPAÑOL' : u'Español'
}

families = {
    'CHOCO' : {
        'DR' : u'embera Darién',
        'CT' : u'catío',
        'CM' : u'embera chamí',
        'TD' : u'embera Tadó',
        'EP' : u'epena Saija',
        'BA' : u'epena basurudó',
        'WM' : u'wounaan',        
    },
    'TUCANO' : {
        'TC' : u'tucano',
        'WN' : u'wanano',
        'PY' : u'piratapuyo',
        'WA' : u'waimaja',
        'BR' : u'bará',
        'TY' : u'tuyuca',
        'YR' : u'yurutí',
        'DE' : u'desano',
        'SR' : u'siriano',
        'TA' : u'tatuyo',
        'CP' : u'carapana',
        'MA' : u'macuna',
        'BS' : u'barasana',
        'TM' : u'tanimuca',
        'CU' : u'cubeo',
        'KG' : u'koreguaje',
        'SE' : u'secoya',
        'SI' : u'siona',
        'OR' : u'orejón',        
    },
    'ARAWAK' : {
        'WY' : u'wayuu',
        'AC' : u'achagua',
        'CR' : u'curripaco',
        'PP' : u'piapoco',
        'YC' : u'yucuna',
        'TO' : u'tariano',
        'CA' : u'cabiyarí',
        'BN' : u'baniva',
        'RE' : u'resígaro',        
    },
    'GUAHIBO' : {
        'PL' : u'playero',
        'GH' : u'guahibo',
        'CI' : u'cuiba',
        'JT' : u'jitnu',
        'GY' : u'guayabero',        
    },
    'WITOTO' : {
        'MR' : u'witoto murui',
        'MN' : u'witoto mɨnɨca',
        'NP' : u'witoto nɨpode',
        'OC' : u'ocaina',
        'MU' : u'muinane',
        'BO' : u'bora',
        u'MÑ' : u'miraña',        
    }
}

import sys, os, re
sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.wordlistbooks

from paste.deploy import appconfig

import importfunctions

dictdata_path = 'quanthistling/dictdata'

def remove_parts_head(str, s, e):
    start = s
    end = e
    subsubstr = str
    match_end = re.search(u"(?:,?† ?| Véase .*?| ?\(SP\??\) ?)$", subsubstr)
    if match_end:
        end = end - len(match_end.group(0))
        subsubstr = subsubstr[:-len(match_end.group(0))]
    match_start = re.match(r"^(?: ?[+=~] ?|\.\.\. ?)", subsubstr)
    if match_start:
        start = start + len(match_start.group(0))
        subsubstr = subsubstr[len(match_start.group(0)):]
    return [start, end]

def remove_parts_head_characters(str):
    h = re.sub(u"\(?(?:\-|–|=|\.\.\.|\!|ˈ|\.|†)\)?", "", str)
    return h

def remove_parts_head_brackets(str):
    h = str
    while re.search(u" ?(?:\([^)]+\)|‘[^’]+’) ?$", h):
        h = re.sub(u" ?(?:\([^)]+\)|‘[^’]+’) ?$", "", h)
    h = re.sub(u" ?=.*$", "", h)
    h = re.sub("[()]", "", h)
    h = re.sub(" +", " ", h)
    return h

def insert_entry_to_db(entry, annotation, page, concept_id, wordlistdata):
    for lang in iter(entry):
        #entry_db = model.WordlistEntry()
        entry_db = importfunctions.process_line(entry[lang]["fullentry"], "wordlist")
        
        language_bookname = languages[lang]
        entry_db.wordlistdata = wordlistdata[language_bookname]
        entry_db.language = wordlistdata[language_bookname].language
        entry_db.fullentry = entry[lang]['fullentry']
        entry_db.pos_on_page = entry[lang]['pos_on_page']
        entry_db.startpage = page
        entry_db.endpage = page
        entry_db.startcolumn = 1
        entry_db.endcolumn = 1
        
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

def create_annotation(start, end, value, type, string):
    match_spaces = re.match(" +", string)
    if match_spaces:
        start = start + len(match_spaces.group(0))
        string = re.sub("^ +", "", string)
    match_spaces = re.search(" +$", string)
    if match_spaces:
        end = end - len(match_spaces.group(0))
        string = re.sub(" +$", "", string)
    
    if len(string) == 0:
        return []
    
    annotations = []

    a = {
        'start' : start,
        'end' : end,
        'value' : value,
        'type' : type,
        'string' : string
    }
    
    annotations.append(a)
    
    if value == "footnote" and re.search("\+", string):
        match_heads = re.search(u"\+ ?([^;]+)(?:;|$)", string)
        start_head = match_heads.start(1)
        for match_head in re.finditer(u"(?:, ?|$)", string[match_heads.start(1):match_heads.end(1)]):
            end_head = match_heads.start(1) + match_head.start(0)
            string_head = remove_parts_head_characters(string[start_head:end_head])
            string_head = remove_parts_head_brackets(string_head)
            if not re.match("Giacone:", string_head):
                a = {
                    'start' : start + start_head,
                    'end' : start + end_head,
                    'value' : "counterpart",
                    'type' : "dictinterpretation",
                    'string' : string_head
                }
                annotations.append(a)
            start_head = match_heads.start(1) + match_head.end(0)
    
    #print annotations
    return annotations

def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id, 16))
    except:
        return id

def decode_unicode_references(data):
    return re.sub("&amp;(\w+?);", _callback, data)

def correct_line(l):
    ret = l
    ret = re.sub(u"<p><b>Bt</b>", u"<p><b>BI</b>", ret)
    ret = re.sub(u"<p><b>St</b>", u"<p><b>SI</b>", ret)
    ret = re.sub(u"<p><b>DM ʒ</b>", u"<p><b>DM</b> ʒ", ret)
    ret = re.sub(u"<p><b>Mac</b><u><b>ú-Puinave</b></u></p>", u"<p><b>Macú-Puinave</b></p>", ret)
    ret = re.sub(u"<p><b>Mac</b>ú-Puinave</p>", u"<p><b>Macú-Puinave</b></p>", ret)
    ret = re.sub(u"<p><b>(\w\w) –</b>", r"<p><b>\1</b>" + u" –", ret)
    ret = re.sub(u"<p><b>(\w\w) </b>", r"<p><b>\1</b> ", ret)
    ret = re.sub(u"<p><b>mr</b>", u"<p><b>MR</b>", ret)
    ret = re.sub(u"<p><b>M</b>Ñ", u"<p><b>MÑ</b>", ret)
    ret = re.sub(u"<p><b>OM</b>", u"<p><b>DM</b>", ret)
    ret = re.sub(u"<p><b>GII</b>", u"<p><b>GH</b>", ret)
    ret = re.sub(u"<p><b>OE</b>", u"<p><b>DE</b>", ret)
    ret = re.sub(u"<p><b>MH</b>", u"<p><b>WA</b>", ret)
    ret = re.sub(u"<p><b>S</b>áliba-Piaroa</p>", u"<p><b>Sáliba-Piaroa</b></p>", ret)
    ret = re.sub(u"<p><b>Choc</b>ó</p>", u"<p><b>Chocó</b></p>", ret)
    ret = re.sub(u"<p><b>Choc</b>ó†</p>", u"<p><b>Chocó†</b></p>", ret)
    ret = re.sub(u"<p><b>Kams</b>á</p>", u"<p><b>Kamsá</b></p>", ret)
    ret = re.sub(u"<p><b>GUAIIIBO</b>", u"<p><b>GUAHIBO</b>", ret)
    ret = re.sub(u"<p><b>CHOC,MU</b>", u"<p><b>CHOCO,MU</b>", ret)
    ret = re.sub(u"<p><b>CT mogara oromá</b></p>", u"<p><b>CT</b> mogara oromá</p>", ret)
    ret = re.sub(u"<p><b>253,CHOCO,WITOTO,WJ</b>", u"<p><b>253,CHOCO,WITOTO,WY</b>", ret)
    ret = re.sub(u"<p><b>CIIOCO</b>", u"<p><b>CHOCO</b>", ret)
    ret = re.sub(u"<p><b>CHOCO, GUAHIBO</b>", u"<p><b>CHOCO,GUAHIBO</b>", ret)
    ret = re.sub(u"<p><b>BR,BS,CP,TC,TY,JR</b>", u"<p><b>BR,BS,CP,TC,TY,YR</b>", ret)
    ret = re.sub(u"<p><b>CI ba-pó-n†</b>", u"<p><b>CI</b> ba-pó-n†", ret)
    ret = re.sub(u"<p><b>CI ba-pó-n†</b>", u"<p><b>CI</b> ba-pó-n†", ret)

    ret = re.sub(u"<p><b>CH</b> lᴶunu</p>", u"<p><b>CH</b> lʲunu</p>", ret)
    ret = re.sub(u"<p><b>CH</b> tᴶaiju</p>", u"<p><b>CH</b> tʲaiju</p>", ret)

    ret = re.sub(u"<p><b>PU</b> bigᴶik</p>", u"<p><b>PU</b> bigɺik</p>", ret)
    ret = re.sub(u"<p><b>PU</b> mo hĩ̵mka huᴶe</p>", u"<p><b>PU</b> mo hĩ̵m̃ka huɺe</p>", ret)
    ret = re.sub(u"<p><b>PU</b> ha moᴶuk tɨjot</p>", u"<p><b>PU</b> ha moɺuk tɨjot</p>", ret)

    ret = re.sub(u"<p><b>WA</b> ˈtúu pua\(-\), há’dé\(-\)</p>", u"<p><b>WA</b> ˈtúu pua(-), háˈdé(-)</p>", ret)

    ret = re.sub(u"</?i>", "", ret)
    ret = re.sub(u"ι", u"ɩ", ret)
    ret = re.sub(u"⍳", u"ɩ", ret)
    ret = re.sub(u"ı", u"ɩ", ret)
    ret = re.sub(u"ᴵ", u"¹", ret)
    ret = re.sub(u"̅", u"̄", ret)
    ret = re.sub(u"ß", u"β", ret)
    ret = re.sub(u"βɯ́́́́́́́ɯ́́́́́́́ríʔií", u"βɯ́ɯ́ríʔií", ret)
    ret = re.sub(u"βɯ́́́́́́́ɯ́́́́́́́ríʔií", u"βɯ́ɯ́ríʔií", ret)
    ret = re.sub(u"Giaeone", u"Giacone", ret)
    ret = re.sub(u"tɨmɉ-kɨna", u"tɨmɨ-kɨna", ret)
    ret = re.sub(u"áikkalawa~a", u"áikkalawa-a", ret)
    ret = re.sub(u"ẽse~ʔh", u"ẽse-ʔh", ret)
    ret = re.sub(u"(?<!MN)̃", u"̄", ret)
    return ret


def main(argv):
    book_bibtex_key = u"huber1992"
    
    if len(argv) < 2:
        print "call: importhuber1992.py ini_file"
        exit(1)
    
    ini_file = argv[1]
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    wordlistbook = {}
    for b in quanthistling.dictdata.wordlistbooks.list:
        if b['bibtex_key'] == book_bibtex_key:
            wordlistbookdata = b

    importfunctions.delete_book_from_db(Session, book_bibtex_key)
    
    book = importfunctions.insert_book_to_db(Session, wordlistbookdata)

    wordlistdata = {}
    for data in wordlistbookdata['wordlistdata']:
        d = importfunctions.insert_wordlistdata_to_db(Session, data, book)
        wordlistdata[data['language_bookname']] = d

    wordlistfile = open(os.path.join(dictdata_path, wordlistbookdata['file']), 'r')
    
    page                        = 0
    pos_on_page                 = 1
    current_entry_text          = ''
    line_in_page                = 0
    concept_id                  = 0
    in_footnote                 = False
    annotation                  = {}
    entry                       = {}

    for line in wordlistfile:
        line_in_page = line_in_page + 1
        
        l = line.strip()
        #l = unescape(l)
        l = l.decode('utf-8')
        
        l = decode_unicode_references(l)
        l = re.sub(u"&amp;", u"&", l)
        l = re.sub(u"<\w></\w>", u"", l)
        l = re.sub(u"#001", u"ᴵ", l)
        l = re.sub(u"#002", u"ˣ", l)
        l = re.sub(u"#003", u"t", l)
        l = re.sub(u"#004", u"t", l)
        l = re.sub(u"<b>M</b>Ñ", u"<b>MÑ</b>", l)
        
        l = correct_line(l)
        l = re.sub(u"'", u"ˈ", l)
        
        if re.search(u'^<p>', l):
            l = re.sub(u'</?p>', '', l)
            #print l.encode("utf-8")
            
            # parse page and line number
            if re.match(u'^\[\d+\]$', l):
                if entry != {}:
                    if "giacone" in annotation:
                        entry["giacone"] = entry["TO"]
                        entry["giacone"]["pos_on_page"] = pos_on_page
                        for a in annotation["TO"]:
                            if a['type'] == "pagelayout":
                                annotation["giacone"].append(a)
                        pos_on_page = pos_on_page + 1
                    insert_entry_to_db(entry, annotation, page, concept_id, wordlistdata)
                number = re.sub(u'[\[\]]', '', l)
                page = int(number)
                line_in_page = 1
                pos_on_page = 1
                in_footnote = False
                annotation = {}
                entry = {}
                print "Parsing page %i" % page
            elif line_in_page == 3:
                meaning_spanish = re.sub(u'(?:</?b>|†)', '', l)
                print "  Spanish: %s" % meaning_spanish.encode("utf-8")
                entry[u'Español'] = {}
                entry[u'Español']['fullentry'] = meaning_spanish
                entry[u'Español']['pos_on_page'] = pos_on_page
                annotation[u'Español'] = []
                
                meaning_spanish = re.sub(u"!", "", meaning_spanish)
                start = 0
                end = 0
                for match in re.finditer(u"(?:, |; | ~ |$)", meaning_spanish):
                    end = match.start(0)
                    a = {}
                    a['start'] = start
                    a['end'] = end
                    a['value'] = 'counterpart'
                    a['type'] = 'dictinterpretation'
                    a['string'] = meaning_spanish[start:end]
                    annotation[u'Español'].append(a)
                    start = match.end(0)
                    
                pos_on_page = pos_on_page + 1
            elif line_in_page == 4:
                id = int(re.sub(u'(?:</?b>|†)', '', l))
                print "  ID: %i" % id
            elif line_in_page == 5:
                meaning_english = re.sub(u'(?:</?b>|†)', '', l)
                print "  English: %s" % meaning_english.encode("utf-8")
                entry['English'] = {}
                entry['English']['fullentry'] = meaning_english
                entry['English']['pos_on_page'] = pos_on_page
                annotation['English'] = []

                meaning_english = re.sub(u"!", "", meaning_english)
                start = 0
                end = 0
                for match in re.finditer(u"(?:, |; | ~ |$)", meaning_english):
                    end = match.start(0)
                    a = {}
                    a['start'] = start
                    a['end'] = end
                    a['value'] = 'counterpart'
                    a['type'] = 'dictinterpretation'
                    a['string'] = meaning_english[start:end]
                    annotation['English'].append(a)
                    start = match.end(0)
                pos_on_page = pos_on_page + 1
                concept_id = "%s_%s" % (meaning_spanish.upper(), meaning_english.upper())
            # parse data
            elif re.search(u"\[Fu[ßβ]noten", l):
                in_footnote = True
            elif re.match(u'^<p/>$', l) or re.match(u'^<b>[^ ]{3,}(?: ?†)?</b>(?: ?†)?$', l):
                pass
            else:
                if in_footnote:
                    match = re.match(u"^(?:<i>)?<b>(.*?)</b>(?:</i>)? ?(.*)$", l)
                    if match:
                        language_string = match.group(1).strip()
                        languages_entry = language_string.split(",");
                        for language in languages_entry:
                            if language.upper() in families:
                                for l in families[language]:

                                    a_newline = { 'start' : len(entry[l]['fullentry']), 'end' : len(entry[l]['fullentry']), 'value' : 'newline', 'type' : 'pagelayout', 'string' : '' }
                                    annotation[l].append(a_newline)

                                    len_entry = len(entry[l]['fullentry'])
                                    entry[l]['fullentry'] = entry[l]['fullentry'] + " " + match.group(2)
                                    #a = {
                                    #    'start' : len_entry,
                                    #    'end' : len(entry[l]['fullentry']),
                                    #    'value' : 'footnote',
                                    #    'type' : 'dictinterpretation',
                                    #    'string' : match.group(2)
                                    #}
                                    a_s = create_annotation(len_entry, len(entry[l]['fullentry']), "footnote", "dictinterpretation", match.group(2))
                                    annotation[l].extend(a_s)
                            elif re.match(u"\d+$", language):
                                for l in ( u'Español', 'English' ):

                                    a_newline = { 'start' : len(entry[l]['fullentry']), 'end' : len(entry[l]['fullentry']), 'value' : 'newline', 'type' : 'pagelayout', 'string' : '' }
                                    annotation[l].append(a_newline)

                                    len_entry = len(entry[l]['fullentry'])
                                    entry[l]['fullentry'] = entry[l]['fullentry'] + " " + match.group(2)
                                    #a = {
                                    #    'start' : len_entry,
                                    #    'end' : len(entry[l]['fullentry']),
                                    #    'value' : 'footnote',
                                    #    'type' : 'dictinterpretation',
                                    #    'string' : match.group(2)
                                    #}
                                    a_s = create_annotation(len_entry + 1, len(entry[l]['fullentry']), "footnote", "dictinterpretation", match.group(2))
                                    annotation[l].extend(a_s)
                            elif language in languages:
                                l = language
                                if language == u"ESPAÑOL":
                                    l = u'Español'
                                elif language == "INGLES":
                                    l = 'English'

                                a_newline = { 'start' : len(entry[l]['fullentry']), 'end' : len(entry[l]['fullentry']), 'value' : 'newline', 'type' : 'pagelayout', 'string' : '' }
                                annotation[l].append(a_newline)
                                
                                len_entry = len(entry[l]['fullentry'])
                                entry[l]['fullentry'] = entry[l]['fullentry'] + " " + match.group(2)
                                #a = {}
                                #a['start'] = len(entry[l]['fullentry'])
                                #a['end'] = len(entry[l]['fullentry']
                                #a['value'] = 'footnote'
                                #a['type'] = 'dictinterpretation'
                                #a['string'] = match.group(2)
                                a_s = create_annotation(len_entry + 1, len(entry[l]['fullentry']), "footnote", "dictinterpretation", match.group(2))
                                annotation[l].extend(a_s)
                                
                                if language == "TO":
                                    if re.search("Giacone:", match.group(2)):
                                        annotation["giacone"] = []
                                        string = match.group(2)
                                        match_heads = re.search(u"Giacone: ?(.+)$", string)
                                        if match_heads:
                                            start_head = match_heads.start(1)
                                            for match_head in re.finditer(u"(?:[;,] ?|$)", string[match_heads.start(1):match_heads.end(1)]):
                                                end_head = match_heads.start(1) + match_head.start(0)
                                                #print string[start_head:end_head]
                                                string_head = remove_parts_head_characters(string[start_head:end_head])
                                                string_head = remove_parts_head_brackets(string_head)
                                                #print string_head.encode("utf-8")
                                                if not re.match(" +$", string_head):
                                                    a = {
                                                        'start' : start_head + len_entry + 1,
                                                        'end' : end_head + len_entry + 1,
                                                        'value' : "counterpart",
                                                        'type' : "dictinterpretation",
                                                        'string' : string_head
                                                    }
                                                    annotation["giacone"].append(a)
                                                start_head = match_heads.start(1) + match_head.end(0)
                                        
                            else:
                                print "Error: Language %s not defined." % language.encode("utf-8")
                else:
                    match = re.match(u"^(?:<i>)?<b>(.*?)</b>(?:</i>)? ?(.*)$", l)
                    if match:
                        if len(match.groups()) < 2:
                            print "Error: Not two groups: %s" % l                                
                        language_string = match.group(1).strip()
                        languages_entry = language_string.split(",");
                        for language in languages_entry:
                            if not language in languages:
                                print "Error: Language %s not defined." % language.encode("utf-8")
                            else:
                                annotation[language] = []
                                entry[language] = {}
                                entry[language]['fullentry'] = match.group(2)
                                entry[language]['pos_on_page'] = pos_on_page
                                pos_on_page = pos_on_page + 1
                                strpos = remove_parts_head(match.group(2), 0, len(match.group(2)))
                                
                                match_spanishloan = re.search(u"\(SP\??\)", match.group(2))
                                if match_spanishloan:
                                    #a = {}
                                    #a['start'] = match_spanishloan.start(0)
                                    #a['end'] = match_spanishloan.end(0)
                                    #a['value'] = 'stratum'
                                    #a['type'] = 'dictinterpretation'
                                    #a['string'] = "Spanish loanword"
                                    a_s = create_annotation(match_spanishloan.start(0), match_spanishloan.end(0), "stratum", "dictinterpretation", "Spanish loanword")
                                    annotation[language].extend(a_s)
                                
                                head_string = match.group(2)[strpos[0]:strpos[1]]
                                start = 0
                                end = 0
                                for match in re.finditer(u"(?:, ?|; | ~ |$)", head_string):
                                    end = match.start(0)
                                    head = remove_parts_head_characters(head_string[start:end])
                                    if head != "":
                                        match_bracket = re.search(u"\(([^)]+?)\) ?$", head)
                                        if match_bracket:
                                            head_base = head[:match_bracket.start(0)]
                                            #a = {}
                                            #a['start'] = strpos[0] + start
                                            #a['end'] = strpos[0] + end
                                            #a['value'] = 'counterpart'
                                            #a['type'] = 'dictinterpretation'
                                            #a['string'] = head_base
                                            a_s = create_annotation(strpos[0] + start, strpos[0] + end, "counterpart", "dictinterpretation", head_base)
                                            annotation[language].extend(a_s)
                                            head = head_base + match_bracket.group(1)
                                            
                                        match_bracket = re.search(u"^\(([^)]+?)\)", head)
                                        if match_bracket:
                                            head_base = head[match_bracket.end(0):]
                                            #a = {}
                                            #a['start'] = strpos[0] + start
                                            #a['end'] = strpos[0] + end
                                            #a['value'] = 'counterpart'
                                            #a['type'] = 'dictinterpretation'
                                            #a['string'] = head_base
                                            a_s = create_annotation(strpos[0] + start, strpos[0] + end, "counterpart", "dictinterpretation", head_base)
                                            annotation[language].extend(a_s)
                                            head = match_bracket.group(1) + head_base

                                        #a = {}
                                        #a['start'] = strpos[0] + start
                                        #a['end'] = strpos[0] + end
                                        #a['value'] = 'counterpart'
                                        #a['type'] = 'dictinterpretation'
                                        #a['string'] = head
                                        a_s = create_annotation(start, end, "counterpart", "dictinterpretation", head)
                                        annotation[language].extend(a_s)
                                    start = match.end(0)
                    else:
                        print "no match: %s" % l.encode("utf-8")
                                

    Session.commit()
    Session.close()
    wordlistfile.close()   

if __name__ == "__main__":
    main(sys.argv)