FROM python:3-alpine

ENV API_TOKEN='a:b'
RUN adduser -D bot && \
    apk update && apk upgrade && \
    apk add --no-cache gcc musl-dev
USER bot
WORKDIR /app
COPY --chown=bot requirements.txt bot.py /app/
RUN pip install --upgrade --no-cache-dir --prefer-binary pip setuptools wheel && pip install --no-cache-dir --prefer-binary -r requirements.txt
CMD python bot.py
