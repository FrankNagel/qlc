# -*- coding: utf8 -*-
#!/usr/bin/env python

import sys, codecs, collections, unicodedata
import re
#import regex as re

from pygraph.classes.graph import graph
from pygraph.algorithms.traversal import traversal
from qlc.TranslationGraph import write, read

# snowball stemmer: http://snowball.tartarus.org/download.php
import Stemmer
stemmer = Stemmer.Stemmer('spanish')

def memo(f):
    "Memoize function f."
    table = {}
    def fmemo(*args):
        if args not in table:
            table[args] = f(*args)
        return table[args]
    fmemo.memo = table
    return fmemo

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
re_stopwords = re.compile("\b(?:{0})\b".format("|".join(stopwords)))

@memo
def remove_stopwords_and_stem(w, split_multiwords = False):
    if w.startswith('"') and w.endswith('"'):
        w = w[1:-1]
    if w in stopwords:
        return []

    words = w.split(" ")
    w_stop = w
    if len(words) > 1:
        w_stop = re_stopwords.sub("", w_stop)
        w_stop = w_stop.strip(" ")
        w_stop = re.sub(" +", " ", w_stop)
        words = w_stop.split(" ")
    if not split_multiwords and len(words) == 1:
        return [stemmer.stemWord(w_stop)]
    elif split_multiwords:
        return stemmer.stemWords(words)
    else:
        return []

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
    
    for node1 in gr.nodes():
        if ("lang", "spa") in gr.node_attributes(node1):
            w1 = node1
            w1_stems = remove_stopwords_and_stem(w1, split_multiwords)
            if len(w1_stems) > 0:
                for node2 in gr.nodes():
                    if ("lang", "spa") in gr.node_attributes(node2) and not gr.has_edge((node1, node2)):
                        w2 = node2
                        if w1 == w2:
                            continue
                        w2_stems = remove_stopwords_and_stem(w2, split_multiwords)
                        if len(w2_stems) > 0:
                            if len(w1_stems) == 1 and len(w2_stems) == 1:
                                if w1_stems[0] == w2_stems[0]:
                                    gr.add_edge((node1, node2), attrs=[('same_stem', True)])
                            elif len(w1_stems) > 1 and len(w2_stems) == 1:
                                if w2_stems[0] in w1_stems:
                                    gr.add_edge((node1, node2), attrs=[('same_stem', True)])
                            elif len(w1_stems) == 1 and len(w2_stems) > 1:
                                if w1_stems[0] in w2_stems:
                                    gr.add_edge((node1, node2), attrs=[('same_stem', True)])
    
    OUT = codecs.open(sys.argv[2], "w", "utf-8")
    OUT.write(write(gr))
    OUT.close()

if __name__ == "__main__":
    main(sys.argv)