#!/usr/bin/python

import codecs
import regex
import unicodedata

# file = codecs.open("heads_minor1987_1_126.txt", "r", "utf-8")
file = codecs.open("syllable_forms-minor1987-1-126", "r", "utf-8")

# create list of head words
def getHeads(file):
    words = []
    for line in file:
        line = line.strip()
        tokens = line.split()
        words.append(tokens[0].strip())
    return words

words = getHeads(file)


def getNextGrapheme(n, s):
    """
*Very brittle function to search forward in a strng for the next grapheme, 
i.e. base character followed by any combining diacritics, given a position 
index in the string.

param:
n
int
index in the string at which the function should start

s
str
word to search through

return str (grapheme)

"""
    result = ""
    for i in range(n, len(s)):
        # test if next char is syllable marker (they can also take diacritics, so just return it!)
        if s[i] == "-":
            return "-"
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
        # test if next char is syllable marker (they can also take diacritics, so just return it!)
        if s[i] == "-":
            return "-"
        c = s[i]
        if unicodedata.combining(c):
            result += s[i]
            continue
        else:
            result += s[i]
            return result[::-1]

# load the vowels from a UTF-8 file
# NOTE: ordering in the regex matters (think phonological rules applying in order)
# you must order vowels from most diacritics to least, e.g. acute-nasal-a, acute-nasal-o, acute-a, acute-o, a, o)
f = codecs.open("minor1987-vowels", "r", "utf-8")
vowels = f.readline()

# create diphthong pattern and insert "-" for Minor syllabic forms
grapheme_pattern = regex.compile("\X", regex.UNICODE)
diphthong_pattern = vowels+"(-)?"+vowels

print "# pattern to match:", diphthong_pattern.encode("utf-8")
print
header = "head_word"+"\t"+"match"+"\t"+"diphthong?"+"\t"+"V1"+"\t"+"V2"+"\t"+"preV1"+"\t"+"postV2"
print header

vowel_sequences_across_syllables = {}

for line in words:
    line = line.strip()
    matches = regex.finditer(diphthong_pattern, line, overlapped=True)

    # loop through iterator of dipthong matches
    for i in matches:
        diphthong_flag = True # teat match as diphthong until proven not
        diphthong = i.group()

        if diphthong.__contains__("-"):
            diphthong_flag = False

        result = line+"\t"
        result += diphthong+"\t"

        # test for multiple same diphthongs in a word
        graphemes = regex.findall("\X", diphthong, regex.UNICODE)
        if len(graphemes) != 2 and len(graphemes) != 3:
            print graphemes
            raise Exception, "too many graphemes in match"


        # track the cross syallable vowel sequences
        if diphthong_flag:
            result += "yes"+"\t"
        else:
            result += "no"+"\t"
            if not vowel_sequences_across_syllables.has_key(str(graphemes)):
                 vowel_sequences_across_syllables[str(graphemes)] = 1
            else:
                vowel_sequences_across_syllables[str(graphemes)] += 1

        result += graphemes[0]+"\t" # get V1 in diphthong
        result += graphemes[-1]+"\t" # get v2 in diphthong


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

#        print graphemes, type(graphemes), "len:", len(graphemes)
#print header
#print 
#print "all vowel sequences across syllable boundaries"
#print vowel_sequences_across_syllables

"""
# an attempt with an list comp
for line in temp_heads:
    line = line.strip()
    print line
    lc = regex.findall(grapheme_pattern, line)
    print lc
    m = [regex.search(diphthong_pattern, (x,y)) for x,y in lc.iter]
    for i in m:
        print i.group()
    print "#"
"""
