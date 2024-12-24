FROM python:3.12-slim

COPY . /app

COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

WORKDIR /app

CMD ["sh", "-c", "python main.py"]