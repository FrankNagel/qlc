# -*- coding: utf8 -*-

import sys, os, glob, re
sys.path.append(os.path.abspath('.'))

import codecs
import functions
import unicodedata

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig

import quanthistling.dictdata.books
import quanthistling.dictdata.wordlistbooks

def main(argv):

    for b in quanthistling.dictdata.books.list + quanthistling.dictdata.wordlistbooks.list:
        #book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()

        print b["bibtex_key"]
        files = glob.glob("scripts/annotations/txt/%s_[0-9]*_[0-9]*.py.txt"%b["bibtex_key"])
        if len(files) > 0:

            for file in files:
                f = codecs.open(file, "r", "utf-8")
                output = codecs.open(os.path.join("scripts/annotations/txt/lang", os.path.basename(file)), "w", "utf-8")
                last_was_doculect = False

                for line in f:
                    if last_was_doculect and re.search("\"string\" :", line):
                        line = functions.normalize_stroke(line)
                        line = unicodedata.normalize("NFD", line)

                    if re.search("\"language_bookname\" :", line):
                        line = functions.normalize_stroke(line)
                        line = unicodedata.normalize("NFD", line)

                    output.write(line)

                    last_was_doculect = False
                    if re.search("\"value\" : \"doculect\"", line):
                        last_was_doculect = True

                f.close()
                output.close()
            
if __name__ == "__main__":
    main(sys.argv)
