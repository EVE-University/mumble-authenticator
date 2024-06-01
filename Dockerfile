FROM python:3.11.9-slim-bookworm as base

ARG DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get install --no-install-recommends -y \
    libstdc++6 \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base as build
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    gettext \
    pkg-config \
    libmariadb-dev \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt ./requirements.txt

RUN python3 -m venv $VIRTUAL_ENV

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir wheel mysqlclient

RUN pip install --no-cache-dir  -r ./requirements.txt

RUN pip uninstall -y setuptools pip

RUN find -P "$VIRTUAL_ENV/lib" -type f -name "*.so" -exec strip -v --strip-unneeded {} \;

FROM base
ARG MUMBLE_AUTH_UID=1000
ARG MUMBLE_AUTH_GID=1000

RUN groupadd --gid ${MUMBLE_AUTH_GID} mumbleauth && useradd --uid ${MUMBLE_AUTH_UID} --gid ${MUMBLE_AUTH_GID} mumbleauth

COPY --from=build $VIRTUAL_ENV $VIRTUAL_ENV

COPY ./entrypoint.sh /entrypoint.sh
COPY ./slices ./slices
COPY ./authenticator.py ./authenticator.py
COPY ./healthcheck.py ./healthcheck.py

RUN touch authenticator.ini && chown mumbleauth:mumbleauth authenticator.ini && chmod 644 authenticator.ini

USER mumbleauth
ENTRYPOINT [ "/entrypoint.sh" ]