FROM python:3.7-stretch

RUN mkdir -p /opt/app_id_registration

WORKDIR /opt/app_id_registration

COPY Pipfile* /opt/app_id_registration/

RUN pip install pipenv \
	&&  apt-get update && apt-get install -y libpq-dev \
	&&  pipenv install

COPY . .

EXPOSE 3000

CMD pipenv run python build_database.py && pipenv run gunicorn -w 4 -b 0.0.0.0:3000 main:app
