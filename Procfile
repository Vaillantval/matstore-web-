web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 4 --worker-class gthread --timeout 120
worker: celery -A config worker --loglevel=info --concurrency=2 --without-heartbeat
beat: celery -A config beat --loglevel=info
