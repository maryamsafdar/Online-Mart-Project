# settings.py
from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
KAFKA_ORDER_TOPIC = config("KAFKA_ORDER_TOPIC", cast=str)
BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
KAFKA_CONSUMER_GROUP_ID_FOR_ORDER = config("KAFKA_CONSUMER_GROUP_ID_FOR_ORDER", cast=str)
USER_SERVICE_URL = config("USER_SERVICE_URL", cast=str)
PRODUCT_SERVICE_URL = config("PRODUCT_SERVICE_URL", cast=str)
INVENTORY_SERVICE_URL = config("INVENTORY_SERVICE_URL", cast=str)
