# -*- coding: utf-8 -*-

# requires that regex package is installed to get "\X" Unicode grapheme match
# http://pypi.python.org/pypi/regex/

import regex 

def parseGraphemes(string):
    grapheme_pattern = regex.compile("\X", regex.UNICODE)
    return grapheme_pattern.findall(string)


if __name__=="__main__":
    print("testing grapheme matcher")
    print(parseGraphemes("aaaa"))
