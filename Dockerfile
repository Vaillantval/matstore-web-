FROM python:3.13-slim

# Empêche Python de générer des fichiers .pyc et assure un affichage direct des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Installation des dépendances système (Postgres, Pillow, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie du projet
COPY . /app/

# Collecte des fichiers statiques pour WhiteNoise
RUN python manage.py collectstatic --noinput

# Railway injecte dynamiquement le port, EXPOSE est ici indicatif
EXPOSE 8080

# --- LE CHANGEMENT CRUCIAL ICI ---
# On utilise ["sh", "-c", "..."] pour que la variable $PORT soit bien interprétée par le système
# CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120"]