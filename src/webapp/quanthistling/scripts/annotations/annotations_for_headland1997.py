# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re
import collections

# Pylons model init sequence
import pylons.test
from paste.deploy import appconfig

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
import functions


#sometimes the head is followed by someting in round or square brackets
#sometimes also in front of translations before pos
garbage = re.compile(r'\s*(\[[^]]*\]|\([^)]*\))\s*')

def annotate_head(entry):
    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)
    head_start = functions.lstrip(entry, 0, head_end, '-')

    for h_start, h_end in functions.split_entry_at(entry, r', |$', head_start, head_end):
        head = functions.insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)
    match = garbage.match(entry.fullentry, head_end)
    if match:
        head_end = match.end()
    return heads, head_end


def annotate_pos(entry, start, end):
    italics = [i for i in functions.get_list_italic_ranges(entry) if i[0] >= start and i[1] <= end]
    if not italics or italics[0][0] - start > 1:
        return start
    italics = italics[0]
    if entry.fullentry[italics[0]:italics[1]].strip() == 'ej.':
        return end
    entry.append_annotation(italics[0], italics[1], u'pos', u'dictinterpretation')
    return italics[1]

def relevant_newlines(entry):
    """Ignore newlines followed by two tabs, which indicates a continued line
    """
    newlines = [n[0] for n in functions.get_list_ranges_for_annotation(entry, 'newline')]
    tabs = [n.start for n in entry.annotations if n.value == 'tab']
    counter = collections.Counter(tabs)
    return [n for n in newlines if counter[n+1] == 1]

def annotate_translations(entry, start, end):
    newlines = relevant_newlines(entry)
    brackets = [n[0] for n in functions.find_brackets(entry) if n[0] >= start and n[0] <= end]
    for num_start, num_end in functions.split_entry_at(entry, r'\d\. |$', start, end):
        #skip parts in round brackets
        match = garbage.match(entry.fullentry, num_start, num_end)
        if match:
            num_start = match.end()
        #sometimes there is a pos after the number
        num_start = annotate_pos(entry, num_start, num_end)
        num_end = next((n for n in newlines if n > num_start and n < num_end), num_end)
        num_end = next((n for n in brackets if n > num_start and n < num_end), num_end)
        for t_start, t_end in functions.split_entry_at(entry, r';|$', num_start, num_end):
            functions.insert_translation(entry, t_start, t_end)


def delete_dictinterpretation(entry):
    for a in entry.annotations:
        if a.annotationtype.type == 'dictinterpretation':
            Session.delete(a)


def main(argv):
    bibtex_key = u'headland1997'

    if len(argv) < 2:
        print 'call: annotations_for%s.py ini_file' % bibtex_key
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=216,pos_on_page=16).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=62,pos_on_page=7).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=61,pos_on_page=1).all())

        startletters = set()

        for e in entries:
            delete_dictinterpretation(e)
            heads, start = annotate_head(e)
            start = annotate_pos(e, start, len(e.fullentry))
            annotate_translations(e, start, len(e.fullentry))
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())

        dictdata.startletters = unicode(repr(sorted(startletters)))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
