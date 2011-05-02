# -*- coding: utf-8 -*-
#!/usr/bin/python

import csv
from qlc.comparison.languagecomparer import LanguageComparer
from qlc.comparison import aline
from qlc.distance import nj
from numpy import *

filename = "data/asjp/salish.csv"

file_data = open(filename, "rb")
file_content = csv.reader(file_data, quoting=csv.QUOTE_NONE, delimiter="\t")
languages = {}

language_names = []
max_strings_per_entry = 0
max_strings_per_row = 0
for row in file_content:
    strings = row[3:]
    if len(strings) > max_strings_per_row:
        max_strings_per_row = len(strings)
    languages[row[0]] = strings
    language_names.append(row[0])
    for s in strings:
        c = s.count("|") + 1
        if c > max_strings_per_entry:
            max_strings_per_entry = c

print max_strings_per_row
print max_strings_per_entry

file_data.seek(0)
language_data = zeros( (len(language_names), max_strings_per_row , max_strings_per_entry), dtype=unicode_)
i = 0
for row in file_content:
    #print row
    #strings = row[3:]
    j = 0
    for s in row[3:]:
        s_decode = s.decode("latin1")
        s_split = s_decode.split("|")
        k = 0
        for s_entry in s_split:
            if s_entry.find("//") != -1:
                s_entry = s_entry.split("//")[0]

            if i == 0:
                print j
                print k
                print s_entry
                print
                
            if s_entry != "":
                language_data[i,j,k] = s_entry
            k += 1
        j += 1
    i += 1

print language_data
    
x = LanguageComparer(languages, aline.ASJP, False)
x.generate_matrix()
print x.matrix
print x.column_names

nj = nj.Nj(x.matrix, x.column_names)
nj.generate_tree()
print nj
nj.as_jpg(filename="njtree.jpg")


