# -*- coding: utf-8 -*-
#!/usr/bin/python

import csv
from qlc.comparison.languagecomparer import LanguageComparer
from qlc.comparison import aline
from qlc.distance.nj import Nj
filename = "data/asjp/salish.csv"

words = csv.reader(open(filename), quoting=csv.QUOTE_NONE, delimiter="\t")
languages = {}

for row in words:
    languages[row[0]] = row[3:]
    
x = LanguageComparer(languages, aline.ASJP, False)
x.generate_matrix()
print x.matrix
print x.column_names

nj = Nj(x.matrix, x.column_names)
nj.generate_tree()
print nj
nj.as_jpg(filename="njtree.jpg")


