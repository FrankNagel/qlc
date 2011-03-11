#!/usr/bin/python

import sys
import codecs
import regex 
sys.path.append("../src/qlc/") # path to OrthographyProfile
import OrthographyProfile


# you need to install regex library for this script to work
# usage: python unique_graphems.py /path/to/orthography_profile /path/to/heads_file
# if orthography file has duplicates, error will trigger

def main(argv):
    if len(argv) < 3:
        print "call: python check_orthography_profile.py /path/to/orthography_profile /path/to/heads_file"
        exit(1)

    print

    grapheme_pattern = regex.compile("\X", regex.UNICODE)
    orthography_hash = {} # hash of graphemes in orthography profile
    headword_unicode_graphemes_hash = {} # hash of Unicode graphemes from head words
    head_words = []

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

    # create a list containing the headwords from the heads file
    heads_file = codecs.open(sys.argv[2], "r", "utf-8")
    for line in heads_file:
        line = line.strip()
        tokens = line.split("\t")
        head = tokens[0]
        head_words.append(head)
    heads_file.close()

    # load hash of unique graphemes from the dictionary heads file and get a list of headwords
    for head_word in head_words:
        graphemes = grapheme_pattern.findall(head_word)
        for grapheme in graphemes:
            grapheme = grapheme.strip()
            if grapheme == " " or grapheme == "":
                continue
            if not headword_unicode_graphemes_hash.has_key(grapheme):
                headword_unicode_graphemes_hash[grapheme] = 1
            else:
                headword_unicode_graphemes_hash[grapheme] += 1

    # print the orthography profile hash
    print "hash from orthography profile (grapheme, tab, count):"
    for k, v in orthography_hash.iteritems():
        print k.encode("utf-8"), "\t", v
    print "number of graphemes in orthography profile:", len(orthography_hash)
    print

    # print the heads unique unicode graphemes hash
    print "hash of unique unicode graphemes from headwords file - pre-orthography profile (grapheme, tab, count):"
    for k, v in headword_unicode_graphemes_hash.iteritems():
        print k.encode("utf-8"), "\t", v
    print "number of unique unicode graphemes in headwords:", len(headword_unicode_graphemes_hash)
    print

    """
    # compare hashes of Unicode regex \X graphemes vs headwords
    print "**Unicode** graphemes via regex '\X' match in head words and NOT in orthograhy profile file:"
    c1 = 0
    for k, v in headword_hash.iteritems():
        if not orthography_hash.has_key(k):
            print "ERROR:", k.encode("utf-8")
            c1 += 1
    if not c1 == 0:
        print "total:", c1
        print
        """

    # check orthography profile contents against headwords
    print "check if orthography profile contents are not in any headwords:"
    missing_orthography_contents = []
    for k, v in orthography_hash.iteritems():
        flag = False
        for line in head_words:
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


    # check headword graphemes against orthography profile contents
    orthography_profile_location = sys.argv[1]
    o = OrthographyProfile.OrthographyProfile(orthography_profile_location)
    ortho_parsed_graphemes = {}
    comparison_hash = {}
    incorrect_forms = []
    ln = 0
    for head in head_words:
        ln += 1
        orthography_parse = o.parse(head)
        parsed_graphemes = orthography_parse.split()
        for g in parsed_graphemes:
            if not ortho_parsed_graphemes.has_key(g):
                ortho_parsed_graphemes[g] = 1
            else:
                ortho_parsed_graphemes[g] += 1
            if not orthography_hash.has_key(g):
                comparison_hash[g] = 1
                incorrect_forms.append((ln, g, head, orthography_parse, parsed_graphemes))
    print "check headword graphemes against orthography profile contents"
    if len(comparison_hash) > 1:
        for k, v in comparison_hash.iteritems():
            print "not in orthography profile: ", k.encode("utf-8")
        print
        print "line", "\t", "miss", "\t", "hw", "\t", "ortho parse", "\t", "orth parse split"
        for i in incorrect_forms:
            if i[1] != "#" and i[1] != "-":
                print i[0], "\t", i[1].encode("utf-8"), "\t", i[2].encode("utf-8"), "\t", i[3].encode("utf-8"), "\t", i[4]

        print
        print "unique graphemes and counts from OrthographyProfile"
        for k, v in ortho_parsed_graphemes.iteritems():
            print k.encode("utf-8"), "\t", v

    else:
        print "all headword graphemes are in the orthography profile"


if __name__=="__main__":
    main(sys.argv)
       
       



