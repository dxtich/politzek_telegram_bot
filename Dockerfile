FROM python:3.11.4-alpine

ENV API_TOKEN='a:b'
RUN adduser -D bot
USER bot
WORKDIR /app
COPY --chown=bot requirements.txt bot.py /app/
RUN pip install -r requirements.txt
CMD python bot.py
