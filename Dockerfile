FROM alpine:3.13.5

# Install python
RUN    apk update && apk upgrade \
    && apk add python3 \
    && apk add py3-pip \
    && python3 -m pip install --upgrade pip

RUN pip install rethinkdb \
    && pip install b2sdk

# Clean up temp files
RUN rm -rf /var/cache/apk/*

# Copy backup scripts
COPY ./scripts/backup.py /backup_script/backup.py
COPY ./scripts/run.sh /run.sh

# Install python deps
WORKDIR /backup_script

CMD ["/run.sh"]