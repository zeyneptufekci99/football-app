import psycopg

from .config import settings


def get_connection(autocommit: bool = False) -> psycopg.Connection:
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    return psycopg.connect(url, autocommit=autocommit)