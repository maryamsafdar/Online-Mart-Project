# main.py
from datetime import timedelta
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from sqlmodel import Field, Session, SQLModel, select, Sequence
from fastapi import FastAPI, Depends,HTTPException # type :ignore
from typing import AsyncGenerator
from aiokafka import AIOKafkaConsumer,AIOKafkaProducer
import asyncio
import json
from app import settings
from app.db_engine import engine
from app.deps import get_kafka_producer,get_session
from app.models.user_model import User,UserUpdate,Register_User,Token
from app.crud.user_crud import add_new_user,get_user_by_id,get_all_users,delete_user_by_id,update_user_by_id
from app.auth import current_user, get_user_from_db ,hash_password,authenticate_user,EXPIRY_TIME,create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.email_address import validate_email_address


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
    task = asyncio.create_task(consume_messages(settings.KAFKA_NOTIFICATION_TOPIC,'broker:19092'))
    
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="User API with DB", 
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

@app.patch("/users/{user_id}", response_model=dict)
async def update_single_user(user_id: int, user: UserUpdate, session: Annotated[Session, Depends(get_session)]):
    """ Update a single user by ID"""
    try:
        if user.password:
            user.password = hash_password(user.password)
        updated_user = update_user_by_id(user_id=user_id, to_update_user_data=user, session=session)

        # Generate a new token for the updated user
        expire_time = timedelta(minutes=EXPIRY_TIME)
        access_token = create_access_token({"sub": updated_user.username}, expire_time)
        
        updated_user_dict = {
            "username": updated_user.username,
            "email": updated_user.email,
            "password": user.password,  # Return the hashed password
        }

        return {
            "message": "User updated successfully",
            "user": updated_user_dict
        }
    except HTTPException as e:
        raise e



#signup user if not already signed up#signup user if not already signed up
@app.post("/register")
async def regiser_user(new_user:Annotated[Register_User, Depends()],
                        session:Annotated[Session, Depends(get_session)],
                        producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):

   
    db_user = get_user_from_db(session, new_user.username, new_user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="User with these credentials already exists")
    user = User(
                username = new_user.username,
                email = new_user.email,
                password = hash_password(new_user.password))

    session.add(user)
    session.commit()
    session.refresh(user)

    #send the registered user into kafka topic 
    user_dict = {field: getattr(user, field) for field in user.dict()}
    user_json = json.dumps(user_dict).encode("utf-8")

    # Send notification about new user registration
    notification_message = {
        "user_id": user.id,
        "title": "User Registered",
        "message": f"User {user.username} has been registered successfully.",
        "recipient": user.email,
        "status": "pending"
    }
    notification_json = json.dumps(notification_message).encode("utf-8")
    await producer.send_and_wait(settings.KAFKA_NOTIFICATION_TOPIC, notification_json)
    return {"message": f""" {user.username} successfully registered """}    

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

@app.get("/current-user/", response_model=User)
async def get_current_user(current_user: Annotated[User, Depends(current_user)]):
    return current_user

@app.get("/protected-route/")
async def protected_route(current_user: Annotated[User, Depends(current_user)]):
    return {
        "message": f"Hello {current_user.username}, you are successfully logged in!",
        "user": current_user,
        "details": "This is a protected route. Only authenticated users can access it."
    }