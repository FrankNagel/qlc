# -*- coding: utf-8 -*-
"""
Two functions to read/write Translation Graphs. TGs are based in python-graph's
graph classes. Currently, the main reason to have our own functions is that we
need to alter the dot-file input and output. The original one uses pyparsing
which consumes a *lot* of memory even for files around 8 MB. Our graphs are
very simple so dot-files can easily be written and parsed without a real
parser. RE must be enough.
"""

import codecs
import re

from pygraph.classes.graph import graph

class WrongDotFormatException(Exception): pass

def read(string):
    """
    Read a graph from a string in Dot language and return it. Nodes and
    edges specified in the input will be added to the current graph.
    
    Args:
        - string: Input string in Dot format specifying a graph.
    
    Returns:
        - pygraph.classes.graph.graph object
    """
    lines = string.split("\n")
    first_line = lines.pop(0)
    if not re.match("graph \w+ {$", first_line):
        raise WrongDotFormatException("string contains no parseable graph")
        
    re_node = re.compile('^"([^"]*)"(?: \[([^]]*)\])?;?$')
    re_edge = re.compile('^"([^"]*)" -- "([^"]*)"(?: \[([^]]*)\])?;?$')
    
    gr = graph()
    
    for line in lines:
        line = line.strip()
        match_node = re_node.search(line)
        match_edge = re_edge.search(line)
        if match_node:
            g = match_node.groups()
            gr.add_node(g[0])
            if g[1]:
                for attribute_string in g[1].split(", "):
                    key, value = attribute_string.split("=")
                    gr.add_node_attribute(g[0], (key, value))
            
        elif match_edge:
            g = match_edge.groups()
            gr.add_edge((g[0], g[1]))
            if g[2]:
                for attribute_string in g[2].split(", "):
                    key, value = attribute_string.split("=")
                    gr.add_edge_attribute((g[0], g[1]), (key, value))
            
        elif line != "}" and len(line) > 0:
            raise WrongDotFormatException("Could not parse line:\n\t{0}".format(line))

    return gr
    

def write(gr):
    """
    Return a string specifying the given graph in Dot language.
    
    Args:
        - graph: pygraph.classes.graph.graph object
        
    Returns:
        - string: input graph in dot language
    """
    if not isinstance(gr, graph):
        raise TypeError("G is not a graph")
    
    graphname = "translationgraph"
    if 'name' in dir(gr):
        graphname = gr.name

    ret = "graph {0}".format(graphname)
    ret += " {\n"
    
    for n in gr.nodes():
        node_string = '"{0}"'.format(n)
        node_attributes = gr.node_attributes(n)
        if len(node_attributes) > 0:
            node_attributes_string_list = ["{0}={1}".format(a[0], a[1]) for a in node_attributes]
            node_string += " [{0}]".format(", ".join(node_attributes_string_list))
        node_string += ";\n"
        ret += node_string

    seen_edges = set()

    for e in gr.edges():
        if (e[0], e[1]) in seen_edges:
            continue
        edge_string = '"{0}" -- "{1}"'.format(e[0], e[1])
        edge_attributes = gr.edge_attributes(e)
        if len(edge_attributes) > 0:
            edge_attributes_string_list = ["{0}={1}".format(a[0], a[1]) for a in edge_attributes]
            edge_string += " [{0}]".format(", ".join(edge_attributes_string_list))
        edge_string += ";\n"
        ret += edge_string
        seen_edges.add((e[1], e[0]))

    ret += "}\n"
    return ret
