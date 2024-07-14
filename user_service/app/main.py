# main.py
from datetime import timedelta
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from sqlmodel import Field, Session, SQLModel, select, Sequence
from fastapi import FastAPI, Depends,HTTPException
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json
from app import settings
from app.db_engine import engine
from app.deps import get_kafka_producer, get_session
from app.models.user_model import User,UserUpdate,Token
from app.crud.user_crud import add_new_user,get_user_by_id,get_all_users,delete_user_by_id,update_user_by_id
from app.auth import authenticate_user,EXPIRY_TIME,create_access_token
from fastapi.security import OAuth2PasswordRequestForm

def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)

async def consume_messages(topic, bootstrap_servers):
    # Create a consumer instance.
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="user-consumer-group",
        # auto_offset_reset="earliest",
    )

    # Start the consumer.
    await consumer.start()
    try:
        # Continuously listen for messages.
        async for message in consumer:
            print("RAW")
            print(f"Received message on topic {message.topic}")

            user_data = json.loads(message.value.decode())
            print("TYPE", (type(user_data)))
            print(f"User Data {user_data}")

            with next(get_session()) as session:
                print("SAVING DATA TO DATABSE")
                db_insert_user = add_new_user(
                    user_data=User(**user_data), session=session)
                print("DB_INSERT_USER", db_insert_user)

            # Here you can add code to process each message.
            # Example: parse the message, store it in a database, etc.
    finally:
        # Ensure to close the consumer when done.
        await consumer.stop()



@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
    task = asyncio.create_task(consume_messages(
        settings.KAFKA_USER_TOPIC, 'broker:19092'))
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    # servers=[
    #     {
    #         "url": "http://127.0.0.1:8000", # ADD NGROK URL Here Before Creating GPT Action
    #         "description": "Development Server"
    #     }
    #     ]
        )



@app.get("/")
def read_root():
    return {"User": "Service"}


# @app.post("/users/", response_model=User)
# def create_new_user(user_data: User, session: Annotated[Session, Depends(get_session)]):
#     new_user = add_new_user(user_data=user_data, session=session)
#     return new_user

@app.get("/users/", response_model=list[User])
def read_users(session: Annotated[Session, Depends(get_session)]):
    """ Get all users from the database"""
    return get_all_users(session)



 #signup user if not already signed up
@app.post("/register/", response_model=User)
async def register_user(user: User, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    """ Register a new user and send it to Kafka"""

    user_dict = {field: getattr(user, field) for field in user.dict()}
    user_json = json.dumps(user_dict).encode("utf-8")
    print("user_JSON:", user_json)
    # Produce message
    await producer.send_and_wait(settings.KAFKA_USER_TOPIC, user_json)
    new_user = add_new_user(user, session)
    return new_user





# login user with username and password
@app.post('/token')
async def login(form_data:Annotated[OAuth2PasswordRequestForm, Depends()],
                session:Annotated[Session, Depends(get_session)]):
    user = authenticate_user (form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expire_time = timedelta(minutes=EXPIRY_TIME)
    access_token = create_access_token({"sub":form_data.username}, expire_time)
    
  
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/{user_id}", response_model=User)
def read_single_user(user_id: int, session: Annotated[Session, Depends(get_session)]):
    """Read a single user"""
    try:
        return get_user_by_id(user_id=user_id, session=session)
    except HTTPException as e:
        raise e

@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Annotated[Session, Depends(get_session)]):
    """ Delete a single user by ID"""
    try:
        return delete_user_by_id(user_id=user_id, session=session)
    except HTTPException as e:
        raise e

@app.patch("/users/{user_id}", response_model=UserUpdate)
def update_single_user(user_id: int, user: UserUpdate, session: Annotated[Session, Depends(get_session)]):
    """ Update a single user by ID"""
    try:
        return update_user_by_id(user_id=user_id, to_update_user_data=user, session=session)
    except HTTPException as e:
        raise e





