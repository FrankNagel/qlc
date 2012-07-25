# -*- coding: utf8 -*-

import sys, os, glob, re
sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig

import quanthistling.dictdata.books
import quanthistling.dictdata.wordlistbooks

def main(argv):

    if len(argv) < 2:
        print "call: updatelanguages.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
        
    re_head = re.compile("{[^}{]+\"value\" : \"head\"[^}{]+},(?:\n|\r\n?)\s*")
    re_translation = re.compile("{[^}{]+\"value\" : \"translation\"[^}{]+},(?:\n|\r\n?)\s*")
    re_annotations = re.compile("\"annotations\" : \[(?:\n|\r\n?)\s*")
    #re_head2 = re.compile("\"value\": \"head\"")
    
    for b in quanthistling.dictdata.books.list:
        #book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()

        print b["bibtex_key"]
        files = glob.glob("scripts/annotations/txt/%s_[0-9]*_[0-9]*.py.txt"%b["bibtex_key"])
        if len(files) > 0:

            for file in files:
                match_id = re.search(r"_([0-9]*)_([0-9]*).py.txt$", file)
                pagenr = match_id.group(1)
                pos_on_page = match_id.group(2)
                                
                dictdata = model.meta.Session.query(model.Dictdata).join(
                        (model.Book, model.Dictdata.book_id==model.Book.id)
                    ).filter(model.Book.bibtex_key==b["bibtex_key"]).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(pagenr)).first()
                
                src_languages = dictdata.src_languages
                tgt_languages = dictdata.tgt_languages
                
                #print dictdata.src_languages[0].language_iso.langcode
                
                f = open(file, "r")
                lines = f.read().decode("utf-8")
                f.close()
                
                match_a = re_annotations.search(lines)
                lines2 = lines[:match_a.end(0)]

                if len(src_languages) == 1:
                    for match_head in re_head.finditer(lines):
                        if src_languages[0].language_iso:
                            a = match_head.group(0)
                            a = re.sub(u"\"value\" : \"head\"", u"\"value\" : \"iso-639-3\"", a)
                            a = re.sub(u"\"string\" : \"[^\"]*\"", u"\"string\" : \"{0}\"".format(src_languages[0].language_iso.langcode), a)
                            lines2 += a
                            

                        if src_languages[0].language_bookname:
                            a2 = match_head.group(0)
                            a2 = re.sub(u"\"value\" : \"head\"", u"\"value\" : \"doculect\"", a2)
                            a2 = re.sub(u"\"string\" : \"[^\"]*\"", u"\"string\" : \"{0}\"".format(src_languages[0].language_bookname.name), a2)
                            lines2 += a2

                if len(tgt_languages) == 1:
                    for match_translation in re_translation.finditer(lines):
                        if tgt_languages[0].language_iso:
                            a = match_translation.group(0)
                            a = re.sub(u"\"value\" : \"translation\"", u"\"value\" : \"iso-639-3\"", a)
                            a = re.sub(u"\"string\" : \"[^\"]*\"", u"\"string\" : \"{0}\"".format(tgt_languages[0].language_iso.langcode), a)
                            lines2 += a
                            

                        if tgt_languages[0].language_bookname:
                            a2 = match_translation.group(0)
                            a2 = re.sub(u"\"value\" : \"translation\"", u"\"value\" : \"doculect\"", a2)
                            a2 = re.sub(u"\"string\" : \"[^\"]*\"", u"\"string\" : \"{0}\"".format(tgt_languages[0].language_bookname.name), a2)
                            lines2 += a2

                lines2 += lines[match_a.end(0):]
                output = open(os.path.join("scripts/annotations/txt/lang", os.path.basename(file)), "w")
                output.write(lines2.encode("utf-8"))
                output.close()
            
if __name__ == "__main__":
    main(sys.argv)
