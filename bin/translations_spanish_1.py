# -*- coding: utf8 -*-

import sys, codecs, collections, re
from operator import itemgetter

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
        
    spanish_singleword_dict = {}
    languages_iso = []
    spanish_len2_dict = collections.defaultdict(int)
    spanish_len3_dict = collections.defaultdict(int)
    spanish_lengreater3_dict = collections.defaultdict(int)
    
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
                translation = re_article.sub("", translation)
                len_translation = len(translation.split(' '))
                
                if len_translation == 1:
                    #print translation.encode("utf-8")
                    if not spanish_singleword_dict.has_key(translation):
                        spanish_singleword_dict[translation] = collections.defaultdict(set)
                    for head in heads_with_translations[entry_id]['heads']:
                        spanish_singleword_dict[translation][language_iso].add(head)
                        
                elif len_translation == 2:
                    #output2.write("%s\n" % (translation))
                    spanish_len2_dict[translation] += 1

                elif len_translation == 3:
                    #output3.write("%s\n" % (translation))
                    spanish_len3_dict[translation] += 1

                else:
                    #output4.write("%s\n" % (translation))
                    spanish_lengreater3_dict[translation] += 1

    output2 = codecs.open("spanish_len2.txt", "w", "utf-8")
    for w in sorted(spanish_len2_dict.iteritems(), key=itemgetter(1), reverse=True):
        output2.write(u"{0}\t{1}\n".format(w[0], w[1]))

    output3 = codecs.open("spanish_len3.txt", "w", "utf-8")
    for w in sorted(spanish_len3_dict.iteritems(), key=itemgetter(1), reverse=True):
        output3.write(u"{0}\t{1}\n".format(w[0], w[1]))

    output4 = codecs.open("spanish_len_greater3.txt", "w", "utf-8")
    for w in sorted(spanish_lengreater3_dict.iteritems(), key=itemgetter(1), reverse=True):
        output4.write(u"{0}\t{1}\n".format(w[0], w[1]))

    output = codecs.open("spanish_singlewords_matrix.txt", "w", "utf-8")
    output.write(u"%s\t%s\n" % ('es', '\t'.join(languages_iso)))
    for sp in spanish_singleword_dict:
        output.write(sp)
        #print spanish_singleword_dict[sp].keys()
        for lang in languages_iso:
            output.write(u"\t%s" % ('|'.join(spanish_singleword_dict[sp][lang])))
        output.write("\n")
        

if __name__ == "__main__":
    main(sys.argv)
