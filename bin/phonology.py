# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys, os, glob
import codecs

from zipfile import ZipFile
from qlc.CorpusReader import CorpusReaderDict

def main(argv):

    if len(argv) < 2:
        print "call: phonology.py data_path [bibtex_key]"
        exit(1)

    cr = CorpusReaderDict(argv[1])
    
    bibtex_key = None
    dictdata_ids = []
    if len(argv) > 2:
        bibtex_key = argv[2]
        dictdata_ids = cr.dictdataIdsForBibtexKey(bibtex_key)
    else:
        dictdata_ids = cr.dictdataStringIds()
        
    for dictdata_id in dictdata_ids:
        phonology = cr.phonologyForDictdataId(dictdata_id)
        dictdata_string = cr.dictdataStringIdForDictataId(dictdata_id)
        bibtex_key = dictdata_string.split("_")[0]
        output = codecs.open("phonology_%s.txt" % dictdata_string, "w", "utf-8")
        
        for entry_id in phonology:
            for p in phonology[entry_id]["phonology"]:
                output.write("%s\thttp://cidles.eu/quanthistling/source/%s/%s/%s/index.html\n" % (p, bibtex_key, phonology[entry_id]["startpage"], phonology[entry_id]["pos_on_page"]))
        
        output.close()

if __name__ == "__main__":
    main(sys.argv)
