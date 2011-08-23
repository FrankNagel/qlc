# -*- coding: utf8 -*-
#!/usr/bin/env python3

"""
This script outputs a dot files for each dictionary. The dot file each
contain a graph, where each spanish translation is connected to each
head word of the dictionary's native language. The spanish translation are
not processed. The head words' strings are each connected to a string with
the source ID. This later helps to distinguish head words from different sources
that are represented by the same string.
"""

import sys, codecs, collections, unicodedata, re

from qlc.CorpusReader import CorpusReaderDict
from pygraph.classes.graph import graph
from qlc.TranslationGraph import write

re_quotes = re.compile('"')

def escape_string(s):
    ret = re_quotes.sub('', s)
    #if not ret.startswith('"') or not ret.endswith('"'):
    #    ret = '"{0}"'.format(ret)
    return ret

def main(argv):
    
    if len(argv) < 3:
        print("call: translations_spanish_graph.py data_path (bibtex_key|component)")
        sys.exit(1)

    cr = CorpusReaderDict(argv[1])

    dictdata_ids = cr.dictdata_ids_for_bibtex_key(argv[2])
    if len(dictdata_ids) == 0:
        dictdata_ids = cr.dictdata_ids_for_component(argv[2])
        if len(dictdata_ids) == 0:
            print("did not find any dictionary data for the bibtex_key or component {0}.".format(argv[2]))
            sys.exit(1)
        

    for dictdata_id in dictdata_ids:
        gr = graph()
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
                for head in heads:
                    head_with_source = escape_string("{0}|{1}".format(head, bibtex_key))
                    translation = escape_string(translation)
                    
                    #translation_with_language = "{0}|{1}".format(translation, language_iso)
                    
                    if not gr.has_node(head_with_source):
                        gr.add_node(head_with_source, [('lang', language_iso), ('source', dictdata_string)])
                    
                    if not gr.has_node(translation):
                        gr.add_node(translation, [('lang', 'spa')])
                        
                    if not gr.has_edge((head_with_source, translation)):
                        gr.add_edge((head_with_source, translation))

        output = codecs.open("{0}.dot".format(dictdata_string), "w", "utf-8")
        output.write(write(gr))
        output.close()

if __name__ == "__main__":
    main(sys.argv)
