# -*- coding: utf8 -*-

import sys, codecs, collections, unicodedata
import regex as re
from operator import itemgetter

from qlc.CorpusReader import CorpusReaderDict
from pygraph.classes.graph import graph
from pygraph.readwrite.markup import write

# snowball stemmer: http://snowball.tartarus.org/download.php
import Stemmer

def spanish_stopwords():
    stopwords = codecs.open("data/stopwords/spa.txt", "r", "utf-8")
    ret = set()
    for line in stopwords:
        word = line.rstrip("\n")
        word = re.sub(" *\|.*$", "", word)
        if re.search("[^\s]", word):
            word = unicodedata.normalize("NFD", word)
            ret.add(word)
    return ret


def main(argv):
    
    if len(argv) < 3:
        print("call: translations_spanish_2.py data_path graph_file_out.txt [component]")
        sys.exit(1)

    cr = CorpusReaderDict(argv[1])

    dictdata_ids = []    
    if len(argv) == 4:
        print("Loading component {0}".format(argv[3]))
        dictdata_ids = cr.dictdata_ids_for_component(argv[3])
        if len(dictdata_ids) == 0:
            print("did not find any dictionary data for the component.")
            sys.exit(1)
    else:
        dictdata_ids = cr.dictdata_string_ids
        
    gr = graph()
    
    stemmer = Stemmer.Stemmer('spanish')
    stopwords = spanish_stopwords()
    re_stopwords = re.compile("\b" + u"(?:{0})".format("|".join(stopwords)) +  r"\b")

    for dictdata_id in dictdata_ids:
        src_language_iso = cr.src_language_iso_for_dictdata_id(dictdata_id)
        tgt_language_iso = cr.tgt_language_iso_for_dictdata_id(dictdata_id)
        if src_language_iso != 'spa' and tgt_language_iso != 'spa':
            continue
        
        language_iso = None
        if tgt_language_iso == 'spa':
            language_iso = src_language_iso
        else:
            language_iso = tgt_language_iso
                        
        heads_with_translations = cr.heads_with_translations_for_dictdata_id(dictdata_id)
        dictdata_string = cr.dictdata_string_id_for_dictata_id(dictdata_id)
        bibtex_key = dictdata_string.split("_")[0]

        for entry_id in heads_with_translations:
            if tgt_language_iso == 'spa':
                heads = heads_with_translations[entry_id]['heads']
                translations = heads_with_translations[entry_id]['translations']
            else:
                heads = heads_with_translations[entry_id]['translations']
                translations = heads_with_translations[entry_id]['heads']
                
            for translation in translations:
                for head in heads_with_translations[entry_id]['heads']:
                    head_with_source = u"{0}|{1}".format(head, bibtex_key)
                    #translation_with_language = "{0}|{1}".format(translation, language_iso)
                    
                    if not gr.has_node(head_with_source):
                        gr.add_node(head_with_source, [('lang', language_iso)])
                    
                    if not gr.has_node(translation):
                        gr.add_node(translation, [('lang', 'spa')])
                        
                    if not gr.has_edge((head_with_source, translation)):
                        gr.add_edge((head_with_source, translation))

    output = codecs.open(sys.argv[2], "w", "utf-8")
    output.write(write(gr))
    output.close()

if __name__ == "__main__":
    main(sys.argv)
