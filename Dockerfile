FROM python:latest

LABEL maintainer Stuart B. Wilkins
COPY . .
RUN pip3 install -r requirements.txt
RUN python setup.py install

CMD horizon_exporter
