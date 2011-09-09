# -*- coding: utf-8 -*-

"""
Convenience class to parse Unicode graphemes
"""

import regex

class GraphemeParser(object):

    def __init__(self):
        self.grapheme_pattern = regex.compile("\X", regex.UNICODE)

    def getGraphemesFromString(self, string):
        self.string = string.strip()
        return self.grapheme_pattern.findall(string)

if __name__=="__main__":
    g = GraphemeParser()
    s = g.getGraphemesFromString("aaaaa")
    print s
