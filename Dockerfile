FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    libmariadb-dev g++ git pkg-config libbz2-dev

# Install python dependencies
RUN pip install --upgrade pip
RUN pip install wheel
RUN pip install bcrypt passlib zeroc-ice mysqlclient

ENTRYPOINT ["sh", "-c"]