#!/usr/bin/python

import codecs
import regex

file = codecs.open("../../heads_with_translations_minor1987_1_126", "r", "utf-8")

graphemes = regex.compile("\X", regex.UNICODE)

for line in file:
    line = line.strip()
    tokens = line.split("\t")
    print tokens[0]
    print graphemes.split(line, regex.UNICODE)
