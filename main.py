from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import json
import requests

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
def reply(user_id,msg):
	data = {
	"recipient": {"id": user_id},
	"message": {"text": msg}
	}
	resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + access_token, json=data)
	print(resp.content)

# @app.route('/', methods = ['POST'])
# def handle_incoming_messages():
# 	data = request.json
# 	sender = data['entry'][0]['messaging'][0]['sender']['id']
# 	message = data['entry'][0]['messaging'][0]['message']['text']
# 	attachment = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['url']
# 	reply(sender,attachment)
# 	return "ok"

@app.route('/', methods = ['POST'])
def handle_incoming_messages():
	data = request.json
	sender = data['entry'][0]['messaging'][0]['sender']['id']
	recieved_payload = data['entry'][0]['messaging'][0]['message']
	recieved_message = recieved_payload.get('text', "")
	attachment_url = recieved_payload.get('attachments',"")
	if attachment_url:
		attachment_url = attachment_url[0]['payload']['url']
	senders_dogs = Dogs.query.filter_by(owner = int(sender)).first()
	output_message = "\n Please give me a thumbs up to change your location; or one of the following commands, park, profile, reset"
	if senders_dogs is None:
		dogs = Dogs(recieved_message,int(sender),False)
		db.session.add(dogs)
		db.session.commit()
		output_message = "Welcome " + dogs.dogs_names + "\n You are currently home \n" + output_message
	if attachment_url.find('https://scontent.xx.fbcdn.net/t39.1997') == 0:
		senders_dogs.in_park = not (senders_dogs.in_park)
		db.session.add(senders_dogs)
		db.session.commit()
		if senders_dogs.in_park:
			output_message = "Enjoy the dog park " + senders_dogs.dogs_names + "! \n" + output_message
		else:
			output_message = "Enjoy home " + senders_dogs.dogs_names + "! \n" + output_message
	if recieved_message == "park":
		output_message = dogs_in_park_string() + output_message
	if recieved_message == "profile":
		output_message = "You are " + senders_dogs.dogs_names + "! \n" + output_message
	if recieved_message == "reset":
		db.session.delete(senders_dogs)
		db.session.commit()
		output_message = "Your data has been reset. \n Please enter the name of your dogs."
	reply(sender,output_message)
	return "ok"


# Formatting data methods
def dogs_in_park_string():
	dogs = Dogs.query.filter_by(in_park = True).all()
	string = "These Dogs are at the Park: \n"
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
	def __init__(self, dogs_names,owner,in_park):
		self.dogs_names = dogs_names
		self.in_park = in_park
		self.owner = owner
	def __repr__(self):
		return '<Name %r>' % self.dogs_names
