FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY credentials.json* ./
COPY token.json* ./

RUN chmod +x generate_and_sync.py

ENTRYPOINT ["python", "generate_and_sync.py"]
CMD ["2026"]