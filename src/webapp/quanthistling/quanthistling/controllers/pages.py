import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from quanthistling.lib.base import BaseController, render

log = logging.getLogger(__name__)

from quanthistling.lib.base import BaseController, render
from quanthistling import model


class PagesController(BaseController):

    def index(self):
        c.heading = 'Start page'
        return render('/derived/pages/index.html')
