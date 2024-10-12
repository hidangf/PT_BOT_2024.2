FROM postgres:14-alpine

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_HOST_AUTH_METHOD=password
RUN touch /usr/share/repl.sh
RUN echo "#!/bin/bash" >> /usr/share/repl.sh
RUN echo "if [ ! -f /var/lib/postgresql/.pgpass ]; then" >> /usr/share/repl.sh
RUN echo "       echo \$DB_REPL_HOST:\$DB_REPL_PORT:*:\$DB_REPL_USER:\$DB_REPL_PASSWORD >> /var/lib/postgresql/.pgpass" >> /usr/share/repl.sh
RUN echo "        chown postgres:postgres /var/lib/postgresql/.pgpass" >> /usr/share/repl.sh
RUN echo "        chmod 600 /var/lib/postgresql/.pgpass" >> /usr/share/repl.sh
RUN echo "fi" >> /usr/share/repl.sh
RUN echo "while true; do" >> /usr/share/repl.sh
RUN echo "        rm -rf /var/lib/postgresql/data/*" >> /usr/share/repl.sh
RUN echo "        su - postgres -c \"pg_basebackup -R -h \$DB_REPL_HOST -U \$DB_REPL_USER -D /var/lib/postgresql/data/ -P\"" >> /usr/share/repl.sh
RUN echo "        sleep 60" >> /usr/share/repl.sh
RUN echo "done" >> /usr/share/repl.sh

RUN chmod +x /usr/share/repl.sh

CMD ["/usr/share/repl.sh"]
