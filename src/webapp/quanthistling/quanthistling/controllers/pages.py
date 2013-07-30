import logging
import os, time

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons import config

from quanthistling.lib.base import BaseController, render

log = logging.getLogger(__name__)

from quanthistling.lib.base import BaseController, render
from quanthistling import model


class PagesController(BaseController):

    def index(self):
        c.heading = 'QuantHistLing Data'
        return render('/derived/pages/index.html')

    def dbdump_date(self):
        stats = os.stat(os.path.join(config['pylons.paths']['static_files'], 'downloads', 'csv', 'data.zip'))
        return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(stats[8]))