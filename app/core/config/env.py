import os
from typing import Literal

from dotenv import load_dotenv

_ = load_dotenv()

EnvKey = Literal[
    "DB_STRING",
    "ALLOW_ADMINS_ONLY",
    "ALMEBIC_DB_URL",
    "DEBUG",
    "EMAIL_APP_PASSWORD",
    "APP_EMAIL_ADDRESS",
    "EMAIL_TEMPLATES_PATH",
    "ADMIN_EMAILS",
    "SUPER_ADMIN_EMAILS",
    "PG_USER",
    "PG_PASSWORD",
    "PG_DATABASE",
    "GEMINI_API_KEY",
]


def get_env(name: EnvKey | str, default: str = ""):
    return os.getenv(name) or default
