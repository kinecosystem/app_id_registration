"""Script to build a database for main.py to write data to."""

import psycopg2
import logging

import config


def setup_postgres(db_name=''):
	"""Set up a connection to the postgres database."""
	conn = psycopg2.connect(
		"postgresql://{}:{}@{}:5432".format(config.DB_ROLE, config.DB_PASSWORD, config.DB_HOST) + db_name)
	conn.autocommit = True
	cur = conn.cursor()
	return cur


def main():
	"""Main entry point."""
	logging.basicConfig(level='INFO', format='%(asctime)s | %(levelname)s | %(message)s')
	# Check if the database already exists
	try:
		setup_postgres(db_name='/' + config.DB_NAME.lower())
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
		cur.execute('CREATE DATABASE {};'.format(config.DB_NAME.lower()))

		# Create the users
		cur.execute('CREATE USER python;')
		cur.execute("ALTER USER python WITH PASSWORD '{}'".format(config.PYTHON_PASSWORD))
		cur.execute('GRANT ALL PRIVILEGES ON DATABASE {} TO python'.format(config.DB_NAME).lower())
		logging.info('Database created successfully.')

	except:
		logging.error('Could not fully create database, please delete all data before retrying.')
		raise


if __name__ == '__main__':
	main()
