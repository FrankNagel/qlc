#!/usr/bin/python

import codecs
import re
import sys

class SpanishDictionary:
    """ Creates a hash of Spanish word forms from the Spanish-English FreeDict dictionary.
    See project: http://freedict.org/en/
    See project wiki: http://sourceforge.net/apps/mediawiki/freedict/
    See TEI dict format: http://www.tei-c.org/release/doc/tei-p5-doc/en/html/DI.html

    Dictionaries are provided in TEI format.

    Note: my use of self is pretty awful.

    """

    def __init__(self):
        self.hash = {} # Hash of Spanish Dictionary forms
        self.normalized_hash = {} # Hash of all the forms normalized (split on space, lowercased)

        self.dictionary_file = codecs.open("spa-eng/spa-eng.tei", "r", "utf-8")
        self.hash = self.getForms(self.dictionary_file)
        self.normalized_hash = self.getNormalizedForms(self.hash)


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
        """ Parse the TEI XML file, extract orthographic forms, add to hash.

        Match orthography tags: <orth>abolir</orth>        
        Note: this is quick hack that assumes only one match per line, as per the TEI format.
        """
        orth_match = re.compile("(<orth>)(.*)(</orth>)") 

        for line in file:
            match = orth_match.search(line)
            if match != None:
                spanish_form = match.group(2) # get the middle group in the regex
                if not self.hash.has_key(spanish_form):
                    self.hash[spanish_form] = 1
                else:
                    self.hash[spanish_form] += 1
        
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

    s.printHash(s.normalized_hash)

