FROM python:alpine3.12

RUN pip3 install mysql-connector-python
RUN mkdir /app
COPY syslogserver.py /app/syslogserver.py


CMD [ "python3", "/app/syslogserver.py" ]