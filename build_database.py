"""Script to build a database for main.py to write data to."""

import os
import psycopg2
import logging


# Get constants from env variables
PYTHON_PASSWORD = os.environ['PYTHON_PASSWORD']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
DB_NAME = os.environ['DB_NAME']
DB_HOST = os.environ['DB_HOST']


def setup_postgres(database=''):
	"""Set up a connection to the postgres database."""
	conn = psycopg2.connect("postgresql://postgres:{}@{}:5432".format(POSTGRES_PASSWORD, DB_HOST) + database)
	conn.autocommit = True
	cur = conn.cursor()
	return cur


def main():
	"""Main entry point."""
	logging.basicConfig(level='INFO', format='%(asctime)s | %(levelname)s | %(message)s')
	# Check if the database already exists
	try:
		setup_postgres(database='/' + DB_NAME.lower())
	except psycopg2.OperationalError as e:
		if 'does not exist' in str(e):
			pass
		else:
			raise
	else:
			logging.info('Using existing database instead of creating a new one')
			quit(0)

	# Connect to the postgres database
	try:
		cur = setup_postgres()

		# Create the database
		cur.execute('CREATE DATABASE {};'.format(DB_NAME.lower()))

		# Create the users
		cur.execute('CREATE USER python;')
		cur.execute("ALTER USER python WITH PASSWORD '{}'".format(PYTHON_PASSWORD))
		cur.execute('GRANT ALL PRIVILEGES ON DATABASE {} TO python'.format(DB_NAME).lower())
		logging.info('Database created successfully.')

	except:
		logging.error('Could not fully create database, please delete all data before retrying.')
		raise


if __name__ == '__main__':
	main()