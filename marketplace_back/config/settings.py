from pathlib import Path
import environ


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG') and not env.bool('VERCEL', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '.vercel.app'])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'aplicaciones.gestion_usuario',
    'aplicaciones.publicacion',
    'aplicaciones.reserva',
    'aplicaciones.reporte',
]

AUTH_USER_MODEL = 'gestion_usuario.Usuario'
AUTHENTICATION_BACKENDS = ['aplicaciones.gestion_usuario.autenticacion.AutenticacionCorreoOUsuario']

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': env.db('DATABASE_URL')
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'aplicaciones.gestion_usuario.validacion.ValidacionSimilitudContrasena'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'aplicaciones.gestion_usuario.validacion.ValidacionComplejidadContrasena'},
]


LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'


CORREO_USUARIO = env('CORREO_USUARIO', default='')
CORREO_CLAVE = env('CORREO_CLAVE', default='')

if CORREO_USUARIO and CORREO_CLAVE:
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {
                'host': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'username': CORREO_USUARIO,
                'password': CORREO_CLAVE,
                'timeout': 10,
            },
        },
    }
else:
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.console.EmailBackend',
        },
    }

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=CORREO_USUARIO or 'marketplace@localhost')
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173')
PASSWORD_RESET_TIMEOUT = 1800



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'aplicaciones.gestion_usuario.seguridad.SesionAutenticacion',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'aplicaciones.gestion_usuario.seguridad.CuentaHabilitada',
    ],
    'EXCEPTION_HANDLER': 'aplicaciones.gestion_usuario.seguridad.manejador_excepciones',
}

ORIGENES_FRONT = list(dict.fromkeys([
    'http://localhost:5173',
    'https://marketplace-alojamientos-kmp6.vercel.app',
    FRONTEND_URL.rstrip('/'),
]))
CORS_ALLOWED_ORIGINS = ORIGENES_FRONT
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ORIGENES_FRONT

STATIC_ROOT = BASE_DIR / 'staticfiles'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True