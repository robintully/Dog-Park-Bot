from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import json
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
PAT = 'EAAKdHU7juZAkBAJaTsp6v57yPNPZBcWIwFn9ev6lGtxVSGX4gXBoUtWZAA67gABBX1sIzyo2prJFK0CZADLB8U4ZAIO4dikN4CbuIpJAQvcgYDnfPZBmPrNMnA6XpdfGyA8v0nZB8LG27QFoja0mMPKH0krc2bnMT9MDTAochOLGQZDZD'

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


# Routes
@app.route('/', methods=['GET'])
def handle_verification():
	if request.args.get('hub.verify_token', '') == 'my_voice_is_my_password_verify_me':
		return request.args.get('hub.challenge', '')
	else:
		return 'Error, wrong validation token'

@app.route('/', methods=['POST'])
def handle_messages():
	payload = request.get_data()
	for sender, message in messaging_events(payload):
		output_message = "\n Please enter one of the following commands: change, dogs at park, profile, reset"
		dogs = Dogs.query.filter_by(owner = int(sender)).first()
		if dogs is None:
			dogs = Dogs(message,int(sender),False)
			db.session.add(dogs)
			db.session.commit()
			output_message = "Welcome " + dogs.dogs_names + "\n" + output_message
		if message == "change":
			dogs.in_park = not (dogs.in_park)
			db.session.add(dogs)
			db.session.commit()
			if dogs.in_park:
				output_message = "Enjoy the dog park " + dogs.dogs_names +  "! \n" + output_message
			else:
				output_message = "Enjoy home " + dogs.dogs_names +  "! \n" + output_message
		if message == "dogs at park":
			output_message = dogs_in_park_string() + output_message
		if message == "profile":
		    output_message = "You are " + dogs.dogs_names + "! \n" + output_message
		if message == "reset":
			db.session.delete(dogs)
			db.session.commit()
			output_message = "Your data has been reset. \n Please enter the name of your dogs."
		send_message(PAT, sender, output_message)
	return "ok"

def messaging_events(payload):
	data = json.loads(payload)
	messaging_events = data["entry"][0]["messaging"]
	for event in messaging_events:
		if "message" in event and "text" in event["message"]:
			yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
		else:
			yield event["sender"]["id"], "I can't echo this"

# The message value under data is what is returned
def send_message(token, recipient, text):
	r = requests.post("https://graph.facebook.com/v2.6/me/messages",
	params={"access_token": token},
	data=json.dumps({
		"recipient": {"id": recipient},
		"message": {"text": text}
	}),
	headers={'Content-type': 'application/json'})

# def determine_message(user_input, user):
# 	return {
# 	"a" : 1,
# 	"b": 2,
# 	"my dogs": my_dogs_string(user),
# 	"dogs at park": dogs_in_park_string()
# 	}.get(user_input,my_dogs_string(user))


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
