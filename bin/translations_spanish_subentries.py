# -*- coding: utf8 -*-

import sys, codecs, collections
from operator import itemgetter

from qlc.CorpusReader import CorpusReaderDict


def main(argv):

    if len(argv) < 3:
        print "call: translations_spanish_1.py data_path bibtex_key"
        sys.exit(1)

    cr = CorpusReaderDict(argv[1])

    dictdata_ids = []    
    dictdata_ids = cr.dictdata_ids_for_bibtex_key(argv[2])
    if len(dictdata_ids) == 0:
        print "did not find any dictionary data for the bibtex_key."
        sys.exit(1)

    
    for dictdata_id in dictdata_ids:
        translations = collections.defaultdict(int)
        heads_with_translations = cr.heads_with_translations_for_dictdata_id(dictdata_id)
        dictdata_string = cr.dictdata_string_id_for_dictata_id(dictdata_id)
        output = codecs.open("translations_subentries_for_%s.txt" % dictdata_string, "w", "utf-8")
        
        for entry_id in heads_with_translations:
            if heads_with_translations[entry_id]['is_subentry'] == 't':
                for t in heads_with_translations[entry_id]['translations']:
                    translations[t] += 1

        for w in sorted(translations.iteritems(), key=itemgetter(1), reverse=True):
            output.write(u"{0}\t{1}\n".format(w[0], w[1]))
    
if __name__ == "__main__":
    main(sys.argv)
