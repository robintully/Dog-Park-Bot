from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timedelta
import json
import requests
import pdb

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
access_token = 'EAAKdHU7juZAkBAJaTsp6v57yPNPZBcWIwFn9ev6lGtxVSGX4gXBoUtWZAA67gABBX1sIzyo2prJFK0CZADLB8U4ZAIO4dikN4CbuIpJAQvcgYDnfPZBmPrNMnA6XpdfGyA8v0nZB8LG27QFoja0mMPKH0krc2bnMT9MDTAochOLGQZDZD'



# Routes for validation
@app.route('/', methods=['GET'])
def handle_verification():
	if request.args.get('hub.verify_token', '') == 'my_voice_is_my_password_verify_me':
		return request.args.get('hub.challenge', '')
	else:
		return 'wrong,token'

# Routes for sending messages
def reply(user_id,msg,include_button_choices,currently_at_park):
	if currently_at_park:
		change_location_message = "Go home"
	else:
		change_location_message= "Go to the park"
	if include_button_choices:
			data = 	{
			  "recipient":{
			    "id":user_id
			  },
			  "message":{
			    "text":msg,
			    "quick_replies":[
				{
				  "content_type":"text",
				  "title": change_location_message,
				  "payload":"CHANGE LOCATION"
				},
			      {
			        "content_type":"text",
			        "title": "Who is at the park?",
			        "payload":"DOGS AT PARK"
			      },
			      {
			        "content_type":"text",
			        "title":"Reset me",
			        "payload":"RESET ME"
			      }
			    ]
			  }
			}
	else:
		data = 	{
		  "recipient":{
			"id":user_id
		  },
		  "message":{
			"text":msg
		  }
		}
	resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + access_token, json=data)
	print(resp.content)



@app.route('/', methods = ['POST'])
def handle_incoming_messages():
	# Recieveed Variables
	data = request.json
	sender = data['entry'][0]['messaging'][0]['sender']['id']
	recieved_payload = data['entry'][0]['messaging'][0]['message']
	recieved_message = recieved_payload.get('text', "")
	attachment_url = recieved_payload.get('attachments',"")
	if attachment_url:
		attachment_url = attachment_url[0]['payload']['url']
	senders_dogs = Dogs.query.filter_by(owner = int(sender)).first()
	output_message = "\n Please select from the following or send a thumbs up \n"
	include_button_choices = True

	if senders_dogs is None:
		senders_dogs = Dogs(recieved_message,int(sender),False)
		db.session.add(senders_dogs)
		db.session.commit()
		output_message = "Welcome " + senders_dogs.dogs_names + "\n You are currently home \n If this is not the name of your dogs please select or type Reset me"
	# change location
	if recieved_message == "Go home" or recieved_message == "Go to the park" or attachment_url.find('https://scontent.xx.fbcdn.net/t39.1997') == 0:
		senders_dogs.in_park = not (senders_dogs.in_park)
		senders_dogs.timestamp = datetime.utcnow()
		db.session.add(senders_dogs)
		db.session.commit()
		if senders_dogs.in_park:
			output_message = "Enjoy the dog park " + senders_dogs.dogs_names + "! \n" + output_message
		else:
			output_message = "Enjoy home " + senders_dogs.dogs_names + "! \n" + output_message
	# at the park
	if recieved_message == "Who is at the park?":
		output_message = dogs_in_park() + output_message
	if recieved_message == "Reset me":
		db.session.delete(senders_dogs)
		db.session.commit()
		output_message = "Your data has been reset. \n Please enter the name of your dogs on one line ('Rover, Spot, and Olive')."
		include_button_choices = False
	reply(sender,output_message,include_button_choices,senders_dogs.in_park)
	return "ok"

# if lastplus.date < datetime.datetime.now()-datetime.timedelta(seconds=20):
#     print "Go"
# Formatting data methods
def dogs_in_park():
	dogs = Dogs.query.filter_by(in_park = True).all()
	for dog in dogs:
	    if dog.timestamp < datetime.now()-timedelta(seconds=20):
	        dog.in_park = False
	        db.session.add(dog)
	        db.session.commit()
	        dogs.remove(dog)
	if dogs == []:
	    return "The park is currently empty  \n"
	string = "These dogs are at the park: \n"
	for index,dogs in enumerate(dogs):
		string += str(index + 1)  + ". " + dogs.dogs_names + "\n"
	return string

def my_dogs_string(user):
	dogs = Dogs.query.filter_by(owner = int(user)).first()
	if dogs is None:
		return "No dogs found"
	return "Your dog(s) are " + dogs.dogs_names

# Models
class Dogs(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	dogs_names = db.Column(db.String(120), unique=True)
	owner = db.Column(db.String(120), unique=True)
	in_park = db.Column(db.Boolean)
	timestamp = db.Column(db.DateTime)

	def __init__(self, dogs_names,owner,in_park):
		self.dogs_names = dogs_names
		self.in_park = in_park
		self.owner = owner
		self.timestamp = datetime.utcnow()
	def __repr__(self):
		return '<Name %r>' % self.dogs_names
if __name__ == "__main__":
    app.run()
