FROM python:latest

WORKDIR /app

VOLUME ["/app/data"]

COPY scraper.py /app
COPY requirements.txt /app

RUN pip install -r requirements.txt

CMD ["python", "-u" , "scraper.py"]