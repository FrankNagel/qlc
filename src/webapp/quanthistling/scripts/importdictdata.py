# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import logging

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.languages
import quanthistling.dictdata.books
import quanthistling.dictdata.components
import quanthistling.dictdata.annotationtypes

from paste.deploy import appconfig

import importbook
import importhuber1992
import importzgraggen1980
import importtoolboxfile

from annotations import *

def ann(ini_file, bibtex_key):
    eval("annotations_for_%s.main(['annotations_for_%s.py', ini_file])" % (bibtex_key, bibtex_key))

def main(argv):
    if len(argv) < 2:
        print "call: importdictdata.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    dictdata_path = 'quanthistling/dictdata'
    
    log = logging.getLogger()
    logging.basicConfig(level=logging.INFO)
    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)
    
    Session.query(model.Annotation).delete()
    Session.query(model.WordlistAnnotation).delete()
    Session.query(model.Entry).delete()
    Session.query(model.WordlistEntry).delete()

    Session.query(model.Wordlistdata).delete()

    # delete languages
    Session.query(model.LanguageTgt).delete()
    Session.query(model.LanguageSrc).delete()
    Session.query(model.LanguageIso).delete()
    Session.query(model.LanguageBookname).delete()
    #Session.query(model.LanguageWordlistdata).delete()

    Session.query(model.Dictdata).delete()
    Session.query(model.Nondictdata).delete()
    Session.query(model.Book).delete()
    Session.query(model.Component).delete()
    # delete annotationtypes
    Session.query(model.Annotationtype).delete()
    
    # insert languages
    for l in quanthistling.dictdata.languages.list:
        language = model.LanguageIso()
        language.name = l['name']
        language.langcode = l['langcode']
        language.description = l['description']
        language.url = l['url']
        Session.add(language)
        Session.commit()
        log.info("Inserted language " + l['name'] + ".")
        
    # insert components
    for c in quanthistling.dictdata.components.list:
        component = model.Component()
        component.name = c['name']
        component.description = c['description']
        Session.add(component)
        Session.commit()
        log.info("Inserted component " + c['name'] + ".")

    # insert annotationtypes
    for at in quanthistling.dictdata.annotationtypes.list:
        annotationtype = model.Annotationtype()
        annotationtype.type = at['type']
        annotationtype.description = at['description']
        Session.add(annotationtype)
        Session.commit()
        log.info("Inserted annotationtype " + at['type'] + ".")
        
    Session.close()
    
    for b in quanthistling.dictdata.books.list:
        importbook.main(['importbook.py', b['bibtex_key'], ini_file])
        if os.path.exists(
                os.path.join(
                    "scripts", "annotations", "annotations_for_{0}.py".format(
                        b['bibtex_key']))):
            log.info("Parsing annotations for " + b['bibtex_key'] + "...")
            eval("annotations_for_%s.main(['annotations_for_%s.py', ini_file])" % (b['bibtex_key'], b['bibtex_key']))
        else:
            log.info("No annotation script found for " + b['bibtex_key'] + "...")

        
    #for b in quanthistling.dictdata.wordlistbooks.list:
    importhuber1992.main(['importhuber1992.py', ini_file])
    importzgraggen1980.main(['importzgraggen1980.py', ini_file])
    importtoolboxfile.main(['importtoolboxfile.py', 'all', ini_file])

if __name__ == "__main__":
    main(sys.argv)
