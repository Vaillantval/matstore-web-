FROM python:3.13-slim

# Empêche Python d'écrire des .pyc et bufferise stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

# Placeholder build-time (les vraies clés viennent des variables Railway)
ENV SECRET_KEY=build-time-placeholder-key
ENV DEBUG=False

WORKDIR /app

# Dépendances système pour psycopg2 + Pillow
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Code source
COPY . /app/

# Fichiers statiques compilés dans l'image
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 2 --timeout 120"]