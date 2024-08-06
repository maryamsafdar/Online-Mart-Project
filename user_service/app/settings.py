from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
KAFKA_CONSUMER_GROUP_ID_FOR_USER = config("KAFKA_CONSUMER_GROUP_ID_FOR_USER", cast=str)



# Email settings
SMTP_SERVER = config("SMTP_SERVER", cast=str)
SMTP_PORT = config("SMTP_PORT", cast=int)
SENDER_EMAIL = config("SENDER_EMAIL", cast=str)
SENDER_PASSWORD = config("SENDER_PASSWORD", cast=Secret)
RECEIVER_EMAIL = config("RECEIVER_EMAIL", cast=str)