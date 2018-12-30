import string
import secrets

from flask import Flask, request, abort
from functools import wraps
from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from wtforms import Form, StringField, validators
from wtforms.validators import (DataRequired, Email)
from flask_cors import CORS
from datadog import DogStatsd

import config

statsd = DogStatsd(config.STATSD_HOST, config.STATSD_PORT, namespace='app-registration')

app = Flask(__name__)
app.API_KEY = config.API_KEY
CORS(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}:5432/{}'.format(config.POSTGRES_USER,
                                                                               config.DB_PASSWORD,
                                                                               config.DB_HOST,
                                                                               config.DB_NAME.lower())
app.config['APP_ID'] = config.API_KEY
db = SQLAlchemy(app)

MIN_LENGTH = 4
MAX_LENGTH = 250
PUBLIC_WALLET_LENGTH = 56

messages = {
	200: 'OK',
	400: 'Bad Request'
}


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == config.API_KEY:
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


def generate_status_code(code):
	return messages[code], code


class Applications(db.Model):
	id = db.Column(db.String(4), primary_key=True)
	email = db.Column(db.String(MAX_LENGTH), unique=True, nullable=True)
	name = db.Column(db.String(MAX_LENGTH), nullable=True)
	app_name = db.Column(db.String(MAX_LENGTH), nullable=True)
	public_wallet = db.Column(db.String(PUBLIC_WALLET_LENGTH), unique=True, nullable=True)

	def __repr__(self):
		return '<Applications %r>' % self.id


class RegistrationForm(Form):
	public_address_pattern = r'G([A-Z0-9]{55})'
	email = StringField('email', validators=[DataRequired(), Email()])
	name = StringField('name', validators=[DataRequired(), validators.length(min=MIN_LENGTH, max=MAX_LENGTH)])
	app_name = StringField('app name',
	                       validators=[DataRequired(), validators.length(min=MIN_LENGTH, max=MAX_LENGTH)])
	public_wallet = StringField('public wallet',
	                            validators=[DataRequired(),
	                                        validators.length(min=PUBLIC_WALLET_LENGTH, max=PUBLIC_WALLET_LENGTH),
	                                        validators.regexp(regex=public_address_pattern)])


class DeletionForm(Form):
	id_pattern = r'([a-zA-Z0-9]{4})'
	app_id = StringField('app_id', validators=[DataRequired(), validators.regexp(regex=id_pattern)])


def generate_id():
	length = 4
	app_id = ''.join(
			secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(length))
	return app_id if not app_id == 'anon' else generate_id()  # anon is reserved app id, recursion till id is not anon


@app.route('/health', methods=['GET'])
def health():
	return generate_status_code(status.HTTP_200_OK)


@app.route('/register', methods=['POST'])
@require_appkey
def register():
	form = RegistrationForm(request.args)
	if not form.validate():
		return generate_status_code(status.HTTP_400_BAD_REQUEST)
	app_id = generate_id()
	while db.session.query(Applications.id).filter_by(id=app_id).scalar() is not None:
		app_id = generate_id()
	email = form.email.data
	app_data = Applications(id=app_id,
	                        email=email,
	                        name=form.name.data,
	                        app_name=form.app_name.data,
	                        public_wallet=form.public_wallet.data)
	try:
		db.session.add(app_data)
		db.session.commit()
		statsd.increment('application_registered.success',
		                 tags=['app_id:%s' % app_id])
		app.logger.debug('application_registered.failed: (%d app_id)', app_id)
		return app_id
	except IntegrityError:
		db.session.rollback()
		statsd.increment('application_registered.failed',
		                 tags=['email:%s' % email])
		app.logger.error('application_registered.failed: (%d app_id)', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)


@app.route('/remove', methods=['DELETE'])
@require_appkey
def remove():
	form = DeletionForm(request.args)
	if not form.validate():
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	app_id = db.session.query(Applications).filter_by(id=form.app_id.data).scalar()
	if app_id is not None:
		try:
			db.session.delete(app_id)
			db.session.commit()
			statsd.increment('application_deletion.success',
			                 tags=['app_id:%s' % app_id])
			app.logger.debug('application_deletion.success: (%d app_id)', app_id)
			return generate_status_code(status.HTTP_200_OK)
		except IntegrityError:
			db.session.rollback()
			app.logger.error('application_deletion.failed: (%d app_id)', app_id)
			return generate_status_code(status.HTTP_400_BAD_REQUEST)
	else:
		return generate_status_code(status.HTTP_400_BAD_REQUEST)


if __name__ == "main":
	db.create_all()
