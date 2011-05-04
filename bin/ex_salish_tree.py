# -*- coding: utf-8 -*-
#!/usr/bin/python

import csv, sys
from qlc.comparison.languagecomparer import LanguageComparer
from qlc.comparison import aline
from qlc.distance import nj
from numpy import *

filename = "data/asjp/salish.csv"

file_data = open(filename, "rb")
file_content = csv.reader(file_data, quoting=csv.QUOTE_NONE, delimiter="\t")
languages = {}

language_names = []

#nr_of_languages = 20
#max_strings_per_row = 101
#max_strings_per_entry = 3
#max_string_length = 73

#max_strings_per_entry = 0
#max_strings_per_row = 0
#max_string_length = 0

#for row in file_content:
#    strings = row[3:]
#    if len(strings) > max_strings_per_row:
#        max_strings_per_row = len(strings)
#    languages[row[0]] = strings
#    language_names.append(row[0])
#    for s in strings:
#        s_decode = s.decode("latin1")
#        s_split = s_decode.split("|")
#        c = len(s_split)
#        if c > max_strings_per_entry:
#            max_strings_per_entry = c
#        for s_entry in s_split:
#            if len(s_entry) > max_string_length:
#                max_string_length = len(s_entry)

#print max_strings_per_row
#print max_strings_per_entry
#print max_string_length

#file_data.seek(0)
#language_data = zeros( (nr_of_languages, max_strings_per_row , max_strings_per_entry), dtype=(unicode_, max_string_length))

language_data = []
for row in file_content:
    language_names.append(row[0])
    language_concepts = []
    for s in row[3:]:
        if s == "":
            language_concepts.append([])
            continue
        s_decode = s.decode("latin1")
        s_split = s_decode.split("|")
        language_concept_entries = []
        for s_entry in s_split:
            if s_entry.find("//") != -1:
                s_entry = s_entry.split("//")[0]
            
            s_entry = s_entry.strip()
                
            if s_entry != "":
                language_concept_entries.append(s_entry)
        language_concepts.append(language_concept_entries)
    language_data.append(language_concepts)

x = LanguageComparer(language_data, aline.ASJP, False)
x.generate_matrix()
print x.matrix

nj = nj.Nj(x.matrix, language_names)
nj.generate_tree()
print nj
nj.as_jpg(filename="njtree.jpg")


