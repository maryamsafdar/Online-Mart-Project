# settings.py
from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
KAFKA_USER_TOPIC = config("KAFKA_USER_TOPIC", cast=str)
BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
