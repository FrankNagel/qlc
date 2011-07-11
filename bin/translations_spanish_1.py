# -*- coding: utf8 -*-

import sys, codecs, collections
from qlc.CorpusReader import CorpusReaderDict


def main(argv):

    if len(argv) < 2:
        print "call: translations_spanish_1.py data_path [component]"
        exit(1)

    cr = CorpusReaderDict(argv[1])

    dictdata_ids = []    
    if len(argv) == 3:
        dictdata_ids = cr.dictdata_ids_for_component(argv[2])
        if len(dictdata_ids) == 0:
            print "did not find any dictionary data for the bibtex_key."
            sys.exit(1)
    else:
        dictdata_ids = cr.dictdata_string_ids
        
    output2 = codecs.open("spanish_len2.txt", "w", "utf-8")
    output3 = codecs.open("spanish_len3.txt", "w", "utf-8")

    spanish_singleword_dict = {}
    languages_iso = []

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
            
        if language_iso not in languages_iso:
            languages_iso.append(language_iso)
            
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
                len_translation = len(translation.split(' '))
                
                if len_translation == 1:
                    #print translation.encode("utf-8")
                    if not spanish_singleword_dict.has_key(translation):
                        spanish_singleword_dict[translation] = collections.defaultdict(list)
                    for head in heads_with_translations[entry_id]['heads']:
                        spanish_singleword_dict[translation][language_iso].append(head)
                        
                elif len_translation == 2:
                    output2.write("%s\n" % (translation))

                elif len_translation == 3:
                    output3.write("%s\n" % (translation))

    output = codecs.open("spanish_singlewords_matrix.txt", "w", "utf-8")
    output.write("%s\t%s\n" % ('es', '\t'.join(languages_iso)))
    for sp in spanish_singleword_dict:
        output.write(sp)
        #print spanish_singleword_dict[sp].keys()
        for lang in languages_iso:
            output.write("\t%s" % ('|'.join(spanish_singleword_dict[sp][lang])))
        output.write("\n")
        

if __name__ == "__main__":
    main(sys.argv)
