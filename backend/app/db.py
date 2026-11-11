import psycopg

from .config import settings


def get_connection() -> psycopg.Connection:
    # .env içindeki SQLAlchemy tarzı önek psycopg tarafından tanınmaz
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    return psycopg.connect(url)