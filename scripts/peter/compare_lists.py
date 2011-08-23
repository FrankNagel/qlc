# -*- coding: utf8 -*-
#!/usr/bin/env python

import sys, codecs, re

set1 = set()
set2 = set()


F = codecs.open(sys.argv[1], "r", "utf-8")
for line in F:
    set1.add(line.strip().split("\t")[0])
F.close()

G = codecs.open(sys.argv[2], "r", "utf-8")
for line in G:
    set2.add(line.strip().split("\t")[0])
G.close()    

i = 0
for word in (set1 - set2):
    print "{0}: {1}".format(i, word.encode("utf-8"))
    i += 1