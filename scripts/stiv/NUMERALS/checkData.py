#!/usr/bin/python3
# -*- coding: utf-8 -*-

# textutil -stdout -convert html INPUT_FILE_NAME.htm | grep '"p2"' > OUTPUT_FILE_NAME.html

import os
import re

def testLength(list, n):
    if len(list) != n:
        print (list)
        raise Exception("length doesn't match")

def parseFile(filename, file):
    count = 0
    total_count = 0
    # loop through lines in the file
    for line in file:
        line = line.strip()
        count += 1
        line = line.replace('<p class="p2">', "")
#        if line.startswith("Linguist"):
        if line.startswith("Note that"):
            print (count, "\t", filename, line)
            total_count += 1
    if total_count > 1:
        print (count, "\t", filename, line)


if __name__=="__main__":
    # list of files that have 1 ethnologue link
    # first past - 2635 of 2965 files
    dir = "output_data_lgs/"
    ethnologue_1_files = open("2635", "r")

    count = 0
    for filename in ethnologue_1_files:
        filename = filename.strip()
        file = open(dir+filename, "rt", encoding="utf-8")
        parseFile(filename, file)
        count += 1
        file.close()

    print (count)
