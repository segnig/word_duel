FROM python:3.12-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --retries 15 --timeout 120 -r requirements.txt

COPY bot.py .
COPY word_duel/ word_duel/

EXPOSE 8080
CMD ["python", "bot.py"]
