import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ── Chargement du fichier .env (sans dépendance externe) ──────────────────────
def _load_dotenv(path: Path) -> None:
    """Charge les variables d'un fichier .env dans os.environ (setdefault)."""
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


_load_dotenv(BASE_DIR / ".env")
# ──────────────────────────────────────────────────────────────────────────────


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-8-+mm$qw&1!uy*y0v!80gco0pw__t!xay2g4l%fz+xi-6yw7z0",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = []

# ── MonCash ───────────────────────────────────────────────────────────────────
MONCASH = {
    "CLIENT_ID":   os.environ.get("MONCASH_CLIENT_ID", ""),
    "SECRET_KEY":  os.environ.get("MONCASH_SECRET_KEY", ""),
    "ENVIRONMENT": os.environ.get("MONCASH_ENVIRONMENT", "sandbox"),
}
# ──────────────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ckeditor_5",
    "django_moncash",
    "shop",
    "dashboard",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.site_settings",
                "shop.context_processors.cart_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "mat_store_ecommerce.db",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "accounts.customer"

# ── CKEditor 5 ────────────────────────────────────────────────────────────────
CKEDITOR_5_UPLOAD_PATH = "ckeditor_uploads/"
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "strikethrough", "|",
            "bulletedList", "numberedList", "blockQuote", "|",
            "link", "insertImage", "insertTable", "|",
            "fontSize", "fontColor", "fontBackgroundColor", "|",
            "outdent", "indent", "alignment", "|",
            "undo", "redo",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "imageStyle:inline",
                "imageStyle:block",
                "imageStyle:side",
            ],
        },
        "height": "300px",
        "width": "100%",
    },
}
