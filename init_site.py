# init_site.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.sites.models import Site


def setup_site():
    Site.objects.get_or_create(
        id=1, defaults={"domain": "matstorehaiti.online", "name": "matstore"}
    )


if __name__ == "__main__":
    setup_site()
