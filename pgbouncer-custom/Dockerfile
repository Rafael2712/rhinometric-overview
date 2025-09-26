FROM postgres:16-alpine
RUN apk add --no-cache pgbouncer
RUN adduser -D -s /bin/sh pgbouncer
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt
RUN chown -R pgbouncer:pgbouncer /etc/pgbouncer
USER pgbouncer
EXPOSE 6432
CMD ["pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
