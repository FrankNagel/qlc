# -*- coding: utf-8 -*-

import collections
import numpy

def ngrams_from_graphemes(graphemes, n):
    list_of_grams = []
    for i in range(0, len(graphemes)-n+1):
        list_of_grams.append(graphemes[i:i+n])
    return list_of_grams


def words_ngrams_matrix_for_graphemes_list(graphemes_list, n):
    ngrams_counts = list()
    ngrams_set = set()
    row_names = list()
    for i, graphemes in enumerate(graphemes_list):

        ngrams_counts.append(collections.defaultdict(int))
        row_names.append(graphemes)
        ngrams = ngrams_from_graphemes(graphemes, n)

        for ngram in ngrams:
            ngrams_counts[i][ngram] += 1
            ngrams_set.add(ngram)

    ngrams_list = sorted(list(ngrams_set))
    matrix = numpy.zeros( ( len(row_names), len(ngrams_list) ) )
    
    for i in range(len(row_names)):
        for j, ngram in enumerate(ngrams_list):
            matrix[i][j] = ngrams_counts[i][ngram]

    return (row_names, ngrams_list, matrix)