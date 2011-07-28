# -*- coding: utf-8 -*-
#!/usr/bin/env python

import codecs, unicodedata, sys

def main(argv):

    if len(argv) < 3:
        print "call: nfd2nfc.py in.txt out.txt"
        exit(1)
        
    IN = codecs.open(argv[1], "r", "utf-8")
    OUT = codecs.open(argv[2], "w", "utf-8")
    
    for line in IN:
        o = unicodedata.normalize("NFC", line)
        OUT.write(o)

if __name__ == "__main__":
    main(sys.argv)