FROM python:3.11.7-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt install -y build-essential && \
    apt-get install -y ffmpeg

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r requirements.txt --verbose

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
