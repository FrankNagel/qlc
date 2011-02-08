# -*- coding: utf8 -*-
import re
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from pylons.decorators import validate
from formencode import htmlfill
from webhelpers.html import literal

from quanthistling.lib.base import BaseController, render
from quanthistling import model
from quanthistling.model import form

from sqlalchemy import and_, or_

class SearchController(BaseController):

    def index(self):
        c.heading = 'Search dictionaries'
        c.dictdata = model.meta.Session.query(model.Dictdata).all()
        c.form = render('/component/search_form.html')
        return render('/derived/search/index.html')
        
    @validate(schema=form.SearchForm(), form='index', post_only=False, on_get=True, auto_error_formatter=form.custom_formatter)
    def result(self):
        c.heading = 'Search dictionaries - Results'
        c.result_by_dictdata = {}
        c.matches = 0
        dictdata_q = model.meta.Session.query(model.Dictdata)
        c.dictdata = dictdata_q.all()
        
        head = self.form_result['head'] #.lower()
        if '*' in head:
            head = re.sub(r'\*', r'%', head)
            
        fullentry = self.form_result['fullentry'] #.lower()
        #if '*' in fullentry:
        #    fullentry = re.sub(r'\*', r'%', fullentry)

        # create filters
        head_filter = None
        if head and ('%' in head):
            head_filter = and_(
                            model.Annotation.string.like(head),
                            model.Annotation.value=='head'
                        )
        else:
            head_filter = and_(
                            model.Annotation.string==head,
                            model.Annotation.value=='head'
                        )
            
        if head and fullentry:
            if self.form_result['logic'] == 'OR':
                entry_filter = or_(
                    head_filter,
                    model.Entry.fullentry.op('~')(fullentry)
                )
            else:
                entry_filter = and_(
                    head_filter,
                    model.Entry.fullentry.op('~')(fullentry)
                )
        elif head:
            entry_filter = head_filter
        elif fullentry:
            entry_filter = model.Entry.fullentry.op('~')(fullentry)
        
        searchinbooks = self.form_result['searchinbooks']
        if type(searchinbooks).__name__ != 'list':
            searchinbooks = [ searchinbooks ]
            
        for indictdata in searchinbooks:
            #entries_indictdata_q = entries_q.filter_by(dictdata_id=indictdata)
            dictdata = dictdata_q.filter_by(id=int(indictdata)).first()
            entries = []
            
            #entries_head_q = None
            entries_q = model.meta.Session.query(model.Entry).join(
                            (model.Annotation, model.Annotation.entry_id==model.Entry.id)
                        ).filter(
                            model.Entry.dictdata_id==int(indictdata)
#                            and_(
#                                model.Entry.dictdata_id==int(indictdata),
#                                model.Annotation.value=='head'
#                            )
                        )
                            
            entries = entries_q.filter(entry_filter).all()

            if len(entries) > 0:
                proc_entries = []
                for e in entries:
                    if e.is_subentry:
                        proc_entries.append(e.mainentry())
                    else:
                        proc_entries.append(e)
                entries = list(set(proc_entries))
                entries = sorted(entries, key=lambda entry: entry.id)
                c.result_by_dictdata[dictdata] = entries
                c.matches = c.matches + len(entries)
        c.form = literal(htmlfill.render(render('/component/search_form.html'), defaults=self.form_result))
        return render('/derived/search/result.html')
