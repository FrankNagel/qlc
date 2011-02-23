# -*- coding: utf8 -*-

import sys, os, glob
sys.path.append(os.path.abspath('.'))

import difflib

# import pylons modules
import pylons.test
from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig

# import dictdata module
import quanthistling.dictdata.books
import quanthistling.dictdata.wordlistbooks

def main(argv):
    
    if len(argv) < 2:
        print "call: insert_manualannotations.py ini_file"
        exit(1)

    ini_file = argv[1]   
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    for book in quanthistling.dictdata.books.list:
    #for book in []:
        #print book["bibtex_key"]
        
        try:
            exec("from manualannotations_for_%s import manual_entries" % book["bibtex_key"])
            print "adding manual annotations for %s" % book["bibtex_key"]
            
        except:
            print "no manual annotations for %s" % book["bibtex_key"]
            continue

        for e in manual_entries:
            dictdata = model.meta.Session.query(model.Dictdata).join(
                (model.Book, model.Dictdata.book_id==model.Book.id)
                ).filter(model.Book.bibtex_key==book["bibtex_key"]).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(e["startpage"])).first()
            
            if not dictdata:
                print "could not find dictdata for entry on page %s, pos on page %s in book %s" % (e["startpage"], e["pos_on_page"], book["bibtex_key"])
            
            entry_db = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
            ratio = difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio()
            if ratio > 0.80:
                entry_db.fullentry = e["fullentry"].decode('utf-8')
                # delete all annotations in db
                for a in entry_db.annotations:
                    Session.delete(a)
                # insert new annotations
                for a in e["annotations"]:
                    entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
                entry_db.has_manual_annotations = True
            else:
                print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem. (ratio: %f)" % (e["startpage"], e["pos_on_page"], ratio)

        Session.commit()

    for book in quanthistling.dictdata.wordlistbooks.list:
        #print book["bibtex_key"]
        
        try:
            exec("from manualannotations_for_%s import manual_entries" % book["bibtex_key"])
            print "adding manual annotations for %s" % book["bibtex_key"]
            
        except:
            print "no manual annotations for %s" % book["bibtex_key"]
            continue

        for e in manual_entries:
            wordlistdata = model.meta.Session.query(model.Wordlistdata).join(
                (model.Book, model.Wordlistdata.book_id==model.Book.id)
                ).filter(model.Book.bibtex_key==book["bibtex_key"]).filter("startpage<=:pagenr and endpage>=:pagenr and language_bookname=:language_bookname").params(pagenr=int(e["startpage"]),language_bookname=e["language_bookname"]).first()
            
            if not wordlistdata:
                print "could not find wordlistdata for entry on page %s, pos on page %s in book %s" % (e["startpage"], e["pos_on_page"], book["bibtex_key"])
            
            entry_db = Session.query(model.WordlistEntry).filter_by(wordlistdata_id=wordlistdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
            if not entry_db:
                print "could not find  entry on page %s, pos on page %s in book %s" % (e["startpage"], e["pos_on_page"], book["bibtex_key"])
                
            ratio = difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio()
            if ratio > 0.80:
                entry_db.fullentry = e["fullentry"].decode('utf-8')
                # delete all annotations in db
                for a in entry_db.annotations:
                    Session.delete(a)
                # insert new annotations
                for a in e["annotations"]:
                    entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
                entry_db.has_manual_annotations = True
            else:
                print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem. (ratio: %f)" % (e["startpage"], e["pos_on_page"], ratio)
        Session.commit()

    # Wordlists
            
if __name__ == "__main__":
    main(sys.argv)
