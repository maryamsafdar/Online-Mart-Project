# main.py
from contextlib import asynccontextmanager
from typing import Annotated
from sqlmodel import Session, SQLModel
from fastapi import FastAPI, Depends, HTTPException
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json

from app import settings
from app.db_engine import engine
from app.models.user_model import User
from app.crud.user_crud import create_user, get_user_by_id, delete_user_by_id, update_user_by_id
from app.deps import get_session, get_kafka_producer


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


async def consume_messages(topic, bootstrap_servers):
    # Create a consumer instance.
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="user_consumer_group",
        auto_offset_reset="earliest",
    )

    # Start the consumer.
    await consumer.start()
    try:
        # Continuously listen for messages.
        async for message in consumer:
            print("Received message on topic {message.topic}")

            user_data = json.loads(message.value.decode())
            print(f"User Data {user_data}")

            with next(get_session()) as session:
                print("Saving data to database")
                db_insert_user = create_user(user_data=User(**user_data), session=session)
                print("DB_INSERT_USER", db_insert_user)

            # Here you can add code to process each message.
            # Example: parse the message, store it in a database, etc.
    finally:
        # Ensure to close the consumer when done.
        await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Creating tables..")
    task = asyncio.create_task(consume_messages(settings.KAFKA_USER_TOPIC, 'broker:19092'))
    create_db_and_tables()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="User Service API",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"User": "Service"}


@app.post("/users/", response_model=User)
async def create_new_user(user: User, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    user_dict = {field: getattr(user, field) for field in user.dict()}
    user_json = json.dumps(user_dict).encode("utf-8")
    print("User JSON:", user_json)
    # Produce message
    await producer.send_and_wait(settings.KAFKA_USER_TOPIC, user_json)
    new_user = create_user(user, session)
    return new_user


@app.get("/users/{user_id}", response_model=User)
def read_single_user(user_id: int, session: Annotated[Session, Depends(get_session)]):
    try:
        return get_user_by_id(user_id=user_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Annotated[Session, Depends(get_session)]):
    try:
        return delete_user_by_id(user_id=user_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: User, session: Annotated[Session, Depends(get_session)]):
    try:
        return update_user_by_id(user_id=user_id, to_update_user_data=user, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
