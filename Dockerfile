FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

COPY requirements/ requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt

COPY . .

RUN mkdir -p logs staticfiles media && \
    chown -R appuser:appuser /app

RUN chmod +x scripts/entrypoint.sh

USER appuser

ENTRYPOINT ["scripts/entrypoint.sh"]