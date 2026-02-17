FROM python:3.11-slim

WORKDIR /app
COPY app ./app
COPY requirements.txt ./requirements.txt

EXPOSE 8000
CMD ["python", "app/main.py"]
