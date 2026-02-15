FROM python:3.11-slim

WORKDIR /app

COPY aws_report.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "aws_report.py"]
