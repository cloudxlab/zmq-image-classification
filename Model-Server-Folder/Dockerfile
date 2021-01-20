FROM python:2

WORKDIR '/app/model-server'

COPY . .

RUN pip install -r ./requirements.txt

CMD python ./resnet_model_server.py
