import os
from pathlib import Path
from urllib.parse import quote

import dj_database_url
import environ
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(BASE_DIR / ".env")

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-change-me")
DEBUG = env("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "web"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "rest_framework_simplejwt",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.properties",
    "apps.guarantees",
    "apps.crops",
    "apps.billing",
    "apps.masterdata",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


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
            ],
        },
    },
]

def _build_database_url_from_parts():
    """Monta postgres:// com user/senha/nome do DB codificados (evita ParseError com [ ] ; @ etc.)."""
    user = env("POSTGRES_USER", default="garantias")
    password = env("POSTGRES_PASSWORD", default="garantias")
    host = env("POSTGRES_HOST", default="db")
    port = env("POSTGRES_PORT", default="5432")
    name = env("POSTGRES_DB", default="garantias")

    def enc(part):
        return quote(str(part), safe="")

    return f"postgres://{enc(user)}:{enc(password)}@{host}:{port}/{enc(name)}"


def _resolve_database():
    raw = os.environ.get("DATABASE_URL")
    if raw is not None:
        raw = raw.strip().strip('"').strip("'")
    else:
        raw = ""

    built = _build_database_url_from_parts()
    # Senha definida no mesmo .env que o serviço `db` → usar URL montada primeiro.
    # Evita: DATABASE_URL sintaticamente válida com senha antiga/errada “ganhar” do POSTGRES_PASSWORD.
    pwd_from_env = (os.environ.get("POSTGRES_PASSWORD") or "").strip()
    if pwd_from_env:
        candidates = [built]
        if raw:
            candidates.append(raw)
    else:
        candidates = []
        if raw:
            candidates.append(raw)
        candidates.append(built)

    candidates.append("postgres://garantias:garantias@db:5432/garantias")

    last_err = None
    for url in candidates:
        try:
            cfg = dj_database_url.parse(url)
            cfg["ENGINE"] = "django.contrib.gis.db.backends.postgis"
            return cfg
        except dj_database_url.ParseError as e:
            last_err = e
            continue

    raise ImproperlyConfigured(
        "Não foi possível interpretar DATABASE_URL. Use senha codificada na URL (ex.: @ → %40) "
        "ou defina POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST e POSTGRES_PORT."
    ) from last_err


DATABASES = {"default": _resolve_database()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:8000", "http://127.0.0.1:8000"],
)
CORS_ALLOW_CREDENTIALS = True

# Mapa (MVP: leaflet)
MAP_PROVIDER = env.str("MAP_PROVIDER", default="leaflet")

# Tiles do mapa (recomendado: usar provedor com termos adequados para SaaS).
# Padrão em dev: ESRI World Imagery (satélite) com atribuição.
MAP_TILE_URL = env.str(
    "MAP_TILE_URL",
    default="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
)
MAP_TILE_ATTRIBUTION = env.str(
    "MAP_TILE_ATTRIBUTION",
    default="Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
)
MAP_TILE_MAX_ZOOM = env.int("MAP_TILE_MAX_ZOOM", default=19)

# Mapa “rua” / predefinição (estilo similar ao Google Maps padrão).
MAP_ROAD_TILE_URL = env.str(
    "MAP_ROAD_TILE_URL",
    default="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
)
MAP_ROAD_TILE_ATTRIBUTION = env.str(
    "MAP_ROAD_TILE_ATTRIBUTION",
    default="Tiles &copy; Esri — Esri, HERE, Garmin, USGS, METI/NASA, EPA",
)

# Overlay de labels (cidades/rodovias) para modo híbrido.
MAP_LABELS_TILE_URL = env.str(
    "MAP_LABELS_TILE_URL",
    default="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
)
MAP_LABELS_ATTRIBUTION = env.str(
    "MAP_LABELS_ATTRIBUTION",
    default="&copy; Esri",
)
MAP_LABELS_OPACITY = env.float("MAP_LABELS_OPACITY", default=1.0)

LOGIN_URL = "/accounts/login/"
# Após login, retornar para a landing para conduzir ao pricing/onboarding.
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

if DEBUG:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }

# OAuth (Google / Microsoft Entra): preparar com django-allauth ou social-auth-app-django quando houver credenciais.
# Ex.: SOCIAL_AUTH_GOOGLE_OAUTH2_KEY / SECRET, AZURE_AD_* — ver rota stub /oauth/
