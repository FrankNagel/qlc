# -*- coding: utf8 -*-
#!/usr/bin/env python3

"""
This script takes two or more dot files (you may use wildcards for filenames)
as input and combines the graphs of the files. Spanish translation are unified,
so that each spanish translation only has one node in the target graph. Head
words of native languages are still sperated in the target graph, so that head
words with the same string from two dictionaries are two nodes in the target
graph.
"""

import sys, codecs, os, glob
import regex as re

#from pygraph.classes.graph import graph
from qlc.TranslationGraph import write, read

def main(argv):
    
    if len(argv) < 4:
        print("call: translations_spanish_graph_connectstemswithoutstopwords.py graph_file_in_1.dot graph_file_in_2.dot [...] graph_file_out.dot", file=sys.stderr)
        sys.exit(1)
        
    IN = None
    file = sys.argv[1]
    if not os.path.exists(file):
        files = glob.glob(sys.argv[1])
        if len(files) == 0:
            print("No input files found.", file=sys.stderr)
            sys.exit(1)
        file = files.pop(0)
    else:
        files = argv[2:len(argv)-1]

    print("Processing file {0}.".format(file), file=sys.stderr)
    try:
        IN = codecs.open(file, "r", "utf-8")
    except:
        print("Could not open file {0}.".format(file), file=sys.stderr)
        sys.exit(1)
        
    gr = read(IN.read())
    IN.close()
        
    
    files = argv[2:len(argv)-1]
    
    for f in files:
        print("Processing file {0}.".format(f), file=sys.stderr)
        IN = codecs.open(f, "r", "utf-8")
        gr2 = read(IN.read())
        for node in gr2:
            gr.add_node(node, gr2.node[node])
        for n1, n2 in gr2.edges_iter():
                gr.add_edge(n1, n2, gr2.edge[n1][n2])
        IN.close()
    
    OUT = codecs.open(sys.argv[len(argv)-1], "w", "utf-8")
    OUT.write(write(gr))
    OUT.close()

if __name__ == "__main__":
    main(sys.argv)