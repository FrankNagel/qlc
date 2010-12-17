#!/usr/bin/python

import codecs
import regex
import unicodedata

file = codecs.open("heads_minor1987_1_126.txt", "r", "utf-8")

def getHeads(file):
    words = []
    for line in file:
        line = line.strip()
        tokens = line.split()
        words.append(tokens[0].strip())
    return words

words = getHeads(file)


def getNextGrapheme(n, s):
    result = ""
    for i in range(n, len(s)):
        # get first character
        if i == n:
            result += s[i]
            continue
        c = s[i]
        if unicodedata.combining(c):
            result += s[i]
    return result

def getPreviousGrapheme(n, s):
    result = ""
    for i in range(n-1, -1, -1):
        c = s[i]
        if unicodedata.combining(c):
            result += s[i]
            continue
        else:
            result += s[i]
            return result[::-1]


f = codecs.open("minor1987-vowels", "r", "utf-8")
vowels = f.readline()
vowels_combos = vowels+vowels
print "# pattern to match:", vowels_combos.encode("utf-8")
print

pattern = regex.compile("\X", regex.UNICODE)
temp_heads = codecs.open("temp_heads", "r", "utf-8")
print "head_word"+"\t"+"match"+"\t"+"V1"+"\t"+"V2"+"\t"+"preV1"+"\t"+"preV2"

for line in temp_heads:
    line = line.strip()
    matches = regex.finditer(vowels_combos, line, overlapped=True)
    graphemed = regex.findall("\X", line)

    # loop through iterator of dipthong matches
    for i in matches:
        result = line+"\t"
        diphthong = i.group()
        result += diphthong+"\t"

        # test for multiple same diphthongs in a word
        graphemes = regex.findall("\X", diphthong, regex.UNICODE)
        if len(graphemes) != 2:
            raise Exception, "too many graphemes in match"

        result += graphemes[0]+"\t" # get V1 in diphthong
        result += graphemes[1]+"\t" # get v2 in diphthong

        # deal with surrounding environments and get environments
        diphthong_span = i.span()

        if diphthong_span[0] == 0:
            result += "#"+"\t"
        else:
            result += getPreviousGrapheme(diphthong_span[0], line)+"\t"

        if len(line) == diphthong_span[1]:
            result += "#"+"\t"
        else:
            result += getNextGrapheme(diphthong_span[1], line)+"\t"

        print result.encode("utf-8")



"""
# an attempt with an list comp
for line in temp_heads:
    line = line.strip()
    print line
    lc = regex.findall(pattern, line)
    print lc
    m = [regex.search(vowels_combos, (x,y)) for x,y in lc.iter]
    for i in m:
        print i.group()
    print "#"
"""
