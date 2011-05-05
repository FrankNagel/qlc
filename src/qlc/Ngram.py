#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import sys


class Ngram(object):
    """
    Ngrams class

    """
    def __init__(self):        
        self.count = 0
        self.hash = {}

    def getListNgramsFromWord(self, word, n):
        list_of_grams = []
        for i in range(0, len(word)-n+1):
            list_of_grams.append(word[i:i+n])
        return list_of_grams

    def getNgramsFromList(self, list, n):
        hash = {}
        for i in range(0, len(list)-n+1):
            grams = list[i:i+n]
            gram = ""
            for i in grams:
                gram += i
            if not hash.has_key(gram):
                hash[gram] = 1
            else:
                hash[gram] += 1
            #print gram
        return hash


if __name__=="__main__":
    ngram = Ngram()
    x = ngram.getListNgramsFromWord("abcdef", 3)
    list = ["aa", "bb", "cc", "dd"]
    print list
    ngram.getHashNgramsFromList(list, 2)

    """
    file = codecs.open("counterparts_huber1992.txt", "r", "utf-8")

    # COUNTERPARTCONCEPTLANGUAGE_BOOKNAMELANGUAGE_CODEFAMILYBIBTEX_KEY
    header = file.readline()
    # print header.encode("utf-8")

    # kekinroPUNZAR_PIERCEtunebo centraltufCHIBCHAhuber1992
    hash = {}
    list_of_words = []

    line = file.readline()
    line = line.strip()
    columns = line.split("\t")
    counterpart = columns[0]
    language_code = columns[3]
    # print line.encode("utf-8")

    code = language_code
    list_of_words.append(counterpart)

    line_num = 2
    
    while line != "":
        # print len(line)
        line_num += 1
        line = file.readline()
        line = line.strip()
        columns =line.split("\t")
        # print len(columns), columns

        if len(columns) > 1:
            counterpart = columns[0]
            language_code = columns[3]

        if language_code != code:
            if not hash.has_key(language_code):
                hash[language_code] = list_of_words
            code = language_code
            list_of_words = []
            continue
        list_of_words.append(counterpart)

    if not hash.has_key(code):
        hash[code] = list_of_words

    for k, v in hash.iteritems():
        print k, v
        """
