FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY election/admin/application.py ./application.py
COPY election/admin/adminDecorator.py ./adminDecorator.py
COPY election/admin/configuration.py ./configuration.py
COPY election/admin/models.py ./models.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/admin"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./application.py"]