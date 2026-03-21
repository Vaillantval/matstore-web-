import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from django.utils.translation import gettext_lazy as _

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SÉCURITÉ & DEBUG ---
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-default-change-me")

# --- GESTION DES HÔTES  ---
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "healthcheck.railway.app"]

# Récupération automatique du domaine Railway
_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
if _railway_domain:
    ALLOWED_HOSTS.append(_railway_domain)

# Ajout des domaines personnalisés depuis les variables d'environnement
_extra_hosts = os.environ.get("ALLOWED_HOSTS", "")
if _extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in _extra_hosts.split(",") if h.strip()]

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    "jazzmin",  # Avant l'admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_ckeditor_5",
    "crispy_forms",
    "crispy_bootstrap4",
    "accounts",
    "shop",
    "dashboard",
    "anymail",
    "emails",
    # API
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "api",
]
# --- CONFIGURATION DU SITE ID ---
SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Pour les fichiers statiques
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
                "django.template.context_processors.debug",
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

# --- BASE DE DONNÉES (VERSION ROBUSTE) ---
_DATABASE_URL = os.environ.get("DATABASE_URL")

if _DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=_DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,  # SSL requis uniquement en production
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- FICHIERS STATIQUES & WHITENOISE ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Utilisation d'un stockage plus tolérant pour éviter les crashs au boot
if DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }

# --- SÉCURITÉ PROXY & HTTPS (IMPORTÉ DE KOULAKAY) ---
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = False  # Railway gère le SSL, Django ne doit pas rediriger
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# --- CSRF TRUSTED ORIGINS ---
CSRF_TRUSTED_ORIGINS = ["http://localhost", "http://127.0.0.1"]
if _railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_domain}")
_extra_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _extra_origins:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_origins.split(",") if o.strip()]

# --- AUTHENTICATION ---
AUTH_USER_MODEL = (
    "accounts.Customer"  # Vérifie que 'Customer' a bien une majuscule dans ton code
)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = "fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- MEDIA ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- CONFIGURATIONS TIERCES (MONCASH, STRIPE, ETC.) ---
MONCASH = {
    "CLIENT_ID": os.environ.get("MONCASH_CLIENT_ID", ""),
    "SECRET_KEY": os.environ.get("MONCASH_SECRET_KEY", ""),
    "ENVIRONMENT": os.environ.get("MONCASH_ENVIRONMENT", "sandbox"),
}

STRIPE = {
    "PUBLIC_KEY": os.environ.get("STRIPE_PUBLIC_KEY", ""),
    "SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY", ""),
    "WEBHOOK_SECRET": os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
}

# Jazzmin settings... (tu peux garder tes réglages JAZZMIN_SETTINGS actuels ici)

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

# --- EMAIL ---
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "anymail.backends.mailjet.EmailBackend"

ANYMAIL = {
    "MAILJET_API_KEY": os.environ.get("MAILJET_API_KEY", ""),
    "MAILJET_SECRET_KEY": os.environ.get("MAILJET_SECRET_KEY", ""),
}

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "MatStore Haiti <info@matstorehaiti.online>"
)
ADMINS_NOTIFY = os.environ.get("ADMINS_NOTIFY", "info@matstorehaiti.online")
SITE_URL = os.environ.get("SITE_URL", "https://matstorehaiti.online")

# --- DJANGO REST FRAMEWORK ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "api.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "api.exceptions.custom_exception_handler",
}

# --- SIMPLE JWT ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_ACCESS_TOKEN_LIFETIME_DAYS", 1))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 30))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- CORS ---
_cors_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = (
    [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    if _cors_origins_env
    else ["http://localhost:3000", "http://localhost:8080"]
)
CORS_ALLOW_CREDENTIALS = True

# --- DRF SPECTACULAR (OpenAPI docs) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "MatStore Haiti API",
    "DESCRIPTION": "API REST pour l'application mobile et le back office MatStore Haiti.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}
