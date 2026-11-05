FROM python:3.12-alpine

# tzdata нужен для корректного времени в сообщениях (Europe/Minsk).
RUN apk add --no-cache tzdata

WORKDIR /app
COPY monitor.py /app/monitor.py

USER nobody
CMD ["python", "-u", "/app/monitor.py"]
