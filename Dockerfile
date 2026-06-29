FROM python:3.11-slim

WORKDIR /app

RUN useradd -m appuser && mkdir -p data logs && chown appuser:appuser data logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

CMD ["python", "-m", "src.bot.main"]