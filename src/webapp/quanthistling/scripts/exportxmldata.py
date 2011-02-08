# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import urllib

import logging

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import quanthistling.dictdata.books

def main(argv):
    log = logging.getLogger()
    logging.basicConfig(level=logging.INFO)
    
    conf = appconfig('config:development.ini', relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    #metadata.create_all(bind=Session.bind)

    #http://www.cidles.eu/quanthistling/book/minor1987/hto/spa?format=xml
    for b in quanthistling.dictdata.books.list:
        for data in b['dictdata']:
            mysock = urllib.urlopen("http://localhost:5000/source/%s/create_xml_dictdata/dictionary-%i-%i.xml" % (b['bibtex_key'], data["startpage"], data["endpage"]))
            fileToSave = mysock.read()
            oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i.xml" % (b['bibtex_key'], data["startpage"], data["endpage"])),'wb')
            oFile.write(fileToSave)
            oFile.close            
            mysock = urllib.urlopen("http://localhost:5000/source/%s/create_xml_annotations_for_dictdata/dictionary-%i-%i-formatting-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"]))
            fileToSave = mysock.read()
            oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-formatting-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"])),'wb')
            oFile.write(fileToSave)
            oFile.close            
            mysock = urllib.urlopen("http://localhost:5000/source/%s/create_xml_annotations_for_dictdata/dictionary-%i-%i-dictinterpretation-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"]))
            fileToSave = mysock.read()
            oFile = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%i-%i-dictinterpretation-annotations.xml" % (b['bibtex_key'], data["startpage"], data["endpage"])),'wb')
            oFile.write(fileToSave)
            oFile.close            
    
if __name__ == "__main__":
    main(sys.argv)
