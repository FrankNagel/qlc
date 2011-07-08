# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys, os, glob
import codecs

from zipfile import ZipFile
from qlc.CorpusReader import CorpusReaderDict

def main(argv):

    if len(argv) < 2:
        print "call: exportheads_with_translations.py data_path [bibtex_key]"
        exit(1)

    cr = CorpusReaderDict(argv[1])
    
    dictdata_ids = []    
    if len(argv) == 3:
        dictdata_ids = cr.dictdata_ids_for_bibtex_key(argv[2])
        if len(dictdata_ids) == 0:
            print "did not find any dictionary data for the bibtex_key."
            sys.exit(1)
    else:
        dictdata_ids = cr.dictdata_string_ids
        
    
    for dictdata_id in dictdata_ids:
        heads_with_translations = cr.heads_with_translations_for_dictdata_id(dictdata_id)
        dictdata_string = cr.dictdata_string_id_for_dictata_id(dictdata_id)
        output = codecs.open("heads_with_translations_%s.txt" % dictdata_string, "w", "utf-8")
        
        for entry_id in heads_with_translations:
            for head in heads_with_translations[entry_id]['heads']:
                for translation in heads_with_translations[entry_id]['translations']:
                    output.write("%s\t%s\n" % (head, translation))
        
        output.close()

if __name__ == "__main__":
    main(sys.argv)
