"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render

from quanthistling.model.meta import Session

#from quanthistling.lib.helpers import History
from pylons import request, response, session, tmpl_context as c, url

class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            Session.remove()

#    def __after__(self, action):
#        if 'history' in session:
#            c.history = session['history']
#            print "History in session"
#        else:
#            c.history = History(20)
#        
#            
#        if hasattr(c, 'heading'):
#            c.history.add(c.heading, url)
#
#        session['history'] = c.history
#        session.save()
#            
