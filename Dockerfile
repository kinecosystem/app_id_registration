FROM python:3.7-alpine3.8

RUN mkdir -p /opt/app_id_registration

WORKDIR /opt/app_id_registration

COPY Pipfile* /opt/app_id_registration/

RUN pip install pipenv \
	&&  apk add -qU --no-cache -t .build-deps gcc musl-dev git postgresql-dev \
	&&  pipenv install

COPY . .

EXPOSE 3000

CMD pipenv run python build_database.py && pipenv run gunicorn -w 4 -b 0.0.0.0:3000 main:app
