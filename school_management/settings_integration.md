# Settings Integration

Add these sections in your Django `settings.py`.

## Installed Apps

```python
INSTALLED_APPS = [
    # ...
    "django.contrib.sessions",
    "django.contrib.messages",
    "accounts",
]
```

## Templates + Context Processor

```python
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

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
                "accounts.context_processors.role_menu",
            ],
        },
    },
]
```

## Login/Session Settings

```python
LOGIN_URL = "login"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
```

## Middleware (verify)

```python
MIDDLEWARE = [
    # ...
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
```

## Database (MySQL db_linkEd)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "db_linkEd",
        "USER": "<your_mysql_user>",
        "PASSWORD": "<your_mysql_password>",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
```
