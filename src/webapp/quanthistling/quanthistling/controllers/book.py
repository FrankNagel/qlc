# -*- coding: utf8 -*-
import os
import logging
import string, re
import datetime
import simplejson
import tempfile
import urllib2
from operator import attrgetter
from BeautifulSoup import BeautifulSoup

from pylons import request, response, session, tmpl_context as c, url
from pylons import config
from pylons.controllers.util import abort, redirect

from quanthistling.lib.base import BaseController, render
from quanthistling import model

from routes import url_for

import webhelpers.paginate as paginate
from webhelpers.html import literal

from sqlalchemy import and_
from turbomail import Message

log = logging.getLogger(__name__)

class BookController(BaseController):
    requires_auth = [ "edit_entryid", "save_entryid", "edit_entryid_wordlist", "save_entryid_wordlist" ]
   
    def __before__(self, bibtexkey=None, startpage=None, endpage=None, pagenr=None):
        # check if auth is needed
        if request.environ['pylons.routes_dict']['action'] in self.requires_auth:
            if 'user' not in session:
                session['path_before_login'] = request.environ.get('SCRIPT_NAME', '') + request.path_info
                session.save()
                return redirect(url_for(controller='login', action='login'))
                
        c.dictdata = None
        c.book = None
        if bibtexkey:
            c.book = model.meta.Session.query(model.Book).filter_by(bibtex_key=bibtexkey).first()
            c.corpushistory = model.meta.Session.query(model.Corpusversion).all()
            c.corpusversion = model.meta.Session.query(model.Corpusversion).order_by(model.Corpusversion.updated).first()
            c.iso_time = c.corpusversion.updated.strftime("%Y-%m-%dT%H:%M:%S")
            c.bibtexkey = bibtexkey
            if not c.book:
                abort(404)
            if c.book.type == "wordlist":
                c.startpage = c.book.wordlistdata_startpage()
                c.endpage = c.book.wordlistdata_endpage()
        if not startpage and not endpage and pagenr and bibtexkey:
            if c.book.type == "dictionary":
                c.dictdata = model.meta.Session.query(model.Dictdata).filter_by(book_id=c.book.id).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(pagenr)).first()
                if not c.dictdata:
                    abort(404)
                else:
                    c.srclanguage = c.dictdata.src_language.langcode
                    c.tgtlanguage = c.dictdata.tgt_language.langcode
                    c.startpage = c.dictdata.startpage
                    c.endpage = c.dictdata.endpage
            elif c.book.type == "wordlist":
                pass
                #c.startpage = model.meta.Session.query(func.max(model.Wordlistdata.startpage)).filter_by(book_id=c.book.id)
                #c.endpage = model.meta.Session.query(func.max(model.Wordlistdata.endpage)).filter_by(book_id=c.book.id)
        elif startpage and endpage and request.environ['pylons.routes_dict']['action'] != "nondictdata":
            c.dictdata = model.meta.Session.query(model.Dictdata).filter_by(book_id=c.book.id).filter_by(startpage=int(startpage), endpage=int(endpage)).first()
            if not c.dictdata:
                abort(404)
            else:
                c.srclanguage = c.dictdata.src_language.langcode
                c.tgtlanguage = c.dictdata.tgt_language.langcode
                c.startpage = int(startpage)
                c.endpage = int(endpage)

    def index(self):
        c.heading = 'List of Books'
        c.books = model.meta.Session.query(model.Book).order_by(model.Book.bibtex_key).all()
        #c.components = model.meta.Session.query(model.Component)
        return render('/derived/book/index.html')

    def wordlists(self):
        c.heading = 'List of Wordlist Books'
        c.books = model.meta.Session.query(model.Book).filter_by(type='wordlist').order_by(model.Book.bibtex_key).all()
        #c.components = model.meta.Session.query(model.Component)
        return render('/derived/book/wordlists.html')

    def view(self, bibtexkey):
        c.heading = c.book.bookinfo_with_status()
        #c.wikicontent = h.get_trac_wiki_book_article(bibtex_key)
        #c.error = ""
        if c.book.type == 'dictionary':
            return render('/derived/book/view.html')
        elif c.book.type == 'wordlist':
            return render('/derived/book/view_wordlist.html')
    
    def dictdata(self, bibtexkey, startpage, endpage, format):
        c.heading = ""
        if c.book:
            if format == 'xml':
                c.heading = c.book.bookinfo()
                #c.entries = model.meta.Session.query(model.Entry).filter(and_(model.Entry.dictdata_id==c.dictdata.id, model.Entry.is_subentry==False)).all()
                #c.entries = []
                xml_file = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%s-%s.xml" % (bibtexkey, startpage, endpage)),'rb')
                data = xml_file.read()
                xml_file.close()
                response.headers['content-type'] = 'text/xml; charset=utf-8'
                response.headers['content-disposition'] = 'attachment; filename=dictionary-%s-%s-%s.xml' % (bibtexkey, startpage, endpage)
                return data
            else:
                c.heading = c.book.bookinfo_with_status()
                return render('/derived/book/dictdata.html')
        else:
            abort(404)

    def create_xml_dictdata(self, bibtexkey, startpage, endpage, format):
        c.heading = c.book.bookinfo()
        if c.book:
            if format == 'xml':
                c.entries = model.meta.Session.query(model.Entry).filter(and_(model.Entry.dictdata_id==c.dictdata.id, model.Entry.is_subentry==False)).all()
                response.headers['content-type'] = 'text/xml; charset=utf-8'
                response.headers['content-disposition'] = 'attachment; filename=dictionary-%s-%s-%s.xml' % (bibtexkey, startpage, endpage)
                return render('/derived/book/dictdata.xml')
            else:
                abort(404)
        else:
            abort(404)
            
    def nondictdata(self, bibtexkey, title, startpage, endpage):
        c.book = model.meta.Session.query(model.Book).filter_by(bibtex_key=bibtexkey).first()
        nondictdata = model.meta.Session.query(model.Nondictdata).filter_by(book_id=c.book.id, startpage=int(startpage), endpage=int(endpage)).first()
        c.heading = '%s: %s (pp. %i - %i)' % (c.book.title, nondictdata.title, nondictdata.startpage, nondictdata.endpage)
        c.html = nondictdata.data
        c.html = re.sub(u"(?is)^.*<body.*?>", "", c.html)
        c.html = re.sub(r'(?is)</body>.*$', '', c.html)
        c.html = literal(c.html)
        if c.book and nondictdata:
            return render('/derived/book/nondictdata.html')
        else:
            abort(404)

    def annotations_for_dictdata(self, bibtexkey, startpage, endpage, annotationtype, format):
        c.heading = ""
        if c.book:
            if format == 'xml':
                c.heading = c.book.bookinfo() + ", Annotations"
                #c.entries = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).all()
                xml_file = open(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'xml', "dictionary-%s-%s-%s-%s-annotations.xml" % (bibtexkey, startpage, endpage, annotationtype)),'rb')
                data = xml_file.read()
                xml_file.close()
                response.headers['content-type'] = 'text/xml; charset=utf-8'
                response.headers['content-disposition'] = 'attachment; filename=dictionary-%s-%s-%s-%s-annotations.xml' % (bibtexkey, startpage, endpage, annotationtype)
                return data
            else:
                c.heading = c.book.bookinfo_with_status() + ", Annotations"
                return render('/derived/book/view.html')
        else:
            abort(404)
        
    def create_xml_annotations_for_dictdata(self, bibtexkey, startpage, endpage, annotationtype, format):
        c.heading = c.book.bookinfo() + ", Annotations"
        c.ces_doc_url = url_for(controller='book', action='create_xml_dictdata', bibtexkey=bibtexkey, startpage=startpage, endpage=endpage, format='xml', qualified=True)
        if c.book:
            if format == 'xml':
                c.entries = model.meta.Session.query(model.Entry).filter(model.Entry.dictdata_id==c.dictdata.id).all()
                if annotationtype == "formatting":
                    c.annotationtypes = [ "pagelayout", "formatting" ]
                elif annotationtype == "dictinterpretation":
                    c.annotationtypes = [ "dictinterpretation", "orthographicinterpretation", "errata" ]
                response.headers['content-type'] = 'text/xml; charset=utf-8'
                response.headers['content-disposition'] = 'attachment; filename=dictionary-%s-%s-%s-%s-annotations.xml' % (bibtexkey, startpage, endpage, annotationtype)
                return render('/derived/book/annotations_for_dictdata.xml')
            else:
                abort(404)
        else:
            abort(404)

    def page_with_layout(self, bibtexkey, pagenr):
        c.heading = c.book.bookinfo_with_status() + ", Page " + pagenr
        c.pagenr = pagenr
        c.entries = []
        c.action = 'page_with_layout'
        if c.book:
            pagenr_minus_one = int(pagenr)-1
            c.entries = model.meta.Session.query(model.Entry).filter_by(dictdata_id=c.dictdata.id,is_subentry=True).filter(and_(model.Entry.startpage==pagenr_minus_one, model.Entry.endpage==int(pagenr))).all()
            c.entries = c.entries + model.meta.Session.query(model.Entry).filter_by(dictdata_id=c.dictdata.id,is_subentry=False).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(pagenr)).all()
            return render('/derived/book/page_with_layout.html')
        else:
            abort(404)
        
    def page(self, bibtexkey, pagenr):
        c.heading = c.book.bookinfo_with_status() + ", Page " + pagenr
        c.pagenr = pagenr
        c.entries = []
        if c.book:
            if c.book.type == "dictionary":
                c.entries = model.meta.Session.query(model.Entry).filter_by(dictdata_id=c.dictdata.id,is_subentry=False).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(pagenr)).all()
                return render('/derived/book/page.html')
            elif c.book.type  == "wordlist":
                c.entries = model.meta.Session.query(model.WordlistEntry).join(
                    (model.Wordlistdata, model.Wordlistdata.id==model.WordlistEntry.wordlistdata_id)
                    ).filter(model.Wordlistdata.book_id==c.book.id).filter(
                    "wordlist_entry.startpage<=:pagenr and wordlist_entry.endpage>=:pagenr").params(pagenr=int(pagenr)).all()
                return render('/derived/book/page_wordlist.html')
        else:
            abort(404)
        
    def letter(self, bibtexkey, startpage, endpage, startletter):
        c.heading = c.book.bookinfo_with_status() + ", Letter " + startletter
        c.entries = []
        startletter_search = string.lower(startletter)
        if startletter == '_':
            startletter_search = '\_'
        if startletter == '(':
            startletter_search = '\('
        c.startletter = startletter
        if c.book:
            entries = model.meta.Session.query(model.Entry).join((model.Annotation, model.Annotation.entry_id==model.Entry.id)).filter(
                and_(
                    model.Entry.dictdata_id==c.dictdata.id,
                    model.Entry.is_subentry==False,
                    model.Annotation.value=='head',
                    model.Annotation.string.like(startletter_search + '%')
                    )
                ).all()
            c.paginator = paginate.Page(
                    entries,
                    page=int(request.params.get('page', 1)),
                    items_per_page = 30,
                )
            return render('/derived/book/letter.html')
        else:
            abort(404)

    def concept_wordlist(self, bibtexkey, concept):
        c.heading = c.book.bookinfo_with_status() + ", Concept " + concept
        c.concept = concept
        c.entries = []
        if c.book:
            if c.book.type  == "wordlist":
                concept_db = model.meta.Session.query(model.WordlistConcept).join(
                    (model.WordlistEntry, model.WordlistEntry.concept_id==model.WordlistConcept.id),
                    (model.Wordlistdata, model.Wordlistdata.id==model.WordlistEntry.wordlistdata_id)
                ).filter(model.Wordlistdata.book_id==c.book.id).filter(model.WordlistConcept.concept==concept).first()
                c.entries = concept_db.entries
                print "!!!!!!!!!!!!!!!!!"
                print c.entries
                return render('/derived/book/page_wordlist.html')                
        else:
            abort(404)

    def language_wordlist(self, bibtexkey, language_bookname, format):
        c.heading = c.book.bookinfo_with_status() + ", Language " + language_bookname
        c.language_bookname = language_bookname
        c.entries = []
        if c.book:
            if c.book.type  == "wordlist":
                wordlistdata_db = model.meta.Session.query(model.Wordlistdata).filter_by(book_id=c.book.id, language_bookname=language_bookname).first()
                c.entries = wordlistdata_db.entries
                return render('/derived/book/page_wordlist.html')
        else:
            abort(404)
        
    def entryid_wordlist(self, bibtexkey, language_bookname, concept, format):
        c.heading = ""
        c.entry = None
        c.concept = concept
        c.language_bookname = language_bookname
        if c.book:
            c.entry = model.meta.Session.query(model.WordlistEntry).join(
                    (model.WordlistConcept, model.WordlistConcept.id==model.WordlistEntry.concept_id),
                    (model.Wordlistdata, model.Wordlistdata.id==model.WordlistEntry.wordlistdata_id)
                ).filter(model.Wordlistdata.language_bookname==language_bookname).filter(model.WordlistConcept.concept==concept).first()

            #if format == 'xml':
            #    c.heading = c.book.bookinfo() + ", Entry " + pos_on_page + " on Page " + pagenr
            #    response.headers['content-type'] = 'text/xml; charset=utf-8'
            #    return render('/derived/book/entryid.xml')
            if format == 'py.txt':
                response.headers['content-type'] = 'text/plain; charset=utf-8'
                return render('/derived/book/entryid_wordlist.py.txt')            
            else:
                c.heading = c.book.bookinfo_with_status() + ", Concept " + concept + " in Language " + language_bookname
                return render('/derived/book/entryid_wordlist.html')
        else:
            abort(404)
        
    def edit_entryid_wordlist(self, bibtexkey, language_bookname, concept, format):
        c.heading = ""
        c.entries = []
        c.language_bookname = language_bookname
        c.concept = concept
        if c.book:
            c.entry = model.meta.Session.query(model.WordlistEntry).join(
                    (model.WordlistConcept, model.WordlistConcept.id==model.WordlistEntry.concept_id),
                    (model.Wordlistdata, model.Wordlistdata.id==model.WordlistEntry.wordlistdata_id)
                ).filter(model.Wordlistdata.language_bookname==language_bookname).filter(model.WordlistConcept.concept==concept).first()
            c.heading = c.book.bookinfo_with_status() + ", Concept " + concept + " in Language " + language_bookname
            c.saveurl = url_for(controller='book', action='save_entryid_wordlist', bibtexkey=c.book.bibtex_key, language_bookname=c.language_bookname, concept=c.concept, format='html')
            return render('/base/edit_entryid.html')
        else:
            abort(404)

    def save_entryid_wordlist(self, bibtexkey, language_bookname, concept, format):
        if c.book:
            c.entry = model.meta.Session.query(model.WordlistEntry).join(
                    (model.WordlistConcept, model.WordlistConcept.id==model.WordlistEntry.concept_id),
                    (model.Wordlistdata, model.Wordlistdata.id==model.WordlistEntry.wordlistdata_id)
                ).filter(model.Wordlistdata.language_bookname==language_bookname).filter(model.WordlistConcept.concept==concept).first()
            param_annotations = request.params.get("annotations", None)
            param_fullentry = request.params.get("fullentry", None)
            #print param_fullentry
            if c.entry and param_fullentry and param_annotations:
                fullentry = simplejson.loads(param_fullentry);
                annotations = simplejson.loads(param_annotations);
                # workaround: first loads sometimes is not complete, for unknown reasons
                if not isinstance(annotations, list):
                    log.error("workaround applied in save_entryid")
                    annotations = simplejson.loads(annotations)
                c.entry.fullentry = fullentry
                # delete all annotations in db
                for a in c.entry.annotations:
                    if a.annotationtype.type == "dictinterpretation" or a.annotationtype.type == "orthographicinterpretation" or a.annotationtype.type == "errata":
                        model.meta.Session.delete(a)
                # insert new annotations
                for a in annotations:
                    print a["string"].encode("utf-8")
                    c.entry.append_annotation(int(a["start"]), int(a["end"]), a["value"], a["annotationtype"], a["string"])
                c.entry.has_manual_annotations = True
                model.meta.Session.commit()
                
                # send mail
                message = Message("pbouda@cidles.eu", "pbouda@cidles.eu", "[quanthistling] Manual wordlist entry %s %s %s" % (bibtexkey, language_bookname, concept), encoding="utf-8")
                python_code = render('/derived/book/entryid_wordlist.py.txt')
                message.plain = "File attached."
                #print python_code.encode("utf-8")
                
                # create temporary file
                filename = u"%s_%s_%s.py.txt" % (bibtexkey, c.entry.startpage, c.entry.pos_on_page)
                tmpfile = tempfile.TemporaryFile()
                tmpfile.write(python_code.encode("utf-8"))
                tmpfile.flush()
                tmpfile.seek(0)
                message.attach(tmpfile, filename)
                message.send()
                tmpfile.close()
                return "success"
        abort(404)

    def entryid(self, bibtexkey, pagenr, pos_on_page, format):
        c.heading = ""
        c.entry = None
        c.pagenr = pagenr
        c.pos_on_page = pos_on_page
        if c.book:
            # only for python code, we use the same method "entryid" for wordlists
            # so that all .py files have similar filenames
            if c.book.type == "wordlist":
                c.entry = model.meta.Session.query(model.WordlistEntry).filter_by(startpage=int(pagenr), pos_on_page=int(pos_on_page)).first()
            else:
                c.entry = model.meta.Session.query(model.Entry).filter_by(startpage=int(pagenr), pos_on_page=int(pos_on_page), dictdata_id=c.dictdata.id).first()

            #c.annotations = sorted(c.entry.annotations, key=attrgetter('start'))
            if format == 'xml':
                c.heading = c.book.bookinfo() + ", Entry " + pos_on_page + " on Page " + pagenr
                response.headers['content-type'] = 'text/xml; charset=utf-8'
                return render('/derived/book/entryid.xml')
            elif format == 'py.txt':
                response.headers['content-type'] = 'text/plain; charset=utf-8'
                if c.book.type == "wordlist":
                    return render('/derived/book/entryid_wordlist.py.txt')            
                else:
                    return render('/derived/book/entryid.py.txt')            
            else:
                c.heading = c.book.bookinfo_with_status() + ", Entry " + pos_on_page + " on Page " + pagenr
                return render('/derived/book/entryid.html')
        else:
            abort(404)
   
    def edit_entryid(self, bibtexkey, pagenr, pos_on_page, format):
        c.heading = ""
        c.entries = []
        c.pagenr = pagenr
        c.pos_on_page = pos_on_page
        if c.book:
            c.entry = model.meta.Session.query(model.Entry).filter_by(startpage=int(pagenr), pos_on_page=int(pos_on_page), dictdata_id=c.dictdata.id).first()
            c.heading = c.book.bookinfo_with_status() + ", Entry " + pos_on_page + " on Page " + pagenr
            c.saveurl = url_for(controller='book', action='save_entryid', bibtexkey=c.book.bibtex_key, pagenr=c.pagenr, pos_on_page=c.pos_on_page, format='html')
            return render('/base/edit_entryid.html')
        else:
            abort(404)

    def save_entryid(self, bibtexkey, pagenr, pos_on_page, format):
        if c.book:
            c.entry = model.meta.Session.query(model.Entry).filter_by(startpage=int(pagenr), pos_on_page=int(pos_on_page), dictdata_id=c.dictdata.id).first()
            param_annotations = request.params.get("annotations", None)
            param_fullentry = request.params.get("fullentry", None)
            #print param_fullentry
            if c.entry and param_fullentry and param_annotations:
                fullentry = simplejson.loads(param_fullentry);
                annotations = simplejson.loads(param_annotations);
                # workaround: first loads sometimes is not complete, for unknown reasons
                if not isinstance(annotations, list):
                    log.error("workaround applied in save_entryid")
                    annotations = simplejson.loads(annotations)
                c.entry.fullentry = fullentry
                # delete all annotations in db
                for a in c.entry.annotations:
                    if a.annotationtype.type == "dictinterpretation" or a.annotationtype.type == "orthographicinterpretation" or a.annotationtype.type == "errata":
                        model.meta.Session.delete(a)
                # insert new annotations
                for a in annotations:
                    print a["string"].encode("utf-8")
                    c.entry.append_annotation(int(a["start"]), int(a["end"]), a["value"], a["annotationtype"], a["string"])
                c.entry.has_manual_annotations = True
                model.meta.Session.commit()
                
                # send mail
                message = Message("pbouda@cidles.eu", "pbouda@cidles.eu", "[quanthistling] Manual entry %s %s %s" % (bibtexkey, pagenr, pos_on_page), encoding="utf-8")
                python_code = render('/derived/book/entryid.py.txt')
                message.plain = "File attached."
                #print python_code.encode("utf-8")
                
                # create temporary file
                filename = u"%s_%s_%s.py.txt" % (bibtexkey, pagenr, pos_on_page)
                tmpfile = tempfile.TemporaryFile()
                tmpfile.write(python_code.encode("utf-8"))
                tmpfile.flush()
                tmpfile.seek(0)
                message.attach(tmpfile, filename)
                message.send()
                tmpfile.close()
                return "success"
        abort(404)

    #def dictinterpretation_annotations_for_entryid(self, bibtexkey, pagenr, pos_on_page, format):
    #    c.heading = ""
    #    c.entries = []
    #    c.annotationtypes = [ "dictinterpretation", "orthographicinterpretation", "errata" ]
    #    c.pagenr = pagenr
    #    c.pos_on_page = pos_on_page
    #    c.ces_doc_url = url_for(controller='book', action='entryid', bibtexkey=bibtexkey, pagenr=int(pagenr), pos_on_page=int(pos_on_page), format='xml', qualified=True)
    #    if c.book:
    #        c.entry = model.meta.Session.query(model.Entry).filter_by(dictdata_id=c.dictdata.id, startpage=int(pagenr), pos_on_page=int(pos_on_page)).first()
    #        #c.annotations = [ a for a in c.entry.annotations if a.annotationtype.type=='dictinterpretation' ]
    #        #c.annotations = sorted(c.annotations, key=attrgetter('start'))
    #        if format == 'xml':
    #            c.heading = c.book.bookinfo() + ", Entry " + pos_on_page + " on Page " + pagenr
    #            response.headers['content-type'] = 'text/xml; charset=utf-8'
    #            return render('/derived/book/annotations_for_entry.xml')
    #        else:
    #            c.heading = c.book.bookinfo_with_status() + ", Entry " + pos_on_page + " on Page " + pagenr
    #            return render('/derived/book/entryid.html')
    #    else:
    #        abort(404)

    #def formatting_annotations_for_entryid(self, bibtexkey, pagenr, pos_on_page, format):
    #    c.heading = ""
    #    c.entries = []
    #    c.annotationtypes = [ 'pagelayout', 'formatting' ]
    #    c.pagenr = pagenr
    #    c.pos_on_page = pos_on_page
    #    c.ces_doc_url = url_for(controller='book', action='entryid', bibtexkey=bibtexkey, pagenr=int(pagenr), pos_on_page=int(pos_on_page), format='xml', qualified=True)
    #    if c.book:
    #        c.entry = model.meta.Session.query(model.Entry).filter_by(dictdata_id=c.dictdata.id, startpage=int(pagenr), pos_on_page=int(pos_on_page)).first()
    #        #c.annotations = [ a for a in c.entry.annotations if a.annotationtype.type=='formatting' or a.annotationtype.type=='pagelayout' ]
    #        #c.annotations = sorted(c.annotations, key=attrgetter('start'))
    #        if format == 'xml':
    #            c.heading = c.book.bookinfo() + ", Entry " + pos_on_page + " on Page " + pagenr
    #            response.headers['content-type'] = 'text/xml; charset=utf-8'
    #            return render('/derived/book/annotations_for_entry.xml')
    #        else:
    #            c.heading = c.book.bookinfo_with_status() + ", Entry " + pos_on_page + " on Page " + pagenr
    #            return render('/derived/book/entryid.html')
    #    else:
    #        abort(404)
