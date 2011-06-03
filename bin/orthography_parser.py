#!/usr/bin/python

import sys
import codecs
sys.path.append("../src/qlc/") # path to OrthographyProfile
import OrthographyProfile

def main(argv):
    if len(argv) < 3:
        print "call: python orthography_parser.py /path/to/orthography_profile /path/to/heads_file"
        exit(1)
    print

    # create a list containing the headwords from the heads file
    heads_file = codecs.open(sys.argv[2], "r", "utf-8")
    head_words = []

    for line in heads_file:
        line = line.strip()
        if line.__contains__("\t"):
            tokens = line.split("\t")
            head = tokens[0]
            head_words.append(head)
        else:
            head_words.append(line)
    heads_file.close()

    # parse head words with the orthography profile and print results
    orthography_profile_location = sys.argv[1]
    o = OrthographyProfile.OrthographyProfile(orthography_profile_location)
    for head in head_words:
        orthography_parse = o.parseToIpa(head)
        print orthography_parse.encode("utf-8")

if __name__=="__main__":
    main(sys.argv)
       
       



