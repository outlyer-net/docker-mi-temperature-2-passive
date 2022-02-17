# Build-only intermediate image
FROM debian:buster-slim AS stage0

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
# NOTE: This doesn't appear to be the case anymore
#ENV LANG C.UTF-8

# Install Debian-provided python packages instead of using pip, will
#  reduce build time considerably
# Otherwise: pip install requests pybluez pycryptodomex bluepy paho-mqtt
RUN apt-get update \
	&& apt-get -y --no-install-recommends install \
		build-essential \
		libbluetooth-dev \
		libglib2.0-dev \
		python3-pip

# Wheel is required for bluepy to build properly. *MUST* run as separate calls to pip install
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install bluepy

FROM debian:buster-slim

LABEL maintainer="Toni Corvera <outlyer@gmail.com>" \
      org.opencontainers.image.name="MiTemperature2 (Passive Mode)" \
      org.opencontainers.image.description="Passive scanning of BLE-enabled Mijia V2 thermometers" \
      org.opencontainers.image.url="https://hub.docker.com/repository/docker/outlyernet/mi-temperature-2" \
      org.opencontainers.image.source="https://github.com/outlyer-net/docker-mi-temperature-2-passive"

# Install Debian-provided python packages instead of using pip, will
#  reduce build time considerably
# Otherwise: pip install requests pybluez pycryptodomex bluepy paho-mqtt
RUN apt-get update \
	&& apt-get -y --no-install-recommends install \
		libcap2-bin \
		python3-bluez \
		python3-paho-mqtt \
		python3-pip \
		python3-pycryptodome \
		python3-requests \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# /usr/local/lib will only contain the packages installed by pip
COPY --from=stage0 /usr/local/lib/ /usr/local/lib/

COPY ./*.py /app/
COPY ./docker/entrypoint.sh /
# Sample configurations
COPY ./mqtt.conf.dist ./sensors.ini.dist /conf/

ENTRYPOINT /entrypoint.sh

# start the created image with sudo docker run --net=host --cap-add NET_RAW --cap-add NET_ADMIN -t your_image_name /bin/bash
