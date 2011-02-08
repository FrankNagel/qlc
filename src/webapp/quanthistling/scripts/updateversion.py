# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import datetime

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.languages
import quanthistling.dictdata.books
import quanthistling.dictdata.annotationtypes

from paste.deploy import appconfig

version = 1
revision = 0

def main(argv):
    if len(argv) < 2:
        print "call: updateversion.py ini_file"
        exit(1)

    ini_file = argv[1]
        
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    new_version = False
    corpusversion = Session.query(model.Corpusversion).filter_by(version=version,revision=revision).first()
    if corpusversion == None:
        corpusversion = model.Corpusversion()
        new_version = True
    corpusversion.version = version
    corpusversion.revision = revision
    corpusversion.updated = datetime.datetime.now()
    if new_version:
        Session.add(corpusversion)
    Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)
