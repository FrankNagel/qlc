"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
import re
from webhelpers.html.tags import *
from routes import url_for

from quanthistling import model

from sqlalchemy.engine import create_engine
from creoleparser import text2html
from webhelpers.html import literal

from pylons import config

def js_escape_string(string):
    return literal(re.sub("'", "\\'", string))

def pycode_escape_string(string):
    return literal(re.sub("\"", "\\\"", string))

def get_components():
    return model.meta.Session.query(model.Component).order_by(model.Component.name).all()

def get_trac_wiki_book_article(bibtex_key):
    try:
        postgres_string = config["sqlalchemy.url"] + "trac"
        engine = create_engine(postgres_string)
        connection = engine.connect()
    except Exception:
        return "Could not connect to database. Does the database exist here?"
    else:
        wiki_text = ""
        result = connection.execute("select * from wiki where name = '%s' order by time desc" % bibtex_key)
        if result.rowcount > 0:
            row = result.fetchone()
            row_text = row['text'].decode("utf-8")
            wiki_text = text2html(row_text)
        else:
            wiki_text = "Could not find an entry for this book. Please check the trac wiki at <a href=\"http://trac.cidles.eu/wiki\">http://trac.cidles.eu/wiki</a>"
        connection.close()
        wiki_text = wiki_text + u"<p><small>Edit this page at <a href=\"http://trac.cidles.eu/wiki/%s\">http://trac.cidles.eu/wiki/%s</a></small></p>" % (bibtex_key, bibtex_key)
        return literal(wiki_text)
