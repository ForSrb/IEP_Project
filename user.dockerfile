FROM python:3

RUN mkdir -p /opt/src/user
WORKDIR /opt/src/user

COPY election/user/application.py ./application.py
COPY election/user/userDecorator.py ./userDecorator.py
COPY election/user/configuration.py ./configuration.py
COPY election/user/models.py ./models.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/user"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./application.py"]