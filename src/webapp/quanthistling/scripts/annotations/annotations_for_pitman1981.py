# -*- coding: utf8 -*-
from scipy.weave.base_spec import arg_spec_list

import sys, os
sys.path.append(os.path.abspath('.'))

import re

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions


pos_regex = r'\(.*?\)'
ord_regex = r'\d\. '
chars_to_exclude = [u' ', u'-', u'–', u')']


def _adjust_start(entry, start):
    chars_to_skip = 0
    for c in entry.fullentry[start:]:
        if c in chars_to_exclude:
            chars_to_skip += 1
        else:
            break
    return start + chars_to_skip


def _split_pos(entry, start, end):
    ps = start
    for comma in re.finditer('(?:[,] ?|$)', entry.fullentry[start:end]):
        pe = start + comma.start(0)
        if entry.fullentry[ps:pe].startswith('('):
            ps += 1
        if entry.fullentry[ps:pe].endswith(')'):
            pe -= 1
        entry.append_annotation(ps, pe, u'pos', u'dictinterpretation')
        ps = start + comma.end(0)


def _head_pos_in_range(entry, start, end):
    pos = re.search(pos_regex, entry.fullentry[start:end])
    head_start = _adjust_start(entry, start)

    if pos is not None:
        head = functions.insert_head(entry, head_start, pos.start(0))
        entry.append_annotation(pos.start(0) + 1, pos.end(0) - 1, u'pos', u'dictinterpretation')
    else:
        head = functions.insert_head(entry, head_start, end)

    return head


def _find_bracketed_at_range_start(entry, start, start_threshold):
    bracket_start = False
    bracketed = []
    for i, c in enumerate(entry.fullentry[start:]):
        if i > start_threshold and not bracket_start:
            return -1
        if c == '(':
            bracketed.append(start + i + 1)
            bracket_start = True
        elif c == ')':
            if bracket_start:
                bracketed.append(start + i)
                return bracketed
    return -1


def _split_translations(entry, start, end):
    part_start = start
    trans_end = end

    trans_ended = False
    s = 0
    # find the end of the translation
    while not trans_ended:
        period = entry.fullentry[start:end].find('.', s)
        for b in re.finditer(r'\(.*\)', entry.fullentry[start:end]):
            if b.start(0) < period < b.end(0):
                trans_ended = False
                s += period
                break
            else:
                trans_end = start + period
                trans_ended = True
        else:
            if period != -1:
                trans_end = start + period
            trans_ended = True

    # split the translations
    for match_semi_colon in re.finditer("(?:[,;] ?|$)",
                                        entry.fullentry[start:trans_end]):
        e = match_semi_colon.start(0)
        s = match_semi_colon.end(0)

        for b in re.finditer(r'\(.*\)', entry.fullentry[start:trans_end]):
            if b.start(0) <= match_semi_colon.end(0) <= b.end(0):
                e = b.end(0)
                break

        part_end = start + e

        part_start = _adjust_start(entry, part_start)

        functions.insert_translation(entry, part_start, part_end)
        if s > e:
            part_start = start + s
        else:
            part_start = start + e


def annotate_everything(entry):
    annot = [a for a in entry.annotations if a.value == 'head' or
             a.value == 'iso-639-3' or a.value == 'doculect' or
             a.value == 'pos' or a.value == 'translation']

    for a in annot:
        Session.delete(a)

    head_end = 0
    heads = []
    head = None

    ordinal = re.search(ord_regex, entry.fullentry)
    pos = re.search(pos_regex, entry.fullentry)

    if ordinal is not None:
        head_end = ordinal.start(0) - 1
        head = _head_pos_in_range(entry, 0, head_end)
        for o in re.finditer(r'(?<=\d\. )(.*?)(?:\d\. |$)', entry.fullentry):
            trans_start = o.start(1)
            end = o.end(1)
            trans_pos = _find_bracketed_at_range_start(entry, o.start(0), 5)
            if trans_pos != -1:
                entry.append_annotation(trans_pos[0], trans_pos[1], u'pos', u'dictinterpretation')
                trans_start = trans_pos[1] + 1

            trans_start = _adjust_start(entry, trans_start)
            _split_translations(entry, trans_start, end)
    elif pos is not None:
        head = _head_pos_in_range(entry, 0, pos.end(0))
        trans_start = _adjust_start(entry, pos.end(0))
        _split_translations(entry, trans_start, len(entry.fullentry))
    else:
        hifen = entry.fullentry.find('-')
        if hifen != -1:
            head = _head_pos_in_range(entry, 0, hifen - 1)
            _split_translations(entry, hifen + 1, len(entry.fullentry))
        else:
            functions.print_error_in_entry(entry, 'Could not annotate. ')

    if head is not None:
        heads.append(head)

    return heads


def main(argv):

    bibtex_key = u"pitman1981"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=108,pos_on_page=1).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=12,pos_on_page=8).all())

        startletters = set()
    
        for e in entries:
            # print 'current page: %i, pos_on_page: %i' % (e.startpage, e.pos_on_page)

            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
