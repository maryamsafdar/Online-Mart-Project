# settings.py
from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
KAFKA_USER_TOPIC = config("KAFKA_USER_TOPIC", cast=str)
KAFKA_CONSUMER_GROUP_ID_FOR_USER = config("KAFKA_CONSUMER_GROUP_ID_FOR_USER", cast=str)

