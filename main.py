import os
import string
import secrets
from flask import Flask, request
from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from wtforms import Form, StringField, validators
from wtforms.validators import (DataRequired, Email)
from flask_cors import CORS

# Get constants from env variables
PYTHON_PASSWORD = os.environ['PYTHON_PASSWORD']
DB_NAME = os.environ['DB_NAME']
DB_HOST = os.environ['DB_HOST']
SECRET_KEY = os.environ['SECRET_KEY']

app = Flask (__name__)
CORS (app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://python:{}@{}:5432/{}'.format (PYTHON_PASSWORD,
                                                                                    DB_HOST,
                                                                                    DB_NAME.lower ())
app.config['SECRET_KEY'] = SECRET_KEY
db = SQLAlchemy (app)

MIN_LENGTH = 4
MAX_LENGTH = 250
PUBLIC_WALLET_LENGTH = 56

messages = {
	200: 'OK',
	400: 'Bad Request'
}


def generate_status_code(code):
	return messages[code], code


class Applications (db.Model):
	id = db.Column (db.String (4), primary_key=True)
	email = db.Column (db.String (MAX_LENGTH), unique=True, nullable=True)
	name = db.Column (db.String (MAX_LENGTH), nullable=True)
	app_name = db.Column (db.String (MAX_LENGTH), nullable=True)
	public_wallet = db.Column (db.String (PUBLIC_WALLET_LENGTH), unique=True, nullable=True)

	def __repr__(self):
		return '<Application_data %r>' % self.id


class RegistrationForm (Form):
	public_address_pattern = r'G([A-Z0-9]{55})'
	email = StringField ('email', validators=[DataRequired (), Email ()])
	name = StringField ('name', validators=[DataRequired (), validators.length (min=MIN_LENGTH, max=MAX_LENGTH)])
	app_name = StringField ('app name',
	                        validators=[DataRequired (), validators.length (min=MIN_LENGTH, max=MAX_LENGTH)])
	public_wallet = StringField ('public wallet',
	                             validators=[DataRequired (),
	                                         validators.length (min=PUBLIC_WALLET_LENGTH, max=PUBLIC_WALLET_LENGTH),
	                                         validators.regexp (regex=public_address_pattern)])


class DeletionForm (Form):
	id_pattern = r'([a-zA-Z0-9]{4})'
	app_id = StringField ('app_id', validators=[DataRequired (), validators.regexp (regex=id_pattern)])


def generate_id():
	length = 4
	id = ''.join (
		secrets.choice (string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range (length))
	return id if not id == 'anon' else generate_id ()  # anon is reserved app id, recursion till id is not anon


@app.route ('/register', methods=['POST'])
def register():
	form = RegistrationForm (request.args)
	if not form.validate ():
		return generate_status_code (status.HTTP_400_BAD_REQUEST)
	app_id = generate_id ()
	while db.session.query (Applications.id).filter_by (id=app_id).scalar () is not None:
		app_id = generate_id ()
	app_data = Applications (id=app_id,
	                         email=form.email.data,
	                         name=form.name.data,
	                         app_name=form.app_name.data,
	                         public_wallet=form.public_wallet.data)
	try:
		db.session.add (app_data)
		db.session.commit ()
		return app_id
	except IntegrityError:
		db.session.rollback ()
		return generate_status_code (status.HTTP_400_BAD_REQUEST)


@app.route ('/remove', methods=['DELETE'])
def remove():
	form = DeletionForm (request.args)
	if not form.validate ():
		return generate_status_code (status.HTTP_400_BAD_REQUEST)

	app_data = db.session.query (Applications).filter_by (id=form.app_id.data).scalar ()
	if app_data is not None:
		try:
			db.session.delete (app_data)
			db.session.commit ()
			return generate_status_code (status.HTTP_200_OK)
		except IntegrityError:
			db.session.rollback ()
			return generate_status_code (status.HTTP_400_BAD_REQUEST)
	else:
		return generate_status_code (status.HTTP_400_BAD_REQUEST)


if __name__ == "__main__":
	db.create_all ()
	app.run ()
