import string
import secrets
import logging
from json import JSONDecodeError

from flask import Flask, request, abort, json
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}:5432/{}'.format(config.DB_ROLE,
                                                                               config.DB_PASSWORD,
                                                                               config.DB_HOST,
                                                                               config.DB_NAME.lower())
app.config['APP_ID'] = config.API_KEY
db = SQLAlchemy(app)

APP_ID_LENGTH = 4
MIN_LENGTH = 2
MAX_LENGTH = 250
PUBLIC_WALLET_LENGTH = 56
APP_ID_PATTERN = r'([a-zA-Z0-9]{4})'
PUBLIC_ADDRESS_PATTERN = r'G([A-Z0-9]{55})'

messages = {
	200: 'OK',
	400: 'Bad Request',
	401: 'Unauthorized'
}

logging.basicConfig(level='INFO', format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('app-id-registration')


class Applications(db.Model):
	id = db.Column(db.String(APP_ID_LENGTH), primary_key=True)
	email = db.Column(db.String(MAX_LENGTH),nullable=False) # mandatory
	name = db.Column(db.String(MAX_LENGTH), nullable=False) # mandatory
	app_name = db.Column(db.String(MAX_LENGTH), nullable=False) # mandatory
	public_wallet = db.Column(db.String(PUBLIC_WALLET_LENGTH), nullable=True)

	def __repr__(self):
		return '<Applications %r>' % self.id

class BaseForm(Form):
	app_id = StringField('app_id', validators=[DataRequired(), validators.regexp(regex=APP_ID_PATTERN)])
	email = StringField('email', validators=[validators.optional(), Email()])
	public_wallet = StringField('public_wallet',
	                            validators=[validators.optional(),
	                                        validators.length(min=PUBLIC_WALLET_LENGTH, max=PUBLIC_WALLET_LENGTH),
	                                        validators.regexp(regex=PUBLIC_ADDRESS_PATTERN)])

	def validate(self):
		if not super().validate():
			return False
		if not self.email.data and not self.public_wallet.data:
			return False
		return True


class RegistrationForm(Form):
	email = StringField('email', validators=[DataRequired(), Email()])
	name = StringField('name', validators=[DataRequired(), validators.length(min=MIN_LENGTH, max=MAX_LENGTH)])
	app_name = StringField('app_name',
	                       validators=[DataRequired(), validators.length(min=MIN_LENGTH, max=MAX_LENGTH)])
	public_wallet = StringField('public_wallet',
	                            validators=[validators.optional(), validators.length(min=PUBLIC_WALLET_LENGTH, max=PUBLIC_WALLET_LENGTH),
	                                        validators.regexp(regex=PUBLIC_ADDRESS_PATTERN)])


class UpdateForm(BaseForm):
	name = StringField('name', validators=[validators.optional(), validators.length(min=MIN_LENGTH, max=MAX_LENGTH)])
	app_name = StringField('app_name',
	                       validators=[validators.optional(), validators.length(min=MIN_LENGTH, max=MAX_LENGTH)])


class GetAppIdForm(BaseForm):
	pass



class DeleteForm(BaseForm):
	pass


def require_app_key(view_function):
	@wraps(view_function)
	def decorated_function(*args, **kwargs):
		if request.headers.get('x-api-key') and request.headers.get('x-api-key') == config.API_KEY:
			return view_function(*args, **kwargs)
		else:
			return generate_status_code(status.HTTP_401_UNAUTHORIZED)
	return decorated_function


def generate_status_code(code):
	return messages[code], code


def validate_data(form, application):
	if application is None:
		return False

	if form.email.data != "" and form.public_wallet.data != "":
		if application.email == form.email.data and application.public_wallet == form.public_wallet.data:
			return True
	elif form.email.data != "":
		if application.email == form.email.data:
			return True
	elif form.public_wallet.data != "":
		if application.public_wallet == form.public_wallet.data:
			return True
	return False

def validate_update_data(form, application):
	if application is None:
		return False

	if form.email.data != "" and form.public_wallet.data != "":
		if application.email == form.email.data or application.public_wallet == form.public_wallet.data:
			return True
	return False


def query_by_app_id(app_id):
	return  db.session.query(Applications).filter_by(id=app_id).first()


def generate_id():
	length = 4
	app_id = ''.join(
			secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(length))
	return app_id if not app_id == 'anon' else generate_id()  # anon is reserved app id, recursion till id is not anon


def short_error(message, data=None):
	call_statsd(message, data)
	logger.error(f'{message} ; data: {data}')


def short_log(message, data=None):
	call_statsd(message, data)
	logger.info(f'{message} ; data: {data}')


def call_statsd(message, data=None):
	try:
		result = json.loads(data) if data is not None else {"app_id": ""}
	except JSONDecodeError:
		result = {"app_id": data}

	statsd.increment(message, tags=['app_id:%s' % result["app_id"]])

def init_data(app_id=None, email=None, name=None, app_name=None, public_wallet=None):
	data = vars()
	result = {}
	for k, v in data.items():
		if v is not None:
			result[k] = v
	return json.dumps(result)

@app.route('/health', methods=['GET'])
def health():
	short_log('health_check.success')
	return generate_status_code(status.HTTP_200_OK)


@app.route('/register', methods=['POST'])
@require_app_key
def register():
	form = RegistrationForm(request.args)
	if not form.validate():
		short_error('application_registered.not_validate')
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	app_id = generate_id()

	while query_by_app_id(app_id) is not None:
		app_id = generate_id()
	email = form.email.data
	application = Applications(id=app_id,
	                        email=email,
	                        name=form.name.data,
	                        app_name=form.app_name.data,
	                        public_wallet=form.public_wallet.data)
	try:
		db.session.add(application)
		db.session.commit()
		application = init_data(app_id, application.email, application.name, application.app_name,
		                     application.public_wallet)
		short_log('application_registered.success', application)
		return app_id
	except IntegrityError:
		db.session.rollback()
		short_log('application_registered.failed', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)


@app.route('/update', methods=['PATCH'])
@require_app_key
def update():
	form = UpdateForm(request.args)
	if not form.validate():
		short_error('application_update.not_validate')
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	app_id = form.app_id.data
	application = query_by_app_id(app_id)

	if application is None or not validate_update_data(form, application):
		short_error('application_update.not_found', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	if form.email.data != "": application.email = form.email.data
	if form.name.data != "": application.name = form.name.data
	if form.app_name.data != "": application.app_name = form.app_name.data
	if form.public_wallet.data != "": application.public_wallet = form.public_wallet.data

	try:
		db.session.commit()
		app_data = init_data(app_id, application.email, application.name, application.app_name, application.public_wallet)
		short_log('application_update.success', app_data)
		return app_id

	except IntegrityError:
		db.session.rollback()
		short_error('application_update.failed', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)


@app.route('/get_app', methods=['GET'])
@require_app_key
def get_app():
	form = GetAppIdForm(request.args)
	if not form.validate():
		short_error('application_retrieved.not_validate')
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	app_id = form.app_id.data;
	application = query_by_app_id(app_id)

	if application is None or not validate_data(form, application):
		short_error('application_retrieved.not_found', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	app_data = init_data(app_id, application.email, application.name, application.app_name, application.public_wallet)
	short_log('application_retrieved.success', app_data)
	return app_data


@app.route('/remove', methods=['DELETE'])
@require_app_key
def remove():
	form = DeleteForm(request.args)
	if not form.validate():
		short_error('application_deletion.not_validate')
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	app_id = form.app_id.data
	application = query_by_app_id(app_id)

	if application is None or not validate_data(form, application):
		short_error('application_deletion.not_found', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)

	try:
		db.session.delete(application)
		db.session.commit()
		app_data = init_data(app_id, application.email, application.name, application.app_name, application.public_wallet)
		short_log('application_deletion.success', app_data)
		return generate_status_code(status.HTTP_200_OK)
	except IntegrityError:
		db.session.rollback()
		short_error('application_deletion.failed', app_id)
		return generate_status_code(status.HTTP_400_BAD_REQUEST)


db.create_all()

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=3000)
