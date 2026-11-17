# Flask + web3.py app for the Lost and Found Registry (used by docker-compose.yml).
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import solcx; solcx.install_solc('0.8.24')"

COPY . .

ENV HOST=0.0.0.0 \
    PORT=5000 \
    PYTHONUNBUFFERED=1
EXPOSE 5000

CMD ["python", "app.py"]
