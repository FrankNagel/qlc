# -*- coding: utf8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))
import re

# Pylons model init sequence
import pylons.test
from paste.deploy import appconfig

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
import functions


head_garbage = re.compile('\s*l\.\s*(\(\*\)\s*)?')

def annotate_head(entry, start):
    heads = []

    sep = re.search('\.{2,} ', entry.fullentry)
    if not sep:
        functions.print_error_in_entry(entry, "Couldn't find head separator")
        return heads, len(entry.fullentry)
    end = sep.start()
    for h_start, h_end in functions.split_entry_at(entry, ', |$', start, end):
        match = head_garbage.match(entry.fullentry, h_start, h_end)
        if match:
            h_start = match.end()
        head = functions.insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)

    return heads, sep.end()


def annotate_translations(entry, start):
    end = len(entry.fullentry)
    for t_start, t_end in functions.split_entry_at(entry, '\s\.{3}\s|, |$', start, end):
        functions.insert_translation(entry, t_start, t_end)

    
def delete_dictinterpretation(entry):
    for a in entry.annotations:
        if a.annotationtype.type == 'dictinterpretation':
            Session.delete(a)

            
def main(argv):
    bibtex_key = u'ceona1928'

    if len(argv) < 2:
        print "call: annotations_for_%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata)\
      .join(model.Book, model.Dictdata.book_id == model.Book.id)\
      .filter(model.Book.bibtex_key == bibtex_key).all()

    for dictdata in dictdatas:
        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=308,pos_on_page=1).all()

        startletters = set()

        for e in entries:
            delete_dictinterpretation(e)
            start = functions.lstrip(e, 0, len(e.fullentry), '.')
            heads, start = annotate_head(e, start)
            annotate_translations(e, start)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())

        dictdata.startletters = unicode(repr(sorted(startletters)))

        Session.commit()


if __name__ == "__main__":
    main(sys.argv)
