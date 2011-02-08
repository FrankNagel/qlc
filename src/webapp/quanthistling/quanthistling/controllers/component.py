import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from quanthistling.lib.base import BaseController, render

log = logging.getLogger(__name__)

from quanthistling.lib.base import BaseController, render
from quanthistling import model

class ComponentController(BaseController):

    def index(self):
        c.heading = 'Components Overview'
        c.components = model.meta.Session.query(model.Component)
        return render('/derived/component/index.html')
        
    def view(self, name):
        c.component = model.meta.Session.query(model.Component).filter(model.Component.name.op('ILIKE')(name)).first()
        c.heading = 'Component Contents: %s' % c.component.name
        return render('/derived/component/view.html')
