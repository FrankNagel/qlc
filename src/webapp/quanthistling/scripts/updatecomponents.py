# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.components

from paste.deploy import appconfig

def main(argv):
    if len(argv) < 2:
        print "call: updatecomponents.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    dictdata_path = 'quanthistling/dictdata'
    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)
    
    # update languages
    for c in quanthistling.dictdata.components.list:
        db_lang = Session.query(model.Component).filter_by(name=c['name']).first()
        if db_lang == None:
            component = model.Component()
            component.name = c['name']
            component.description = c['description']
            Session.add(component)
            Session.commit()
            print("Inserted component " + c['name'] + ".")
        

if __name__ == "__main__":
    main(sys.argv)
