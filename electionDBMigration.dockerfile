FROM python:3

RUN mkdir -p /opt/src/election
WORKDIR /opt/src/election

COPY election/migrate.py ./migrate.py
COPY election/configuration.py ./configuration.py
COPY election/models.py ./models.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/election"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./migrate.py"]