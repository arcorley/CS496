#!/usr/bin/env python

# [START imports]
from google.appengine.ext import ndb
import webapp2
import json
import logging
# [END imports]

# [START Boat declaration]
class Boat(ndb.Model): #set up the structure of boat data
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()
# [END Boat declaration]

# [START Slip declaration]
class Slip(ndb.Model): #set up structure of slip data
    id = ndb.StringProperty()
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
# [END Slip declaration]

# [START BoatHandler]
class BoatHandler(webapp2.RequestHandler):
    # [START post handler]
    def post(self): #post request handler
        boat_data = json.loads(self.request.body) #grab the body of the request

        if ('name' in boat_data.keys()): #handle name update
            nameVar = boat_data['name']
        else:
            nameVar = ""

        if ('type' in boat_data.keys()): #handle type update
            typeVar = boat_data['type']
        else:
            typeVar = ""

        if ('length' in boat_data.keys()): #handle length update
            lengthVar = boat_data['length']
        else:
            lengthVar = None

        if (nameVar == "" or typeVar == "" or lengthVar == None): #set up a response if incomplete data is sent
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.headers.add('Status', '400 Bad Request')
            r = {}
            r['message'] = "Incomplete data sent"
            self.response.write(json.dumps(r))
        else: #if complete data is supplied, 
            new_boat = Boat(id="", name=nameVar, type=typeVar, length=lengthVar, at_sea=True) #assign values 
            new_boat.put() #save the fields we have
            new_boat.id = str(new_boat.key.id()) #get the id generated by datastore
            new_boat.put() #save the id to the boat we created
            boat_dict = new_boat.to_dict() #convert to a dictionary
            boat_dict['self'] = '/boats/' + new_boat.key.urlsafe() #add self element to dictionary
            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.write(json.dumps(boat_dict)) #send back the results
    # [END post handler]

    # [START get handler]
    def get(self, id=None): #get request handler
        if id: #if an id is given, use this
            b = ndb.Key(urlsafe=id).get() #get the boat object referred to by that id
            b_d = b.to_dict() #convert to a dictionary
            b_d['self'] = "/boats/" + id #create the self link
            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')            
            self.response.write(json.dumps(b_d)) #send back the results
        else: #if no id is given, use this
            results = [] #create array to store query results
            qry = Boat.query()
            qryResults = qry.fetch()
            for x in qryResults: #for each result, serialize the output so it can be sent to JSON
                x_d = x.to_dict()
                x_d['self'] = "/boats/" + x.key.urlsafe()
                results.append(x_d) #add the dictionary to results
            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.write(json.dumps(results)) #respond with array of JSON objects
    # [END get handler]

    # [START patch handler]
    def patch(self, id): #update request handler
        b = ndb.Key(urlsafe=id).get() #get the existing boat by id
        boat_data = json.loads(self.request.body) #get the request parameters

        continueVar = 0

        #Check if any fields were sent to be updated
        if ('name' in boat_data.keys()): #if name is one of the fields requested to change, do this
            b.name = boat_data['name']
            continueVar = 1

        if ('type' in boat_data.keys()): #if type is one of the fields requested to change, do this
            b.type = boat_data['type']
            continueVar = 1

        if ('length' in boat_data.keys()): #if length is one of the fields requeested to change, do this
            b.length = boat_data['length']
            continueVar = 1

        if (continueVar == 1): #if a field was sent to be changed, continue
            b.put() #commmit the changes to the boat

            b_d = b.to_dict() #add the self link for the response
            b_d['self'] = "/boats/" + id

            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.write(json.dumps(b_d)) #send the response
        else: #if no update field was sent, send an error message
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.headers.add('Status', '400 Bad Request')
            r = {}
            r['message'] = "No fields submitted to update"
            self.response.write(json.dumps(r))            
    # [END patch handler]

    # [START put handler]
    def put(self, id): #replace request handler
        b = ndb.Key(urlsafe=id).get() #get the existing boat by id
        boat_data = json.loads(self.request.body) #get the request parameters

        if ('name' in boat_data.keys()): #handle name update
            nameVar = boat_data['name']
        else:
            nameVar = ""

        if ('type' in boat_data.keys()): #handle type update
            typeVar = boat_data['type']
        else:
            typeVar = ""

        if ('length' in boat_data.keys()): #handle length update
            lengthVar = boat_data['length']
        else:
            lengthVar = None

        if ('at_sea' in boat_data.keys()): #handle at_sea update
            at_sea = boat_data['at_sea']
        else:
            at_sea = True

        b.name = nameVar #assign new values to the boat
        b.type = typeVar
        b.length = lengthVar
        b.at_sea = at_sea

        b.put() #commit the changes to the boat

        b_d = b.to_dict() #write the self link
        b_d['self'] = "/boats/" + id

        self.response.write(json.dumps(b_d)) #send the response
    # [END put handler]

    # [START delete handler]
    def delete(self, id):
        b = ndb.Key(urlsafe=id).get()
        #if the boat is in a slip, empty the slip
        if (b.at_sea == False):
            #get the slip that has this boat as the current_boat
            qry = Slip.query()
            qryResults = qry.fetch()
            for x in qryResults: #for each result, check if the current_boat is equal to this boat's id
                if (x.current_boat == b.id):
                    slipId = x.id
                    break

            s = ndb.Key("Slip", long(slipId)).get() #get the slip object this boat is located in
            s.current_boat = "" #empty the slip
            s.arrival_date = ""      
            s.put()

        self.response.headers.add('Status', '200 OK')
        ndb.Key(urlsafe=id).delete()
    # [END delete handler]

