#!/usr/bin/python
# -*- coding: utf-8 -*-


import codecs
import re
import sys
import unicodedata

class SpanishDictionary:
    

    def __init__(self):
	self.hash = {} # Hash of Spanish Dictionary forms
        self.normalized_hash = {} # Hash of all the forms normalized (split on space, lowercased)
    
        self.lemario_dictionary_file = codecs.open("lemario-20101017.txt", "r", "utf-8")
        self.getForms(self.lemario_dictionary_file)
        
        self.coes_dictionary_file = codecs.open("/Users/ramon/Documents/SpanishDictionary/coes-lexemes/wordlist_from_coes.txt", "r", "utf-8")
        self.getFormsFromCoesDict(self.coes_dictionary_file)
        	
        self.stemmer_dictionary_file = codecs.open("/Users/ramon/Documents/lexemes_from_stemmer/voc.txt", "r", "utf-8")
        self.getForms(self.stemmer_dictionary_file)
        
        self.google_dictionary_file = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-0.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file)

        self.google_dictionary_file1 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-1.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file1)
        
        self.google_dictionary_file2 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-2.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file2)
        
        self.google_dictionary_file3 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-3.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file3)
        
        self.google_dictionary_file4 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-4.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file4)
        
        self.google_dictionary_file5 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-5.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file5)
        
        self.google_dictionary_file6 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-6.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file6)
        
        self.google_dictionary_file7 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-7.csv", "r", "utf-8")
        self.parseGoogleNgrams(self.google_dictionary_file7)
        
        self.google_dictionary_file9 = codecs.open("/Users/ramon/Documents/google_books_spa_corpus/googlebooks-spa-all-1gram-20090715-9.csv", "r", "utf-8")
	self.parseGoogleNgrams(self.google_dictionary_file9)
	
	
        self.normalized_hash = self.getNormalizedForms(self.hash)

    def parseGoogleNgrams(self, file):
	for line in file:
		line = unicodedata.normalize("NFD", line)
		line = line.strip()
		columns = line.split('\t')
		form = columns[0]
	        if not self.hash.has_key(form):
        		self.hash[form] = 1
		else:
			self.hash[form] += 1
	return self.hash



    def getNormalizedForms(self, hash):
        """ Take the hash of Spanish entries and parse out all words, normalize them, and create new hash.

        Note: doesn't handle things like punctuation, e.g. "..."
        """
        for k, v in hash.iteritems():
            forms = k.split()
            for form in forms:
                form = form.strip()
                form = form.lower()
                if not self.normalized_hash.has_key(form):
                    self.normalized_hash[form] = 1
                else:
                    self.normalized_hash[form] += 1
        return self.normalized_hash



    def getForms(self, file):
        
        for form in file:
	    form = unicodedata.normalize("NFD", form)
            form = form.strip()
            form = form.lower()
            if not self.hash.has_key(form):
                self.hash[form] = 1
            else:
                self.hash[form] += 1
        
        return self.hash
    
    def getFormsFromCoesDict(self, file):
	for form in file:
	    form = unicodedata.normalize("NFD", form)
	    form = form.strip()
	    form = form.lower()
	    if not self.hash.has_key(form):
		self.hash[form] = 1
	    else:
		self.hash[form] += 1
	return self.hash
	
    def printHash(self, hash):
        for k, v in hash.iteritems():
            print k.encode("utf-8"), "\t", v

    def lookUpForms(self, input_hash, normalized=1):
        """ Given a hash of forms, check to see which are not in the Spanish
        Dictionary hash
        """
        missing_count = 0
        for k, v in input_hash.iteritems():
            if not self.hash.has_key(k):
                print k.encode("utf-8")
                missing_count += 1
                
        if not missing_count == 0:
            print "Total missing forms: ", missing_count


if __name__=="__main__":
    if not len(sys.argv) == 2:
        raise Exception("Provide a filename on the command line!")
    file = codecs.open(sys.argv[1], "r", "utf-8")
    comparison_hash = {}
    for line in file:
        # do some processing to get the spanish forms
        line = line.replace("(", "")
        line = line.replace(")", "")
	line = line.replace(".", "")
	line = line.replace(":", "")
	line = line.replace(";", "")
	line = line.replace("/", " ")
	line = line.replace(" ?", "")
	line = line.replace("?", "")
	line = line.replace(u" ̅", "")
	line = line.replace(u"—", "")
	line = line.replace(u"–", "")
	line = line.replace("!", "")
	line = line.replace("-", "")
        line = line.replace(",", "")
        (spanish_translation, url) = line.split("\t")
        spanish_words = spanish_translation.split()

        for word in spanish_words:
            word = word.lower() # normalize
            if not comparison_hash.has_key(word):
                comparison_hash[word] = 1
            else:
                comparison_hash[word] += 1
	    
    # now make the comparison of the comparison hash against the dictionary
    s = SpanishDictionary()
    s.lookUpForms(comparison_hash)

    #s.printHash(s.normalized_hash)

