FROM node:16.16.0-buster as pixlet-node

# Clone pixlet
RUN git clone https://github.com/tidbyt/pixlet

# Build node parts
WORKDIR /pixlet
RUN npm install
RUN npm run build

##############################################################
##############################################################
##############################################################

FROM golang:1.19-buster as pixlet-golang

# Install libwebp
RUN apt-get update && apt-get install libwebp-dev -y

# Copy pixlet
COPY --from=pixlet-node /pixlet /pixlet

# Continue build
WORKDIR /pixlet
RUN make build

##############################################################
##############################################################
##############################################################

FROM python:3.10-buster

RUN pip install quart
RUN pip install pyatv
RUN pip install tzlocal

# # Move the binary into your path.
COPY --from=pixlet-golang /pixlet/pixlet /usr/local/bin/pixlet

# Add apple-tv-now-playing
ADD . /

CMD [ "python", "./app.py" ]
