# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from sqlmodel import Field, Session, SQLModel, select, Sequence
from fastapi import FastAPI, Depends,HTTPException
from typing import AsyncGenerator
from aiokafka import AIOKafkaConsumer,AIOKafkaProducer
import asyncio
import json
from app import settings
from app.db_engine import engine
from app.deps import get_kafka_producer,get_session
from app.models.noti_models import Notification,NotificationUpdate
from app.crud.noti_crud import add_new_notification,delete_notification_by_id,get_notification_by_id,get_all_notifications,update_notification_by_id


def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)

# async def consume_messages(topic, bootstrap_servers):
#     # Create a consumer instance.
#     consumer = AIOKafkaConsumer(
#         topic,
#         bootstrap_servers=bootstrap_servers,
#         group_id="product_consumer_group",
#         auto_offset_reset='earliest'
#     )

#     # Start the consumer.
#     await consumer.start()
#     try:
#         # Continuously listen for messages.
#         async for message in consumer:
#             print("RAW")
#             print(f"Received message on topic {message.topic}")

#             product_data = json.loads(message.value.decode())
#             print("TYPE", (type(product_data)))
#             print(f"Product Data {product_data}")


            
#             with next(get_session()) as session:
#                 print("SAVING DATA TO DATABSE")
#                 db_insert_product = add_new_product(
#                     product_data=Product(**product_data), session=session)
#                 print("DB_INSERT_PRODUCT", db_insert_product)
                
#             # print(f"Received message: {message.value.decode()} on topic {message.topic}")
#             # Here you can add code to process each message.
#             # Example: parse the message, store it in a database, etc.
#     finally:
#         # Ensure to close the consumer when done.
#         await consumer.stop()


# # The first part of the function, before the yield, will
# # be executed before the application starts.
# # https://fastapi.tiangolo.com/advanced/events/#lifespan-function
# # loop = asyncio.get_event_loop()
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables....")
    # task = asyncio.create_task(consume_messages(settings.KAFKA_ORDER_TOPIC, 'broker:19092'))
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
    return {"Noti": "Service"}

@app.get("/test")
def read_root():
    SQLModel.metadata.create_all(engine)
    return {"Noti": "Service"}



@app.post("/notifications/", response_model=Notification)
async def create_new_notification(notification: Notification, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    # notification_dict = {field: getattr(notification, field) for field in notification.dict()}
    # notification_json = json.dumps(notification_dict).encode("utf-8")
    # print("notificationJSON:", notification_json)
    # # Produce message
    # await producer.send_and_wait(settings.KAFKA_NOTIFICATION_TOPIC, notification_json)
    return add_new_notification(notification_data=notification, session=session)
    

@app.get("/notifications/", response_model=list[Notification])
def read_notifications(session: Annotated[Session, Depends(get_session)]):
    """Get all notifications from the database"""
    return get_all_notifications(session)

@app.get("/notifications/{notification_id}", response_model=Notification)
def read_single_notification(notification_id: int, session: Annotated[Session, Depends(get_session)]):
    """Read a single notification"""
    try:
        return get_notification_by_id(notification_id=notification_id, session=session)
    except HTTPException as e:
        raise e

@app.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, session: Annotated[Session, Depends(get_session)]):
    """Delete a single notification by ID"""
    try:
        return delete_notification_by_id(notification_id=notification_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/notifications/{notification_id}", response_model=NotificationUpdate)
def update_single_notification(notification_id: int, notification: NotificationUpdate, session: Annotated[Session, Depends(get_session)]):
    """Update a single notification by ID"""
    try:
        return update_notification_by_id(notification_id=notification_id, to_update_notification_data=notification, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
