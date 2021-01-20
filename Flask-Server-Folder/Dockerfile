FROM python:2

WORKDIR '/app/flask-server'

COPY ./requirements.txt ./

RUN pip install -r ./requirements.txt

COPY . .

CMD python ./app.py
