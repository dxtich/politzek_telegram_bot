FROM python:3-alpine

RUN apk update && apk upgrade && \
    apk add --no-cache gcc
ENV API_TOKEN='a:b'
#RUN useradd -U bot
RUN adduser -D bot
WORKDIR /app
COPY --chown=bot requirements.txt bot.py /app/
RUN pip install --upgrade --no-cache-dir --prefer-binary pip setuptools wheel && pip install --no-cache-dir --prefer-binary -r requirements.txt
USER bot
CMD python bot.py
