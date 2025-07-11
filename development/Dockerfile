
ARG NAUTOBOT_VER="2.4.10"

# Accepts a desired Python version as build argument, default to 3.11
ARG PYTHON_VER="3.11"

FROM ghcr.io/nautobot/nautobot-dev:${NAUTOBOT_VER}-py${PYTHON_VER}

# Runtime argument and environment setup
ARG NAUTOBOT_ROOT=/opt/nautobot

ENV prometheus_multiproc_dir=/prom_cache
ENV NAUTOBOT_ROOT=${NAUTOBOT_ROOT}
ENV INVOKE_NAUTOBOT_APP_VPN_LOCAL=true


RUN which poetry || curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false


# Copy in the source code
WORKDIR /source
COPY . /source

# Build args must be declared in each stage
ARG NAUTOBOT_VER
ARG PYTHON_VER


ARG CI
RUN if [ -z "${CI+x}" ]; then \
    INSTALLED_NAUTOBOT_VER=$(pip show nautobot | grep "^Version" | sed "s/Version: //"); \
    poetry add --lock nautobot@${INSTALLED_NAUTOBOT_VER} || \
    poetry add --lock git+https://github.com/nautobot/nautobot.git#${NAUTOBOT_VER}; fi


# Install the app
RUN poetry install --extras all --with dev

COPY development/nautobot_config.py ${NAUTOBOT_ROOT}/nautobot_config.py
