# -*- coding: utf8 -*-

import re
import sys

if len(sys.argv) < 3:
    print "call: xml_benaissa1991.py xml_in.xml xml_out.xml"
    exit(1)
    
print "Parsing " + sys.argv[1] + "..."

f1 = open(sys.argv[1], 'r')
f2 = open(sys.argv[2], 'w')

for l in f1:
    l = l.decode('utf-8')

    if not re.match(r'<p>\[(?:Seite|Spalte) \d+\]</p>', l) and not re.match(u'<p><b>\w\w? - \w\w?</b></p>', l):
        l = re.sub(r'<p>(?!\t)<b>', '<p><mainentry/><b>', l)
        l = re.sub(r'<p>\t<b>', '<p><subentry/><b>\t\t', l)

    if not re.match(u'<p><b>\w\w? - \w\w?</b></p>', l):
        f2.write(l.encode('utf-8'))

f1.close()
f2.close()