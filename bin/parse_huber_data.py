#!/usr/bin/python

import codecs
import sys
import operator # python-sort-a-dictionary-by-value

sys.path.append("../src/qlc/") # path to OrthographyProfile
import OrthographyProfile
import Ngram

"""
script to parse the huber data and output ngram matrices

"""

if len(sys.argv) != 4:
    sys.exit("Call: python parseHuberData.py len_of_ngram path_to_orthographyprofile path_to_huber_data \nE.g: python parseHuberData.py 2 ../data/orthography_profiles/Huber1992.txt counterparts_huber1992.txt")

# load orthography profile to parse linguistic forms from the dictionary
# load the ngram class to parse and calculate freqs of ngmrams
# load the huber database dump

o = OrthographyProfile.OrthographyProfile(sys.argv[2])
n = Ngram.Ngram()

# start the script
file = codecs.open(sys.argv[3], "r", "utf-8")

file_header = file.readline()
# COUNTERPART CONCEPT LANGUAGE_BOOKNAME LANGUAGE_CODE FAMILY BIBTEX_KEY

concept_container = {} 
data_container = {}
ngram_container = {}
language_ngram_sums = {}
language_names = {}

for line in file:
    line = line.strip()
    columns = line.split("\t")
    counterpart = columns[0]
    concept = columns[1]
    language_bookname = columns[2]
    language_code = columns[3]
    family = columns[4]
    bibtex_key = columns[5]

    if language_code == "spa" or language_code == "eng":
        continue

    # store the data
    if not data_container.has_key(language_bookname):
        data_container[language_bookname] = {}
        data_container[language_bookname][concept] = {}
    else:
        if not data_container[language_bookname].has_key(concept):
            data_container[language_bookname][concept] = {}

    # store the concepts
    if not concept_container.has_key(concept):
        concept_container[concept] = 1
    else:
        concept_container[concept] += 1

    # store language names
    if not language_names.has_key(language_bookname):
        language_names[language_bookname] = 1
    else:
        language_names[language_bookname] += 1

    # do the orthography parsing
    orthography_parse = o.parseToIpa(counterpart) # set to parse to Ipa; see also o.parse() for just graphemic parse
    orthography_parse = orthography_parse.replace("#", "")
    split_orthography_parse = orthography_parse.split()
    ngram_hash = n.getNgramsFromList(split_orthography_parse, int(sys.argv[1])) # set length of ngrams

    # keep track of all ngrams across all languages and their counts
    for k, v in ngram_hash.iteritems():
        if not ngram_container.has_key(k):
            ngram_container[k] = v
        else:
            ngram_container[k] += v

    # populate grams into hash of hash of hash
    for k, v in ngram_hash.iteritems():
        if not data_container[language_bookname][concept].has_key(k):
            data_container[language_bookname][concept][k] = v
        else:
            data_container[language_bookname][concept][k] += v            

    # populate language names and gram sums hash
    if not language_ngram_sums.has_key(language_bookname):
        language_ngram_sums[language_bookname] = {}
        for k, v in ngram_hash.iteritems():
            if not language_ngram_sums[language_bookname].has_key(k):
                language_ngram_sums[language_bookname][k] = v
            else:
                language_ngram_sums[language_bookname[k]] += v
    else:
        for k, v in ngram_hash.iteritems():
            if not language_ngram_sums[language_bookname].has_key(k):
                language_ngram_sums[language_bookname][k] = v
            else:
                language_ngram_sums[language_bookname][k] += v
                                    
                                    
    #print counterpart.encode("utf-8"), "\t", orthography_parse, "\t", split_orthography_parse, "\t", ngram_hash
    #print

#print ngram_container
#print len(ngram_container)

# print data container
def printDataContainer():
    for k, v in data_container.iteritems():
        print k, v
    print


# print ngrams by languages

# language_names_sorted = sorted(language_names.iteritems(), key=operator.itemgetter(1), reverse=True) 
# print language_names_sorted
def printLanguageNgrams():
    for k, v in language_ngram_sums.iteritems():
        print k, v
        print

def printSumGramsByLanguages():
    s = "ngram"
    for k, v in language_names.iteritems():
        s += "\t"+k
    print s.encode("utf-8")


    for ngram, count in ngram_container.iteritems():
        row = ngram
        for lang_name, concept_count in language_names.iteritems():
            if language_ngram_sums[lang_name].has_key(ngram):
                sum = language_ngram_sums[lang_name][ngram]
                row += "\t"+str(sum)
            else:
                row += "\t"+"0"
        print row.encode("utf-8").rstrip("\t")
        

# printSumGramsByLanguages()

def printAllNgrams():    
    for k, v in ngram_container.iteritems():
        print k.encode("utf-8"), "\t", v


# print everything
def printGramsByConceptsMatrix():
    s = "lang_name"+"\t"+"ngram"
    for k, v in concept_container.iteritems():
        s += "\t"+k.encode("utf-8")
    print s.rstrip("\t")

    # iterate through outter hash in container: language_bookname: {}
    s = ""
    for language_name, concept_hash in data_container.iteritems():

        # iterate over all ngrams
        for ngram, ngram_count in ngram_container.iteritems():
            s += language_name+"\t"+ngram
            # iterate through the x header of concepts
            for concept, ngram_hash in concept_container.iteritems():

                # check to see if the language has the concept
                if data_container[language_name].has_key(concept):

                    # if language has concept, check to see if that counterpart has the ngram
                    if data_container[language_name][concept].has_key(ngram):
                        count = data_container[language_name][concept][ngram]
                        s += "\t"+str(count)
                    else:
                        s += "\t"+"0"

                else:
                    s += "\t"+"NA"
                    
            print s.encode("utf-8").rstrip("\t")
            s = ""

printGramsByConceptsMatrix()

"""
# checks out ok -- 366 concepts
check_hash = {}
for k, v in data_container.iteritems():
    #print k.encode("utf-8"), v
    for k, v in v.iteritems():
        print k
        if not check_hash.has_key(k):
            check_hash[k] = 1
        else:
            check_hash[k] += 1
print len(check_hash)
"""

#print len(ngram_container)
