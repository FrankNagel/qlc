# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter

# Pylons model init sequence
import pylons.test
import logging

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.books

from paste.deploy import appconfig

import functions

glossary = {
    u"ayahuasca": u"especie de bejuco del que se extrae una droga alucinógena amarga y narcótica que produce un prolongado sueño",
    u"bagre": u"especie de pez",
    u"batea": u"recipiente o tabla de poco fondo donde se machuca la yuca",
    u"capirona": u"especie de árbol leñoso, muy duro",
    u"carachama": u"especie de pez",
    u"carachamita": u"especie de pez",
    u"curuhuinse": u"especie de hormiga",
    u"chambira": u"especie de palmera cuyo coco es comestible; fibras de esta palmera",
    u"chonta": u"cogollo de la palmera del mismo nombre",
    u"huacrapona": u"especie de palmera usada para hacer cerbatanas",
    u"huanchaco": u"especie de pájaro pequeño de plumaje rojo y negro",
    u"huayusa": u"líquido parecido al té usado para el lavado estomacal",
    u"huitina": u"especie de planta de tubérculo comestible",
    u"masato": u"bebida fermentada generalmente hecha de yuca o plátano",
    u"mitayero": u"cazador",
    u"mitayo": u"caza, animales de caza",
    u"patarashca": u"carne o pescado asado envuelto en hojas",
    u"pijuayo": u"palmera alta cuyo tallo es espinoso y cuyo fruto comestible es grande y de color amarillo. Su cogollo es comestible.",
    u"sachapapa": u"tubérculo comestible de la selva",
    u"súngaro": u"especie de pez",
    u"suri": u"especie de gusano comestible",
    u"shungo": u"especie de árbol de madera dura cuyo tronco es usado para hacer horcones",
    u"tamshi": u"especie de bejuco cuya fibra sirve para hacer canastas, casas, muebles, etc.",
    u"toé": u"sustancia con propiedades estupefacientes",
    u"ungurahui": u"especie de palmera"
}

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    for match_crossref in re.finditer(u'\((?:vea|Sinón\.) (.*?)\)', entry.fullentry):
        start = match_crossref.start(1)
        substr = entry.fullentry[match_crossref.start(1):match_crossref.end(1)]
        for match in re.finditer(r', ?', substr):
            end = match.start(0) + match_crossref.start(1)
            entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
            start = match.end(0) + match_crossref.start(1)
        end = match_crossref.end(1)
        entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
        #entry.append_annotation(match.start(1), match.end(1), u'crossreference', u'dictinterpretation')

def insert_head_from_glossary(entry, start, end, s = None):
    s2 = s
    if not s2:
        s2 = entry.fullentry[start:end]
    heads = []
    if ("*" not in s2):
        h = functions.insert_head(entry, start, end, s)
        heads.append(h)
    elif (" " in s2):
        head_base = re.sub("\*", "", s2)
        h = functions.insert_head(entry, start, end, head_base)
        heads.append(h)
    else:
        head_base = re.sub("\*", "", s2)
        if head_base in glossary:
            h = functions.insert_head(entry, start, end, glossary[head_base])
            heads.append(h)
        h = functions.insert_head(entry, start, end, head_base)
        heads.append(h)
    return heads

def insert_head(entry, start, end):
    substr = entry.fullentry[start:end]
    match_spaces = re.search("^ +", substr)
    if match_spaces:
        start = start + len(match_spaces.group(0))

    match_spaces = re.search(":? *$", substr)
    if match_spaces:
        end = end - len(match_spaces.group(0))

    substr = entry.fullentry[start:end]

    match = re.search(r"(?! )(\()(.*?)\)$", substr)
    if match:
        heads = []
        head_base = entry.fullentry[start:start+match.start(1)]
        h = insert_head_from_glossary(entry, start, start + match.start(1), head_base)
        heads.extend(h)
        h = insert_head_from_glossary(entry, start, end, head_base + match.group(2))
        heads.extend(h)
        return heads
    else:
        h = insert_head_from_glossary(entry, start, end)
        return h

