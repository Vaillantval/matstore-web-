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
DEBUG = os.environ.get("DEBUG", "False") == "True"

_allowed = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]

# ── MonCash ───────────────────────────────────────────────────────────────────
MONCASH = {
    "CLIENT_ID": os.environ.get("MONCASH_CLIENT_ID", ""),
    "SECRET_KEY": os.environ.get("MONCASH_SECRET_KEY", ""),
    "ENVIRONMENT": os.environ.get("MONCASH_ENVIRONMENT", "sandbox"),
}
# ── Stripe ────────────────────────────────────────────────────────────────────
STRIPE = {
    "TEST_PUBLIC_KEY": os.environ.get("STRIPE_TEST_PUBLIC_KEY", ""),
    "TEST_SECRET_KEY": os.environ.get("STRIPE_TEST_SECRET_KEY", ""),
    "LIVE_PUBLIC_KEY": os.environ.get("STRIPE_LIVE_PUBLIC_KEY", ""),
    "LIVE_SECRET_KEY": os.environ.get("STRIPE_LIVE_SECRET_KEY", ""),
    "WEBHOOK_SECRET": os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
}
# ──────────────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "jazzmin",  # ← doit être AVANT django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ckeditor_5",
    "shop",
    "dashboard",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ← static files en prod
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

# Base de données : PostgreSQL en prod (DATABASE_URL injecté par Railway),
# SQLite en local si DATABASE_URL absent.
import dj_database_url

_DATABASE_URL = os.environ.get("DATABASE_URL")

if _DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(default=_DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "mat_store_ecommerce.db",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # dossier collectstatic
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Sécurité HTTPS (activée uniquement hors DEBUG) ────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    X_FRAME_OPTIONS = "DENY"

AUTH_USER_MODEL = "accounts.customer"

# ── CKEditor 5 ────────────────────────────────────────────────────────────────
CKEDITOR_5_UPLOAD_PATH = "ckeditor_uploads/"
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "|",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "|",
            "link",
            "insertImage",
            "insertTable",
            "|",
            "fontSize",
            "fontColor",
            "fontBackgroundColor",
            "|",
            "outdent",
            "indent",
            "alignment",
            "|",
            "undo",
            "redo",
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

# ── Jazzmin — Admin UI ────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    # ── CSS custom ────────────────────────────────────────────────────────────
    "custom_css": "assets/css/admin_matstore.css",
    # ── Branding ──────────────────────────────────────────────────────────────
    "site_title": "matstore Admin",
    "site_header": "matstore",
    "site_brand": "matstore",
    "welcome_sign": "Bienvenue sur le back-office matstore",
    "copyright": "matstore © 2026",
    # Icône onglet navigateur (favicon) — utilise le logo du site si dispo,
    # sinon Bootstrap Icons intégrées à Jazzmin (aucun fichier requis)
    "site_icon": None,
    "site_logo": None,  # ex: "assets/img/logo.png" si tu en as un
    "site_logo_classes": "img-circle",
    # ── Recherche globale ──────────────────────────────────────────────────────
    "search_model": ["shop.Product", "shop.Order", "accounts.Customer"],
    # ── Liens utiles (top bar) ────────────────────────────────────────────────
    "topmenu_links": [
        {"name": "Boutique", "url": "/", "new_window": True},
        {"name": "Produits", "url": "admin:shop_product_changelist"},
        {"name": "Commandes", "url": "admin:shop_order_changelist"},
        {"model": "accounts.Customer"},
    ],
    # ── User menu (coin haut-droit) ───────────────────────────────────────────
    "usermenu_links": [
        {
            "name": "Voir la boutique",
            "url": "/",
            "new_window": True,
            "icon": "fas fa-store",
        },
        {"model": "accounts.Customer"},
    ],
    # ── Navigation latérale ───────────────────────────────────────────────────
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    # Ordre & groupement des apps dans la sidebar
    "order_with_respect_to": [
        "shop",
        "shop.Order",
        "shop.OrderDetail",
        "shop.Product",
        "shop.Category",
        "shop.Collection",
        "shop.Carrier",
        "shop.Method",
        "shop.Setting",
        "shop.ExchangeRate",
        "shop.Slider",
        "shop.Page",
        "shop.FAQ",
        "shop.ContactMessage",
        "dashboard",
        "dashboard.Adress",
        "accounts",
        "accounts.Customer",
        "auth",
    ],
    # Groupes personnalisés dans la sidebar (sections avec titres)
    "custom_links": {
        "shop": [
            {
                "name": "Voir la boutique",
                "url": "/",
                "icon": "fas fa-external-link-alt",
                "permissions": ["shop.view_product"],
            },
        ],
    },
    # ── Icônes des modèles ────────────────────────────────────────────────────
    "icons": {
        # Apps
        "shop": "fas fa-store",
        "dashboard": "fas fa-tachometer-alt",
        "accounts": "fas fa-users",
        "auth": "fas fa-shield-alt",
        # Modèles shop
        "shop.order": "fas fa-shopping-bag",
        "shop.orderdetail": "fas fa-list-alt",
        "shop.product": "fas fa-box",
        "shop.category": "fas fa-tags",
        "shop.collection": "fas fa-layer-group",
        "shop.carrier": "fas fa-truck",
        "shop.method": "fas fa-credit-card",
        "shop.setting": "fas fa-cogs",
        "shop.exchangerate": "fas fa-exchange-alt",
        "shop.slider": "fas fa-images",
        "shop.page": "fas fa-file-alt",
        "shop.faq": "fas fa-question-circle",
        "shop.contactmessage": "fas fa-envelope",
        # Modèles dashboard
        "dashboard.adress": "fas fa-map-marker-alt",
        # Modèles accounts
        "accounts.customer": "fas fa-user-circle",
        # Auth
        "auth.group": "fas fa-users-cog",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    # ── Comportement des listes ───────────────────────────────────────────────
    "list_filter_dropdown": True,  # filtres en dropdown plutôt qu'en liste
    "related_modal_active": True,  # ouvre les FK dans une modale
    "show_ui_builder": False,  # désactiver en prod
    # ── Personnalisation des formulaires ──────────────────────────────────────
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    # ── Language ──────────────────────────────────────────────────────────────
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-warning",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    # Thème clair épuré comme base
    "theme": "flatly",
    "default_theme_mode": "light",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-outline-success",
    },
}
# ──────────────────────────────────────────────────────────────────────────────