# [END BoatHandler]

# [START SlipHandler]
class SlipHandler(webapp2.RequestHandler):
    # [START post handler]
    def post(self): #post request handler
        slip_data = json.loads(self.request.body) #grab the body of the request

        if ('number' in slip_data.keys()): #handle name update
            numberVar = slip_data['number']
        else:
            numberVar = None

        if ('arrival_date' in slip_data.keys()): #handle length update
            arrival_date = slip_data['arrival_date']
        else:
            arrival_date = ""

        existingNumber = 0
        qry = Slip.query() #query the slips data to check if the slip number entered already exists
        qryResults = qry.fetch()
        for x in qryResults: #iterate through each query result
            x_d = x.to_dict()
            if (x_d['number'] == numberVar): #compare the number in the results to the number provided request
                existingNumber = 1
                break

        if (numberVar == None): #set up a response if incomplete data is sent
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.headers.add('Status', '400 Bad Request')
            r = {}
            r['message'] = "Incomplete data sent"
            self.response.write(json.dumps(r))
        else: #if complete data is supplied
            if (existingNumber == 1): #if slip number already exists, return an error
                self.response.headers.add('Content-Type', 'Application/JSON')
                self.response.headers.add('Status', '400 Bad Request')
                r = {}
                r['message'] = "The slip number provided already exists"
                self.response.write(json.dumps(r))
            else: #otherwise, create the new slip and send a success response
                new_slip = Slip(id="", number=numberVar, current_boat="", arrival_date=arrival_date) #assign values 
                new_slip.put() #save the fields we have
                new_slip.id = str(new_slip.key.id()) #get the id generated by datastore
                new_slip.put() #save the id to the boat we created
                slip_dict = new_slip.to_dict() #convert to a dictionary
                slip_dict['self'] = '/slips/' + new_slip.key.urlsafe() #add self element to dictionary
                self.response.headers.add('Status', '200 OK')
                self.response.headers.add('Content-Type', 'Application/JSON')
                self.response.write(json.dumps(slip_dict)) #send back the results
    # [END post handler]

    # [START get handler]
    def get(self, id=None): #get request handler
        if id: #if an id is given, use this
            s = ndb.Key(urlsafe=id).get() #get the boat object referred to by that id
            s_d = s.to_dict() #convert to a dictionary
            s_d['self'] = "/slips/" + id #create the self link
            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')            
            self.response.write(json.dumps(s_d)) #send back the results
        else: #if no id is given, use this
            results = [] #create array to store query results
            qry = Slip.query()
            qryResults = qry.fetch()
            for x in qryResults: #for each result, serialize the output so it can be sent to JSON
                x_d = x.to_dict()
                x_d['self'] = "/slips/" + x.key.urlsafe()
                if (x.current_boat != ""): #if a new boat was passed in
                    b = ndb.Key("Boat", long(x.current_boat)).get()
                    x_d['boat_in_slip'] = "/boats/" + b.key.urlsafe()
                else:
                    x_d['boat_in_slip'] = ""
                results.append(x_d) #add the dictionary to results
            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.write(json.dumps(results)) #respond with array of JSON objects
    # [END get handler]

    # [START patch handler]
    def patch(self, id): #update request handler
        s = ndb.Key(urlsafe=id).get() #get the existing slip by id
        slip_data = json.loads(self.request.body) #get the request parameters

        continueVar = 0

        #Check if any fields were sent to be updated
        if ('number' in slip_data.keys()): #if name is one of the fields requested to change, do this
            s.number = slip_data['number']
            continueVar = 1

        if (continueVar == 1): #if the number field was updated, continue
            s.put() #commmit the changes to the slip

            s_d = s.to_dict() #add the self link for the response
            s_d['self'] = "/slips/" + id

            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.write(json.dumps(s_d)) #send the response
        else: #if no update field was sent, send an error message
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.headers.add('Status', '400 Bad Request')
            r = {}
            r['message'] = "No fields submitted to update"
            self.response.write(json.dumps(r))            
    # [END patch handler]

    # [START put handler]
    def put(self, id): #replace request handler
        s = ndb.Key(urlsafe=id).get() #get the existing slip by id
        slip_data = json.loads(self.request.body) #get the request parameters

        continueVar = 1 #set to 0 if any validations fail. This is a cue to prevent changes from being made

        #do some request parameter checking
        if ('number' in slip_data.keys()): #check that a number was sent along with request
            numberVar = slip_data['number']
        else:
            contineVar = 0
            numberVar = None
            self.response.headers.add('Status', '400 Bad Request')
            self.response.headers.add('Content-Type', 'Application/JSON')
            r = {}
            r['message'] = "Request didn't contain a slip number"
            self.response.write(json.dumps(r))
            return

        if ('current_boat' in slip_data.keys() and 'arrival_date' in slip_data.keys()): #if a boat is provided, an arrival date must be provided also
            boatVar = slip_data['current_boat']
            dateVar = slip_data['arrival_date']
        elif ('current_boat' not in slip_data.keys() and 'arrival_date' not in slip_data.keys()):
            boatVar = ""
            dateVar = ""
        else:
            continueVar = 0
            self.response.headers.add('Status', '400 Bad Request')
            self.response.headers.add('Content-Type', 'Application/JSON')
            r = {}
            r['message'] = "current_boat and arrival_date must both be provided or must both be empty"
            self.response.write(json.dumps(r))
            return

        #this section completes the put functionality if the request passes validation
        if (continueVar == 1):
            existingNumber = 0 #if 0, the slip number provided doesn't match an existing slip number

            #this section processes the slip number
            if (numberVar != s.number): #if a different number was provided, need to check that it doesn't match an existing slip
                qry = Slip.query() #query the slips data to check if the slip number entered already exists
                qryResults = qry.fetch()
                for x in qryResults: #iterate through each query result
                    x_d = x.to_dict()
                    if (x_d['number'] == numberVar): #compare the number in the results to the number provided request
                        existingNumber = 1
                        break

            if (existingNumber == 1): #if the slip number exists, return an error
                self.response.headers.add('Status', '400 Bad Request')
                self.response.headers.add('Content-Type', 'Application/JSON')
                r = {}
                r['message'] = "The slip number provided already exists"
                self.response.write(json.dumps(r))
                return
            else: #else, overwrite the slip number
                s.number = numberVar
                s.put()

            #this section processes the current_boat field
            if (s.current_boat == ""): #if field is currently empty
                if (boatVar != ""): #if requested field is not empty. if it is empty, we can just leave it alone
                    s.current_boat = boatVar #update the slip with the new id
                    b = ndb.Key("Boat", long(s.current_boat)).get() #get the boat with the id passed in
                    b.at_sea = False #update the boat's at_sea field
                    b.put()
            else: #if there is currently a boat in the slip
                cb = ndb.Key("Boat", long(s.current_boat)).get() #get the current_boat
                cb.at_sea = True #kick boat out of slip
                cb.put() #commit the change

                if (boatVar != ""): #if requested field is not empty
                    s.current_boat = boatVar #update the slip with the new id
                    b = ndb.Key("Boat", long(boatVar)).get() #get the boat with the id passed in
                    b.at_sea = False
                    b.put() #commit the change
                else:
                    s.current_boat = boatVar #set the current_boat field to empty

            s.put() #commit the changes to the slip

            #this section processes the arrival_date field
            s.arrival_date = dateVar
            s.put()

            #add the links to the response
            s_d = s.to_dict()
            s_d['self'] = "/slips/" + id #add the self link
            s_d['boat_in_slip'] = ""

            if (boatVar != ""): #if a new boat was passed in
                b = ndb.Key("Boat", long(boatVar)).get()
                s_d['boat_in_slip'] = "/boats/" + b.key.urlsafe()

            #send the response
            self.response.headers.add('Status', '200 OK')
            self.response.headers.add('Content-Type', 'Application/JSON')
            self.response.write(json.dumps(s_d))
            return
    # [END put handler]

    # [START delete handler]
    def delete(self, id):
        s = ndb.Key(urlsafe=id).get() #get the existing slip by id
        #currBoatInt = int(s.current_boat)
        
        #if there is a boat in the slip, need to change its at_sea property
        if (s.current_boat != ""):
            b = ndb.Key("Boat", long(s.current_boat)).get()
            b.at_sea = True
            b.put()

        self.response.headers.add('Status', '200 OK')
        ndb.Key(urlsafe=id).delete()
    # [END delete handler]    

# [END SlipHandler]

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.write("hello")
# [END main_page]

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boats', BoatHandler),
    ('/boats/(.*)', BoatHandler),
    ('/slips', SlipHandler),
    ('/slips/(.*)', SlipHandler)
], debug=True)
# [END app]