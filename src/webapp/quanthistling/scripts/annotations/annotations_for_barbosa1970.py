# -*- coding: utf8 -*-

import sys, os

sys.path.append(os.path.abspath('.'))

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions


def annotate_everything(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or
                        a.value == 'iso-639-3' or a.value == 'doculect' or
                        a.value == 'translation']
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    chars_to_skip = [u'†', u'—', ' ']
    offset = 0
    for c in reversed(entry.fullentry[:head_end]):
        if c in chars_to_skip:
            offset += 1
        else:
            break

    head_end -= offset
    head = functions.insert_head(entry, 0, head_end)

    heads.append(head)

    italics = functions.get_list_ranges_for_annotation(entry, 'italic', head_end,
                                                       len(entry.fullentry))
    for i in italics:
        functions.insert_translation(entry, i[0], i[1])

    return heads


def main(argv):

    bibtex_key = u'barbosa1970'
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=26,pos_on_page=6).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