def insert_translation_from_glossary(entry, start, end, s = None):
    s2 = s
    if not s2:
        s2 = entry.fullentry[start:end]
    heads = []
    s2 = re.sub("\.\.\.!", "", s2)
    s2 = re.sub(u"[¡!]", "", s2)
    if ("*" not in s2):
        h = functions.insert_translation(entry, start, end, s2)
        heads.append(h)
    elif (" " in s2):
        head_base = re.sub("\*", "", s2)
        h = functions.insert_translation(entry, start, end, head_base)
        heads.append(h)
    else:
        head_base = re.sub("\*", "", s2)
        if head_base in glossary:
            h = functions.insert_translation(entry, start, end, glossary[head_base])
            heads.append(h)
        h = functions.insert_translation(entry, start, end, head_base)
        heads.append(h)
    return heads

def insert_translation(entry, start, end):
    substr = entry.fullentry[start:end]
    match_spaces = re.search("^ +", substr)
    if match_spaces:
        start = start + len(match_spaces.group(0))

    match_spaces = re.search("\.? *$", substr)
    if match_spaces:
        end = end - len(match_spaces.group(0))

    substr = entry.fullentry[start:end]

    match = re.search(r"(?! )(\()([^)]{1,3})\)$", substr)
    if match:
        translation_base = entry.fullentry[start:start+match.start(1)]
        h = insert_translation_from_glossary(entry, start, start + match.start(1), translation_base)
        h = insert_translation_from_glossary(entry, start, end, translation_base + match.group(2))
    else:
        h = insert_translation_from_glossary(entry, start, end)

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []
    
    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_start_pos = 0

    heads = []

    if head_end_pos > -1:
        start = head_start_pos
        substr = entry.fullentry[head_start_pos:head_end_pos]
        for match in re.finditer(r'(?:, ?|$)', substr):
            end = match.start(0) + head_start_pos
            inserted_heads = insert_head(entry, start, end)
            #entry.append_annotation(start, end, u'head', u'dictinterpretation')
            heads.extend(inserted_heads)
            start = match.end(0) + head_start_pos
    else:
        if entry.fullentry[0] == u"║" and entry.is_subentry():
            head_annotations_mainentry = [ a for a in entry.mainentry().annotations if a.value=='head']
            for a in head_annotations_mainentry:
                entry.append_annotation(0, 1, "head", "dictinterpretation", a.string)
        else:
            functions.print_error_in_entry(entry, "No head found.")
            #print "no head"
            #print entry.fullentry.encode('utf-8')
        
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
    
    start = italic_annotation.start
    end = italic_annotation.end
    entry.append_annotation(start, end, u'pos', u'dictinterpretation')

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    if len(pos_annotations) > 0:
        head_end_pos = pos_annotations[0].end
    else:
        head_end_pos = functions.get_last_bold_pos_at_start(entry)
        
    if head_end_pos > -1:
        substr = entry.fullentry[head_end_pos:]
        if re.match(u" ?\(vea ", substr):
            return
        start = head_end_pos
        for match in re.finditer(r'(?:, ?|; ?|\d\. |$)', substr):
            # Are we in exclamation or question marks?
            mybreak = False
            for match_mark in re.finditer(u'[¡][^!]*[!]', substr):
                if match.start() > match_mark.start() and match.start() < match_mark.end():
                    mybreak = True
                    
            if mybreak:
                continue
            
            end = match.start(0) + head_end_pos
            
            pattern = re.compile(u' ?\(Sinón ')
            match_link = pattern.search(entry.fullentry[start:end])
            if match_link:
                end = match_link.start(0)
            
            match_pos = re.search(u"║ ?([^.]+\.) ?", entry.fullentry[start:end])
            if match_pos:
                insert_translation(entry, start, start + match_pos.start(0))
                insert_translation(entry, start + match_pos.end(0), end)
                entry.append_annotation(start + match_pos.start(1), start + match_pos.end(1), u'pos', u'dictinterpretation')
            else:
                if not(re.match(r"\s*$", entry.fullentry[start:end])):
                    insert_translation(entry, start, end)
            start = match.end(0) + head_end_pos

def main(argv):
    bibtex_key = u"wipiodeicat1996"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=271,pos_on_page=53).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
            annotate_crossrefs(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)