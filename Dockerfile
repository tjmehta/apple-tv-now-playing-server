FROM python:3.10.8

ADD . /
RUN pip install quart
RUN pip install pyatv

CMD [ "python", "./app.py" ]
