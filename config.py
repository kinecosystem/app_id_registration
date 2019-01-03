import os

# Get constants from env variables
PYTHON_PASSWORD = os.environ.get('PYTHON_PASSWORD', '1234')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '11111')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_ROLE = os.environ.get('DB_ROLE', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'applications_db')
API_KEY = os.environ.get('API_KEY', 'One Ring To Rule Them All')

STATSD_HOST = os.environ.get('STATSD_HOST', 'localhost')
STATSD_PORT = int(os.environ.get('STATSD_PORT', 8125))
