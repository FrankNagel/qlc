#!/usr/bin/python

import sys
import codecs
import regex 

# you need to install regex library for this script to work
# usage: python unique_graphems.py /path/to/orthography_profile /path/to/heads_file
# if orthography file has duplicates, error will trigger

def main(argv):
    if len(argv) < 3:
        print "call: python check_orthography_profile.py /path/to/orthography_profile /path/to/heads_file"
        exit(1)

    grapheme_pattern = regex.compile("\X", regex.UNICODE)

    orthography_hash = {}
    headword_hash = {}

    # load orthography hash
    orthography_profile = codecs.open(sys.argv[1], "r", "utf-8")
    for line in orthography_profile:
        line = line.strip()
        if line == "":
            continue
        tokens = line.split(",")
        grapheme = tokens[0]
    
        if not orthography_hash.has_key(grapheme):
            orthography_hash[grapheme] = 1
        else:
            orthography_hash[grapheme] += 1
            print "you have duplicates in your orthography profile - fix it and rerun"
            sys.exit()
    orthography_profile.close()

    # load hash of unique graphemes from the dictionary heads file and get a list of headwords
    heads = []
    heads_file = codecs.open(sys.argv[2], "r", "utf-8")
    for line in heads_file:
        line = line.strip()
        tokens = line.split("\t")
        head = tokens[0]
        heads.append(head)

        graphemes = grapheme_pattern.findall(head)

        for grapheme in graphemes:
            grapheme = grapheme.strip()
            if grapheme == " " or grapheme == "":
                continue
            if not headword_hash.has_key(grapheme):
                headword_hash[grapheme] = 1
            else:
                headword_hash[grapheme] += 1
    heads_file.close()


    # print the orthography profile hash
    print "hash from orthography profile (grapheme, tab, count):"
    for k, v in orthography_hash.iteritems():
        print k.encode("utf-8"), "\t", v
    print "number of graphemes in orthography profile:", len(orthography_hash)
    print

    # print the heads unique grapheme hash
    print "hash of unique graphemes from headwords file (grapheme, tab, count):"
    for k, v in headword_hash.iteritems():
        print k.encode("utf-8"), "\t", v
    print "number of unique graphemes in headwords:", len(headword_hash)
    print


    # compare hashes orthography profile against headwords
    print "graphemes in head words and NOT in orthograhy profile file:"
    c1 = 0
    for k, v in headword_hash.iteritems():
        if not orthography_hash.has_key(k):
            print "ERROR:", k.encode("utf-8")
            c1 += 1
    if not c1 == 0:
        print "total:", c1
        print


    # compare hashes headwords against orthography profile
    print "graphemes in orthograhy profile and NOT in graphemes file (multigraphs not finished yet):"
    c2 = 0
    for k, v in orthography_hash.iteritems():
        if not headword_hash.has_key(k):
            print "ERROR:", k.encode("utf-8")
            c2 += 1
    if not c2 == 0:
        print "total:", c2
        print


    # check orthography profile contents against headwords
    print "check if orthography profile contents are not in the headwords:"
    missing_orthography_contents = []
    for k, v in orthography_hash.iteritems():
        flag = False
        for line in heads:
            if line.__contains__(k):
                flag = True
        if flag == False:
            missing_orthography_contents.append(k)

    if len(missing_orthography_contents) > 0:
        for item in missing_orthography_contents:
            print "NOT IN HEADWORDS:", item.encode("utf-8")
        print "total:", len(missing_orthography_contents)
    else:
        print "all orthography profile graphemes are present in the data"

    print

if __name__=="__main__":
    main(sys.argv)
       
       



