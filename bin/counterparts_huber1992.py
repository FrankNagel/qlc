# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys, os, glob
import codecs

from zipfile import ZipFile
from qlc.CorpusReader import CorpusReaderWordlist

families = {
    'embera Darién': 'CHOCO',
    'catío': 'CHOCO',
    'embera chamí': 'CHOCO',
    'embera Tadó': 'CHOCO',
    'epena Saija': 'CHOCO',
    'epena basurudó': 'CHOCO',
    'wounaan': 'CHOCO',
    'tucano': 'TUCANO',
    'wanano': 'TUCANO',
    'piratapuyo': 'TUCANO',
    'waimaja': 'TUCANO',
    'bará': 'TUCANO',
    'tuyuca': 'TUCANO',
    'yurutí': 'TUCANO',
    'desano': 'TUCANO',
    'siriano': 'TUCANO',
    'tatuyo': 'TUCANO',
    'carapana': 'TUCANO',
    'macuna': 'TUCANO',
    'barasana': 'TUCANO',
    'tanimuca': 'TUCANO',
    'cubeo': 'TUCANO',
    'koreguaje': 'TUCANO',
    'secoya': 'TUCANO',
    'siona': 'TUCANO',
    'orejón': 'TUCANO',
    'wayuu': 'ARAWAK',
    'achagua': 'ARAWAK',
    'curripaco': 'ARAWAK',
    'piapoco': 'ARAWAK',
    'yucuna': 'ARAWAK',
    'tariano': 'ARAWAK',
    'giacone': 'ARAWAK',
    'cabiyarí': 'ARAWAK',
    'baniva': 'ARAWAK',
    'resígaro': 'ARAWAK',        
    'playero': 'GUAHIBO',
    'guahibo': 'GUAHIBO',
    'cuiba': 'GUAHIBO',
    'jitnu': 'GUAHIBO',
    'guayabero': 'GUAHIBO', 
    'witoto murui': 'WITOTO',
    'witoto mɨnɨca': 'WITOTO',
    'witoto nɨpode': 'WITOTO',
    'ocaina': 'WITOTO',
    'muinane': 'WITOTO',
    'bora': 'WITOTO',
    'miraña': 'WITOTO',
    'ika': 'CHIBCHA',
    'kogui': 'CHIBCHA',
    'chimila': 'CHIBCHA',
    'tunebo': 'CHIBCHA',
    'tunebo central': 'CHIBCHA',
    'barí': 'CHIBCHA',
    'dí̵mɨna': 'CHIBCHA',
    'jupda': 'MACÚ-PUINAVE',
    'kakua': 'MACÚ-PUINAVE',
    'puinave': 'MACÚ-PUINAVE',
    'nukak': 'MACÚ-PUINAVE',
    'kamsá': 'KAMSÁ',
    'carijona': 'CARIB',
    'yukpa': 'CARIB',
    'cha\'palaachi': 'BARBACOA',
    'páez': 'BARBACOA',
    'guambiano': 'BARBACOA',
    'totoró': 'BARBACOA',
    'tsafiqui pila': 'BARBACOA',
    'awa': 'BARBACOA',
    'sáliba': 'SÁLIBA-PIAROA',
    'inga': 'QUECHUA',
    'English': 'GERMANIC',
    'Español': 'ROMANIC',
    'giacone': 'ARAWAK'
}

def main(argv):

    if len(argv) < 2:
        print("call: counterparts_huber1992.py data_path")
        exit(1)

    cr = CorpusReaderWordlist(argv[1])
        
    output = codecs.open("counterparts_huber1992.txt", "w", "utf-8")
    output.write("COUNTERPART\tCONCEPT\tLANGUAGE_BOOKNAME\tLANGUAGE_CODE\tFAMILY\tBIBTEX_KEY\n")
    
    for wordlistdata_id in cr.wordlist_ids_for_bibtex_key('huber1992'):
        #counterparts = cr.counterpartsForWordlistdataId(wordlistdata_id)
        #print wordlistdata_id
        language_bookname = cr.get_language_bookname_for_wordlist_data_id(wordlistdata_id)
        language_code = cr.get_language_code_for_wordlist_data_id(wordlistdata_id)
        family = families[language_bookname]
        
        for concept, counterpart in cr.concepts_with_counterparts_for_wordlistdata_id(wordlistdata_id):
            output.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (counterpart, concept, language_bookname, language_code, family, 'huber1992'))
        
    output.close()

if __name__ == "__main__":
    main(sys.argv)
