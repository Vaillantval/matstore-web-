FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV SECRET_KEY=build-time-placeholder-key
ENV DEBUG=False
ENV APP_PORT=8080
ENV HEALTH_CHECK_PORT=8081

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8080 8081

CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${APP_PORT} --workers 2 --timeout 120"]