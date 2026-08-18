FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY word_duel/ word_duel/

EXPOSE 8080
CMD ["python", "bot.py"]
