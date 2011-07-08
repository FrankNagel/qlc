# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys, os, glob
import codecs

from zipfile import ZipFile
from qlc.CorpusReader import CorpusReaderWordlist

families = {
    u'embera Darién': 'CHOCO',
    u'catío': 'CHOCO',
    u'embera chamí': 'CHOCO',
    u'embera Tadó': 'CHOCO',
    u'epena Saija': 'CHOCO',
    u'epena basurudó': 'CHOCO',
    u'wounaan': 'CHOCO',
    u'tucano': 'TUCANO',
    u'wanano': 'TUCANO',
    u'piratapuyo': 'TUCANO',
    u'waimaja': 'TUCANO',
    u'bará': 'TUCANO',
    u'tuyuca': 'TUCANO',
    u'yurutí': 'TUCANO',
    u'desano': 'TUCANO',
    u'siriano': 'TUCANO',
    u'tatuyo': 'TUCANO',
    u'carapana': 'TUCANO',
    u'macuna': 'TUCANO',
    u'barasana': 'TUCANO',
    u'tanimuca': 'TUCANO',
    u'cubeo': 'TUCANO',
    u'koreguaje': 'TUCANO',
    u'secoya': 'TUCANO',
    u'siona': 'TUCANO',
    u'orejón': 'TUCANO',
    u'wayuu': 'ARAWAK',
    u'achagua': 'ARAWAK',
    u'curripaco': 'ARAWAK',
    u'piapoco': 'ARAWAK',
    u'yucuna': 'ARAWAK',
    u'tariano': 'ARAWAK',
    u'giacone': 'ARAWAK',
    u'cabiyarí': 'ARAWAK',
    u'baniva': 'ARAWAK',
    u'resígaro': 'ARAWAK',        
    u'playero': 'GUAHIBO',
    u'guahibo': 'GUAHIBO',
    u'cuiba': 'GUAHIBO',
    u'jitnu': 'GUAHIBO',
    u'guayabero': 'GUAHIBO', 
    u'witoto murui': 'WITOTO',
    u'witoto mɨnɨca': 'WITOTO',
    u'witoto nɨpode': 'WITOTO',
    u'ocaina': 'WITOTO',
    u'muinane': 'WITOTO',
    u'bora': 'WITOTO',
    u'miraña': 'WITOTO',
    u'ika': 'CHIBCHA',
    u'kogui': 'CHIBCHA',
    u'chimila': 'CHIBCHA',
    u'tunebo': 'CHIBCHA',
    u'tunebo central': 'CHIBCHA',
    u'barí': 'CHIBCHA',
    u'dí̵mɨna': 'CHIBCHA',
    u'jupda': u'MACÚ-PUINAVE',
    u'kakua': u'MACÚ-PUINAVE',
    u'puinave': u'MACÚ-PUINAVE',
    u'nukak': u'MACÚ-PUINAVE',
    u'kamsá': u'KAMSÁ',
    u'carijona': 'CARIB',
    u'yukpa': 'CARIB',
    u'cha\'palaachi': 'BARBACOA',
    u'páez': 'BARBACOA',
    u'guambiano': 'BARBACOA',
    u'totoró': 'BARBACOA',
    u'tsafiqui pila': 'BARBACOA',
    u'awa': 'BARBACOA',
    u'sáliba': u'SÁLIBA-PIAROA',
    u'inga': 'QUECHUA',
    u'English': 'GERMANIC',
    u'Español': 'ROMANIC',
    u'giacone': 'ARAWAK'
}

def main(argv):

    if len(argv) < 2:
        print "call: counterparts_huber1992.py data_path"
        exit(1)

    cr = CorpusReaderWordlist(argv[1])
        
    output = codecs.open("counterparts_huber1992.txt", "w", "utf-8")
    output.write("COUNTERPART\tCONCEPT\tLANGUAGE_BOOKNAME\tLANGUAGE_CODE\tFAMILY\tBIBTEX_KEY\n")
    
    for wordlistdata_id in cr.wordlist_ids_for_bibtex_key('huber1992'):
        #counterparts = cr.counterpartsForWordlistdataId(wordlistdata_id)
        #print wordlistdata_id
        language_bookname = cr.get_language_bookname_for_wordlist_data_id(wordlistdata_id)
        family = families[language_bookname]
        
        for cp in cr.counterparts_for_wordlistdata_id(wordlistdata_id):
            for cp_string in cp['counterpart']:
                output.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (cp_string, cp['concept'], cp['language_bookname'], cp['language_code'], family, cp['bibtex_key']))
        
    output.close()

if __name__ == "__main__":
    main(sys.argv)
