FROM python:3.7-alpine

RUN mkdir -p /opt/app_id_registration

WORKDIR /opt/app_id_registration

COPY . .

RUN pip install pipenv \
	&&  apk add -qU --no-cache -t .build-deps gcc musl-dev git postgresql-dev \
	&&  pipenv install

EXPOSE 3000

CMD pipenv run python build_database.py && pipenv run gunicorn -w 4 -b 0.0.0.0:3000 main:app
