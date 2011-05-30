# -*- coding: utf-8 -*-

"""
Orthography Profile class for parsing strings into Quantitiative Language Comparison format
"""

import codecs
import sys

class OrthographyProfile(object):
    """
    The orthography profile class for reading in a dictionary's 
    orthography profile and parsing and formating strings into the 
    agreed upon format:

    input string example: uubo
    output string example: # uu b o #
    """

    def __init__(self, orthography_profile):
        """
        Constructor of OrthographyProfile class. 

        Args:
        - orthography_profile (obligatory): the path to the orthography profile file
        in the file system.

        Returns:
        - nothing

        """
        
        # read in orthography profile and create a tree structure
        self.root = createTree(orthography_profile)

    def parse(self, string):
        """
        Returns the parsed and formated string given the graphemes encoded in the 
        orthography profile.

        Args:
        - string (obligatory): the string to be parsed and formatted

        Returns:    
        - the parsed and formatted string
        """
        self.string = string.replace(" ", "#") # add boundaries between words
        self.result = ""
        self.result += printMultigraphs(self, self.root, self.string, self.result+"# ")
        return self.result

# ---------- Tree node --------

class TreeNode(object):
    def __init__(self, char):
        self.char = char
        self.children = {}
        self.sentinel = False

    def isSentinel(self):
        return self.sentinel

    def getChar(self):
        return self.char

    def makeSentinel(self):
        self.sentinel = True

    def addChild(self, char):
        child = self.getChild(char)
        if not child:
            child = TreeNode(char)
            self.children[char] = child
        return child

    def getChild(self, char):
        if char in self.children:
            return self.children[char]
        else:
            return None

    def getChildren(self):
        return self.children

# ---------- Util functions ------
    
def createTree(file_name):
    # Internal function to add a multigraph starting at node.
    def addMultigraph(node, line):
        for char in line:
            node = node.addChild(char)
        node.makeSentinel()

    # Add all multigraphs in each line of file_name. Skip "#" comments and blank lines.
    root = TreeNode('')
    root.makeSentinel()
    file = codecs.open(file_name, "r", "utf-8")
    for line in file:
        line = line.strip()
        # skip any comments
        if line.startswith("#") or line == "":
            continue

        tokens = line.split(",") # split the orthography profile into columns
        grapheme = tokens[0]
        addMultigraph(root, grapheme)
    file.close()
    return root

def printMultigraphs(self, root, line, result):
    # Base (or degenerate..) case.
    if len(line) == 0:
        result += "#"
        return result

    # Walk until we run out of either nodes or characters.
    curr = 0   # Current index in line.
    last = 0   # Index of last character of last-seen multigraph.
    node = root
    while curr < len(line):
        node = node.getChild(line[curr])
        if not node:
            break
        if node.isSentinel():
            last = curr
        curr += 1

    # Print everything up to the last-seen sentinel, and process
    # the rest of the line, while there is any remaining.
    last = last + 1  # End of span (noninclusive).
    result += line[:last]+" "
    return printMultigraphs(self, root, line[last:], result)

def printTree(root, indent):
    children = ""
    for char, child in root.getChildren().iteritems():
        if child.isSentinel():
            char += "*"
        children += char + " "
    print indent + children
    for char, child in root.getChildren().iteritems():
        printTree(child, indent + "  ")

# ---------- Main ------

if __name__=="__main__":
    o = OrthographyProfile("../../data/orthography_profiles/Thiesen1998.txt")
    test_words = ["aa", "aabuu", "uuabaa auubaa"]
    for word in test_words:
        print o.parse(word)
        
