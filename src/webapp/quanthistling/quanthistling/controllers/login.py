import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from quanthistling.lib.base import BaseController, render

log = logging.getLogger(__name__)

class LoginController(BaseController):

   def login(self):
       """
       Show login form. Submits to /login/submit
       """
       c.heading = "Login"
       return render('/derived/login/login.html')

   def submit(self):
        """
        Verify username and password
        """
        # Both fields filled?
        #form_username = str(request.params.get('username'))
        form_password = str(request.params.get('password'))
    
        if form_password != 'mcrrjpsm':
            c.heading = "Login"
            return render('/derived/login/login.html')
            
        # Mark user as logged in
        session['user'] = 'user'
        session.save()
    
        # Send user back to the page he originally wanted to get to
        if session.get('path_before_login'):
            redirect(session['path_before_login'])
        else: # if previous target is unknown just send the user to a welcome page
            redirect(request.environ.get('SCRIPT_NAME', '/'))

