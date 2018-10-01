FROM b3vis/borgmatic

# Starting from an existing borgmatic image, install the local source on top of
# it so that we can test any local changes.
RUN adduser -h /home -D app
COPY test_requirements.txt /app/
RUN pip3 install --upgrade --requirement /app/test_requirements.txt
COPY . /app
RUN rm -fr /app/.tox /app/.git \
    && pip3 install --upgrade /app \
    && chown -R app /app

USER app
WORKDIR /app
ENV BORG_CACHE_DIR "/app/.cache/borg"

CMD ["py.test"]
