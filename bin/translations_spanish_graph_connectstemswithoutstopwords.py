# -*- coding: utf8 -*-
#!/usr/bin/env python3

"""
This script akes as input one dot files and output a corresponding dot file
which has additional edges between spanish translations. The additional edges
connect translations that have equal stems. Before the comparison stop words
will be removed from each translation. If you add the argument
"splitmultiwords", translations with more than one word will be splitted and
each word of the translation will be compared with each word of each other
translation.
"""

import sys, codecs, collections, unicodedata
import regex as re

from pygraph.classes.graph import graph
from pygraph.algorithms.traversal import traversal
from qlc.TranslationGraph import write, read

# snowball stemmer: http://snowball.tartarus.org/download.php
import Stemmer
stemmer = Stemmer.Stemmer('spanish')

def spanish_stopwords():
    stopwords = codecs.open("data/stopwords/spa.txt", "r", "utf-8")
    ret = set()
    for line in stopwords:
        word = line.rstrip("\n")
        word = re.sub(" *\|.*$", "", word)
        if re.search("[^\s]", word):
            word = unicodedata.normalize("NFD", word)
            ret.add(word)
    return ret

stopwords = spanish_stopwords()
re_stopwords = re.compile(r"\b(?:{0})\b".format( "|".join(stopwords).encode("utf-8") ))
re_spaces = re.compile(" +")

def remove_stopwords_and_stem(w, split_multiwords):
    #if w in stopwords:
    #    return []

    w = w.strip(" ")
    w_stop = w
    if " " in w_stop:
        w_stop = re_stopwords.sub("", w_stop)
        w_stop = w_stop.strip(" ")
        w_stop = re_spaces.sub(" ", w_stop)
    if " " in w_stop:
        if split_multiwords:
            return stemmer.stemWords(w_stop.split(" "))
        else:
            return([])
    elif len(w_stop) > 0:
        return [stemmer.stemWord(w_stop)]
    else:
        return([])

def main(argv):
    
    if len(argv) < 3:
        print("call: translations_spanish_graph_connectstemswithoutstopwords.py graph_file_in.dot graph_file_out.dot [splitmultiwords]")
        sys.exit(1)
        
    split_multiwords = False
    if len(argv) == 4 and argv[3] == "splitmultiwords":
        print("Will split multiwords.")
        split_multiwords = True

    IN = codecs.open(sys.argv[1], "r", "utf-8")
    gr = read(IN.read())
    IN.close()
 
    print("Parse finished.", file=sys.stderr)
    nodes = gr.nodes()

    i = 0    
    for n in gr.nodes():
        if ("lang", "spa") in gr.node_attributes(n):
            w1_stems = remove_stopwords_and_stem(n, split_multiwords)
            for stem in w1_stems:
                stem = stem + "|stem"
                if stem not in gr.nodes():
                    gr.add_node(stem, attrs=[('is_stem', True)])
                if (stem, n) not in gr.edges():
                    gr.add_edge((stem, n))
    
    OUT = codecs.open(sys.argv[2], "w", "utf-8")
    OUT.write(write(gr))
    OUT.close()

if __name__ == "__main__":
    main(sys.argv)