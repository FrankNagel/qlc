# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys, os, glob
import codecs

from zipfile import ZipFile
from qlc.CorpusReader import CorpusReaderDict

def main(argv):

    if len(argv) < 2:
        print "call: exportheads_with_translations.py data_path"
        exit(1)

    cr = CorpusReaderDict(argv[1])
        
    for dictdata_id in cr.dictdataStringIds():
        heads_with_translations = cr.headsWithTranslationsForDictdataId(dictdata_id)
        dictdata_string = cr.dictdataStringIdForDictataId(dictdata_id)
        output = codecs.open("heads_with_translations_%s.txt" % dictdata_string, "w", "utf-8")
        
        for entry_id in heads_with_translations:
            for head in heads_with_translations[entry_id]['heads']:
                for translation in heads_with_translations[entry_id]['translations']:
                    output.write("%s\t%s\n" % (head, translation))
        
        output.close()

if __name__ == "__main__":
    main(sys.argv)
