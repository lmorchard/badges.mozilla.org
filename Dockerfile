FROM debian:wheezy
RUN apt-get update && apt-get install -y python python-pip python-dev libpq-dev \
    libxml2-dev libxslt-dev mysql-client libmysqlclient-dev gettext libjpeg8 \
    libjpeg62-dev libfreetype6 libfreetype6-dev

# Using PIL or Pillow? You probably want to uncomment next line
# RUN apt-get update && apt-get install -y libjpeg8-dev

WORKDIR /app

# First copy requirements.txt and peep so we can take advantage of
# docker caching.
COPY requirements/dev.txt /app/requirements/dev.txt
COPY requirements/prod.txt /app/requirements/prod.txt
COPY ./scripts/peep.py /app/scripts/peep.py
RUN ./scripts/peep.py install -r requirements/dev.txt

COPY . /app

EXPOSE 80

CMD ["./bin/run-docker.sh"]
