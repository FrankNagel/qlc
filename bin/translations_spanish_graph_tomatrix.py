# -*- coding: utf8 -*-
#!/usr/bin/env python3

import sys, codecs, os, collections
from qlc.TranslationGraph import write, read

def main(argv):
    
    if len(argv) < 3:
        print("call: translations_spanish_graph_connectstemswithoutstopwords.py graph_file_in.dot matrix_file_out.csv")
        sys.exit(1)

    IN = codecs.open(sys.argv[1], "r", "utf-8")
    gr = read(IN.read())
    IN.close()
 
    print("Parse finished.", file=sys.stderr)

    matrix = {}
    sources = set()
    for node in gr.nodes():
        if ("is_stem", True) in gr.node_attributes(node):
            spanish_nodes = [n for n in gr[node] if ("lang", "spa") in gr.node_attributes(n)]
            head_nodes = []
            for sp in spanish_nodes:
                head_nodes += [n for n in gr[sp] if  ("lang", "spa") and ("is_stem", True) not in gr.node_attributes(n)]
            head_nodes = set(head_nodes)

            heads = collections.defaultdict(list)
            for head in head_nodes:
                (head, source) = head.split("|")
                sources.add(source)
                heads[source].append(head)
            matrix["|".join(sorted(spanish_nodes))] = heads

    OUT = codecs.open(argv[2], "w", "utf-8")
    sorted_sources = sorted(sources)
    OUT.write("{0}\t{1}\n".format("spa", "\t".join(sorted_sources)))
    for spanish in sorted(matrix):
        OUT.write(spanish)
        OUT.write("\t")
        sources_heads = []
        for source in sorted(sources):
            heads = [h for h in matrix[spanish][source]]
            sources_heads.append("|".join(sorted(heads)))
        OUT.write("\t".join(sources_heads))
        OUT.write("\n")
    OUT.close()

if __name__ == "__main__":
    main(sys.argv)