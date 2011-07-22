# -*- coding: utf8 -*-

import sys, codecs, collections, re
from operator import itemgetter

from qlc.CorpusReader import CorpusReaderDict
from pygraph.classes.graph import graph
from pygraph.readwrite.markup import write

def main(argv):

    if len(argv) < 2:
        print("call: translations_spanish_2.py data_path [component]")
        sys.exit(1)

    cr = CorpusReaderDict(argv[1])

    dictdata_ids = []    
    if len(argv) == 3:
        dictdata_ids = cr.dictdata_ids_for_component(argv[2])
        if len(dictdata_ids) == 0:
            print("did not find any dictionary data for the bibtex_key.")
            sys.exit(1)
    else:
        dictdata_ids = cr.dictdata_string_ids
        
    gr = graph()
    
    re_article = re.compile("^(?:el|la|al|un|uno|y|no|una|lo|le|ser|estar|los|tener|hacer|o|de) ")

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

        for entry_id in heads_with_translations:
            if tgt_language_iso == 'spa':
                heads = heads_with_translations[entry_id]['heads']
                translations = heads_with_translations[entry_id]['translations']
            else:
                heads = heads_with_translations[entry_id]['translations']
                translations = heads_with_translations[entry_id]['heads']
                
            for translation in translations:
                for head in heads_with_translations[entry_id]['heads']:
                    head_with_language = "{0}|{1}".format(head, 'spa')
                    translation_with_language = "{0}|{1}".format(translation, language_iso)
                    
                    if not gr.has_node(head_with_language):
                        gr.add_node(head_with_language)
                    
                    if not gr.has_node(translation_with_language):
                        gr.add_node(translation_with_language, [('source', dictdata_string)])
                    else:
                        gr.add_node_attribute(translation_with_language, [('source', dictdata_string)])
                        
                    if not gr.has_edge((head_with_language, translation_with_language)):
                        gr.add_edge((head_with_language, translation_with_language))

    output = codecs.open("translation_graph.txt", "w", "utf-8")
    output.write(write(gr))
    output.close()

if __name__ == "__main__":
    main(sys.argv)
