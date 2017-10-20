#!/usr/bin/env python

# [START imports]
from google.appengine.ext import ndb
import webapp2
import jinja2
import json
import logging
import os
import hashlib
import urllib
import time
from google.appengine.api import urlfetch
# [END imports]

# [START State declaration]
class State(ndb.Model): 
    id = ndb.StringProperty(),
    state = ndb.StringProperty()
# [END State declaration]

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        state = hashlib.sha256(os.urandom(1024)).hexdigest() #generate a random key
        template_values = {
            'state' : state
        }

        # save the key to the datastore for later comparison
        new_key = State(id="", state=state)
        new_key.put()
        new_key.id = str(new_key.key.id())
        new_key.put()

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]

# [START OAuthHandler]
class OAuthHandler(webapp2.RequestHandler):

    def get(self):
        state = self.request.get('state') # get the state sent back
        logging.info(state)
        code = self.request.get('code') # get the code sent by server
        good_req = 0

        qry = State.query()
        qryResults = qry.fetch()
        for x in qryResults: #for each key in the data store, compare the state we got back
            if (x.state == state):
                good_req = 1
                stateId = x.id
                ndb.Key("State", long(x.key.id())).delete()

        if (good_req == 1):
            client_id = "128044531992-ro9noeiibg5ve0g1bmou1vqct9h2n02b.apps.googleusercontent.com"
            client_secret = "Y4qv8d-icvsC7nTUDE8AbgLK"
            redirect_uri = "https://oauth-2-implementation.appspot.com/oauth"

            payload = { #set up the post request to get the token
                'code' : code,
                'client_id' : client_id,
                'client_secret' : client_secret,
                'redirect_uri' : redirect_uri,
                'grant_type' : 'authorization_code'
            }

            #execute post request
            payload = urllib.urlencode(payload)
            result = urlfetch.fetch(url="https://www.googleapis.com/oauth2/v4/token", payload = payload, method=urlfetch.POST)

            time.sleep(0.3) # wait a little bit for the request to finish
            results = json.loads(result.content)
            token = results['access_token']
            
            template_values = {
                'state' : state,
                'token' : token
            }

            template = JINJA_ENVIRONMENT.get_template('oauth_landing.html')
            self.response.write(template.render(template_values))

        else:
            self.response.write("bad request")
# [END OAuthHandler]

class NameHandler(webapp2.RequestHandler):

    def post(self):
        state = self.request.get('state')
        token = self.request.get('token')

        auth_header = 'Bearer ' + token

        #set up the next request for the google plus info
        headers = {
            'Authorization' : auth_header
        }

        result = urlfetch.fetch(url="https://www.googleapis.com/plus/v1/people/me", headers = headers, method=urlfetch.GET)
        time.sleep(0.3) # wait a little bit for the request to finish
        results = json.loads(result.content)
        plusUser = results['isPlusUser']

        if (plusUser == True):
            firstName = results['name']['givenName']
            lastName = results['name']['familyName']
            url = results['url']
            template_values = {}
            template_values['state'] = state
            template_values['firstName'] = firstName
            template_values['lastName'] = lastName
            template_values['url'] = url

            template = JINJA_ENVIRONMENT.get_template('gplus.html')
            self.response.write(template.render(template_values))
        else:
            template = JINJA_ENVIRONMENT.get_template('non_gplus.html')
            self.response.write(template.render())

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/oauth', OAuthHandler),
    ('/name', NameHandler)
], debug=True)
# [END app]