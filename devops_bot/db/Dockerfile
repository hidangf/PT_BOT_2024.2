FROM postgres:14-alpine

ENV POSTGRES_HOST_AUTH_METHOD=scram-sha-256

RUN mkdir -p /oracle/pg_data/archive
RUN mkdir -p /var/log/postgresql
RUN chown postgres:postgres /var/log/postgresql
RUN chmod -R 777 /oracle/pg_data
