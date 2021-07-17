FROM python:3

RUN mkdir -p /opt/src/dameon
WORKDIR /opt/src/dameon

COPY election/dameon/application.py ./application.py
COPY election/dameon/configuration.py ./configuration.py
COPY election/dameon/models.py ./models.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/dameon"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./application.py"]