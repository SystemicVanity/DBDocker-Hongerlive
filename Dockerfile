FROM python:3-slim

RUN apt update && mkdir -p /app && mkdir -p /arcalive
RUN pip install --quiet --upgrade pip
RUN pip install --quiet requests beautifulsoup4

COPY hongerlive.py /app/hongerlive.py

CMD ["python3", "/app/hongerlive.py", "DB_NAME", "SLUG_ID"]