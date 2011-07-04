# -*- coding: utf-8 -*-
#!/usr/bin/python

# Corresponding wiki page:
# http://code.google.com/p/qlc/wiki/PhyloTreeAsjp

import csv, sys
from qlc.comparison.languagecomparer import LanguageComparer
from qlc.comparison import aline
from qlc.distance import nj
from numpy import *

filename = "data/asjp/output_aline.txt"

file_data = open(filename, "rb")
file_content = csv.reader(file_data, quoting=csv.QUOTE_NONE, delimiter="\t")
languages = {}

language_names = []

language_data = []
for row in file_content:
    language_names.append(row[1])
    language_concepts = []
    for s in row[9:]:
        if s == "":
            language_concepts.append([])
            continue
        s_decode = s.decode("latin1")
        s_split = s_decode.split("|")
        language_concept_entries = []
        for s_entry in s_split:
            s_entry = s_entry.strip()
                
            if s_entry != "":
                language_concept_entries.append(s_entry)
        language_concepts.append(language_concept_entries)
    language_data.append(language_concepts)

x = LanguageComparer(language_data, aline.ASJP, False)
x.generate_matrix()
print x.matrix

# plot with our nj module
nj = nj.Nj(x.matrix, language_names)
nj.generate_tree()
#print nj
nj.as_png(filename="njtree.png")

# plot with rpy2
try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr

    L = robjects.StrVector(language_names)
    M = robjects.r['matrix'](list(x.matrix.flatten()), len(language_names))
    
    # workaround to set column names, there is a bug in rpy2:
    # https://bitbucket.org/lgautier/rpy2/issue/70/matrix-colnames-and-possibly-rownames
    M = robjects.r['as.data.frame'](M)
    M.colnames = L
    M = robjects.r['as.matrix'](M)

    print M

    ape = importr('ape')
    grdevices = importr('grDevices')

    tr = ape.nj(M)

    ofn = 'njtree.pdf'
    grdevices.pdf(ofn)
    robjects.r.plot(tr)
    grdevices.dev_off()

except:
    print "rpy2 not installed, I will not plot nj tree with R."

