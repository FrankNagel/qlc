# -*- coding: utf8 -*-
#!/usr/bin/env python

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
        for node in gr2.nodes():
            if not gr.has_node(node):
                gr.add_node(node, attrs=gr2.node_attributes(node))
        for edge in gr2.edges():
            if not gr.has_edge(edge):
                gr.add_edge(edge, attrs=gr2.edge_attributes(edge))
        IN.close()
    
    OUT = codecs.open(sys.argv[len(argv)-1], "w", "utf-8")
    OUT.write(write(gr))
    OUT.close()

if __name__ == "__main__":
    main(sys.argv)