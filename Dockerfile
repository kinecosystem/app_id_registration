FROM python:3.7-alpine

RUN mkdir -p /opt/app_id_registration

WORKDIR /opt/app_id_registration

COPY . .

RUN pip install pipenv \
	&&  apk add -qU --no-cache -t .build-deps gcc musl-dev git postgresql-dev \
	&&  pipenv install

CMD pipenv run python build_database.py && pipenv run python main.py
