# -*- coding: utf8 -*-

import sys, os, glob
import re
import codecs
import HTMLParser
sys.path.append(os.path.abspath('.'))

import quanthistling.dictdata.books
import quanthistling.dictdata.wordlistbooks

def main(argv):

    h = HTMLParser.HTMLParser()
    
    for book in quanthistling.dictdata.books.list + quanthistling.dictdata.wordlistbooks.list:

        if book["bibtex_key"] in [ "zgraggen1980b", "zgraggen1980c", "zgraggen1980d",
                "kraft1981-2", "kraft1981-3" ]:
            continue

        if book["bibtex_key"] == "kraft1981-1":
            book["bibtex_key"] = "kraft1981"

        print book["bibtex_key"]
        files = glob.glob("scripts/annotations/txt/%s_*.py.txt"%book["bibtex_key"])
        if len(files) > 0:
            output = codecs.open("scripts/annotations/manualannotations_for_%s.py"%book["bibtex_key"], "w", "utf-8")
            output.write("# -*- coding: utf8 -*-\n\nmanual_entries = []\n\n")
            for file in files:
                f = codecs.open(file, "r", "utf-8")
                content = f.read()
                content = re.sub("&#34;", "\\\"", content)
                content = h.unescape(content)
                #content = re.sub("\"", "\\\"", content)
                output.write(content)
                output.write("\n")
                f.close()
            output.close()
            
if __name__ == "__main__":
    main(sys.argv)
