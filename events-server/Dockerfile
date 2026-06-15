FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir "poetry==2.4.1" \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

COPY . .

EXPOSE 8080
ENV SERVER_PORT=8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "server:app"]
