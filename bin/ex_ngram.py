# encoding: utf-8
#!/usr/bin/env python3

"""
Documentation.

Authors:

* The Team
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011
#  The Quantitative Language Comparison (scikits.qlc) Team
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import sys, os, itertools, collections

from qlc.CorpusReader import CorpusReaderWordlist
from qlc.OrthographyProfile import OrthographyProfile

import qlc.Ngram
import numpy

def main(argv):

    if len(argv) < 2:
        print("call: counterparts_huber1992.py data_path")
        exit(1)

    cr = CorpusReaderWordlist(argv[1])
    o = OrthographyProfile(os.path.join(argv[1], "orthography_profiles", "huber1992.txt"))
    
    ngrams_by_language_count = list()
    ngrams_set = set()
    
    for i, wordlistdata_id in enumerate(cr.wordlist_ids_for_bibtex_key('huber1992')):
        #counterparts = cr.counterpartsForWordlistdataId(wordlistdata_id)
        #print wordlistdata_id
        language_bookname = cr.get_language_bookname_for_wordlist_data_id(wordlistdata_id)
        language_code = cr.get_language_code_for_wordlist_data_id(wordlistdata_id)
                
        counterpart_graphemes = (o.parse_string_to_graphemes(counterpart) \
            for counterpart in cr.counterparts_for_wordlistdata_id(wordlistdata_id))

        (rows, columns, matrix) = qlc.Ngram.words_ngrams_matrix_for_graphemes_list(counterpart_graphemes, 2)
        
        sum = numpy.sum(matrix, 0)
        #print("Sum length: {0}".format(len(sum)))
        #print("Column length: {0}".format(len(columns)))
        
        if len(sum.nonzero()[0]) != len(columns):
            print("Error: ")
            print("{0} != {1}".format(len(sum.nonzero()[0]), len(columns)))
            print(language_bookname)
        
        ngrams_by_language_count.append(collections.defaultdict(int))
        for j, c in enumerate(columns):
            ngrams_set.add(c)
            ngrams_by_language_count[i][c] = sum[j]

    ngrams_list = sorted(list(ngrams_set))
    matrix = numpy.zeros( ( len(ngrams_by_language_count), len(ngrams_list) ) )
    
    for i in range(len(ngrams_by_language_count)):
        for j, ngram in enumerate(ngrams_list):
            matrix[i][j] = ngrams_by_language_count[i][ngram]
            
    print(matrix)
    
if __name__ == "__main__":
    main(sys.argv)