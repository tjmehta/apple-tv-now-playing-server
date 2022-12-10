FROM python:3.10.8

RUN pip install quart
RUN pip install pyatv
RUN pip install tzlocal

# Download the archive.
RUN curl -LO https://github.com/tidbyt/pixlet/releases/download/v0.22.8/pixlet_0.22.8_linux_amd64.tar.gz
# Unpack the archive.
RUN tar -xvf pixlet_0.22.8_linux_amd64.tar.gz
# Ensure the binary is executable.
RUN chmod +x ./pixlet
# Move the binary into your path.
RUN mv pixlet /usr/local/bin/pixlet

ADD . /

CMD [ "python", "./app.py" ]
