# -*- coding: utf-8 -*-

# requires that regex package is installed to get "\X" Unicode grapheme match
# http://pypi.python.org/pypi/regex/

import regex 

def parseGraphemes(string):
    grapheme_pattern = regex.compile("\X", regex.UNICODE)
    return grapheme_pattern.findall(string)

def storeHash(hash, k):
    if not hash.has_key(k):
        hash[k] = 1
    else:
        hash[k] += 1
    return hash

if __name__=="__main__":
    print "testing grapheme matcher - should return a list: ['a', 'a', 'a', 'a']"
    print "test:", parseGraphemes("aaaa")
    print
    print "test hash set"
    hash = {"a":1, "b":0}
    storeHash(hash, "a")
    storeHash(hash, "b")
    storeHash(hash, "c")
    print hash
    

