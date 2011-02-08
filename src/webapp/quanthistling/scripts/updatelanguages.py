# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import logging

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.languages

from paste.deploy import appconfig

def main(argv):
    if len(argv) < 2:
        print "call: updatelanguages.py ini_file"
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
    
    # update languages
    for l in quanthistling.dictdata.languages.list:
        db_lang = Session.query(model.Language).filter_by(name=l['name']).first()
        if db_lang == None:
            language = model.Language()
            language.name = l['name']
            language.langcode = l['langcode']
            language.description = l['description']
            language.url = l['url']
            Session.add(language)
            Session.commit()
            log.info("Inserted language " + l['name'] + ".")
        

if __name__ == "__main__":
    main(sys.argv)
