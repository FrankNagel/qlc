# -*- coding: utf8 -*-

import sys, codecs, collections, unicodedata
import regex as re
from operator import itemgetter

from qlc.CorpusReader import CorpusReaderDict

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

    if len(argv) < 2:
        print("call: translations_spanish_1.py data_path [component]")
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
        
    spanish_singleword_dict = {}
    languages_iso = []
    spanish_len2_dict = collections.defaultdict(int)
    spanish_len3_dict = collections.defaultdict(int)
    spanish_lengreater3_dict = collections.defaultdict(int)
    
    stemmer = Stemmer.Stemmer('spanish')
    stopwords = spanish_stopwords()
    re_stopwords = re.compile(r"\b(?:{0})\b".format("|".join(stopwords)))

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
                if len_translation > 1:
                    translation_without_stopwords = re_stopwords.sub("", translation)
                    translation_without_stopwords = translation_without_stopwords.strip(" ")
                    translation_without_stopwords = re.sub(" +", " ", translation_without_stopwords)
                    len_translation_without_stopwords = len(translation_without_stopwords.split(' '))
                else:
                    translation_without_stopwords = translation
                    len_translation_without_stopwords = len_translation
                
                if "(incl.)" in translation:
                    print(translation)
                    print(translation_without_stopwords)

                if len_translation_without_stopwords == 1:
                    #print translation.encode("utf-8")
                    translation_stem = stemmer.stemWord(translation_without_stopwords)
                    if not translation_stem in  spanish_singleword_dict:
                        spanish_singleword_dict[translation_stem] = collections.defaultdict(set)
                    for head in heads_with_translations[entry_id]['heads']:
                        spanish_singleword_dict[translation_stem][language_iso].add(head)
                        

                elif len_translation == 2:
                    #output2.write("%s\n" % (translation))
                    spanish_len2_dict[translation] += 1

                elif len_translation == 3:
                    #output3.write("%s\n" % (translation))
                    spanish_len3_dict[translation] += 1

                else:
                    #output4.write("%s\n" % (translation))
                    spanish_lengreater3_dict[translation] += 1

    #output1 = codecs.open("spanish_len1.txt", "w", "utf-8")
    #for w in sorted(spanish_singleword_dict.iteritems(), key=itemgetter(0), reverse=True):
    #    output1.write(u"{0}\n".format(w[0]))

    output2 = codecs.open("spanish_len2.txt", "w", "utf-8")
    for w in sorted(spanish_len2_dict.items(), key=itemgetter(1), reverse=True):
        output2.write("{0}\t{1}\n".format(w[0], w[1]))

    output3 = codecs.open("spanish_len3.txt", "w", "utf-8")
    for w in sorted(spanish_len3_dict.items(), key=itemgetter(1), reverse=True):
        output3.write("{0}\t{1}\n".format(w[0], w[1]))

    output4 = codecs.open("spanish_len_greater3.txt", "w", "utf-8")
    for w in sorted(spanish_lengreater3_dict.items(), key=itemgetter(1), reverse=True):
        output4.write("{0}\t{1}\n".format(w[0], w[1]))

    output = codecs.open("spanish_singlewords_matrix.txt", "w", "utf-8")
    output1 = codecs.open("spanish_len1.txt", "w", "utf-8")
    total_count = 0
    more_than_one_lang_count = 0
    output.write("%s\t%s\n" % ('es', '\t'.join(languages_iso)))
    for sp in spanish_singleword_dict:
        output.write(sp)
        #print spanish_singleword_dict[sp].keys()
        count_languages = 0
        for lang in languages_iso:
            if len(spanish_singleword_dict[sp][lang]) > 0:
                count_languages += 1
            output.write("\t%s" % ('|'.join(spanish_singleword_dict[sp][lang])))
        output.write("\n")
        output1.write("{0}\n".format(sp))
        if count_languages > 1:
            more_than_one_lang_count += 1
        total_count += 1
        
    print("total number of entries in single word matrix: {0}".format(total_count))
    print("number of entries with more than one language: {0}".format(more_than_one_lang_count))

if __name__ == "__main__":
    if py3k == sys.version_info < (3, 0):
        print("This script requires at least Python 3.0")
        sys.exit(1)

    main(sys.argv)
