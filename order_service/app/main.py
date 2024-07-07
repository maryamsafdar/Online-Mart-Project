# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from sqlmodel import Field, Session, SQLModel, select, Sequence # type: ignore
from fastapi import FastAPI, Depends,HTTPException # type: ignore
from typing import AsyncGenerator
# from aiokafka import AIOKafkaConsumer,AIOKafkaProducer
import asyncio
import json
from app import settings
from app.db_engine import engine
from app.deps import get_kafka_producer,get_session
from app.models.order_model import Order,UpdateOrder
from app.crud.order_cruds import add_order,get_all_orders,get_order,delete_order,update_order


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

    # Start the consumer.
    # await consumer.start()
    # try:
    #     # Continuously listen for messages.
    #     async for message in consumer:
    #         print("RAW")
    #         print(f"Received message on topic {message.topic}")

    #         product_data = json.loads(message.value.decode())
    #         print("TYPE", (type(product_data)))
    #         print(f"Product Data {product_data}")


            
    #         with next(get_session()) as session:
    #             print("SAVING DATA TO DATABSE")
    #             db_insert_product = add_new_product(
    #                 product_data=Product(**product_data), session=session)
    #             print("DB_INSERT_PRODUCT", db_insert_product)
                
    #         # print(f"Received message: {message.value.decode()} on topic {message.topic}")
    #         # Here you can add code to process each message.
    #         # Example: parse the message, store it in a database, etc.
    # finally:
    #     # Ensure to close the consumer when done.
    #     await consumer.stop()


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
# loop = asyncio.get_event_loop()
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



# Root endpoint
@app.get("/")
def read_root():
    return {"Welcome": "order_service"}



@app.post("/orders/", response_model=Order)
def create_order(order:Order, session: Session = Depends(get_session)):
    return add_order(session, order)

@app.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: int, session: Session = Depends(get_session)):
    order = get_order(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/orders/", response_model=list[Order])
def list_orders(user_id: int, session: Session = Depends(get_session)):
    return get_all_orders(session, user_id)

@app.patch("/orders/{order_id}", response_model=UpdateOrder)
def update_order_status(order_id: int,order:UpdateOrder, session: Annotated[Session, Depends(get_session)]):
    try:
        return update_order(session=session, order_id=order_id,to_update_order=order)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/orders/{order_id}")
def delete_order_by_id(order_id: int,session: Annotated[Session, Depends(get_session)]):
    try:
        return delete_order(session=session, order_id=order_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/order-items/", response_model=schemas.OrderItemRead)
# def add_order_item(order_item: schemas.OrderItemCreate, session: Session = Depends(get_session)):
#     order_item_data = OrderItem(**order_item.dict())
#     return crud.add_order_item(session, order_item_data)

# @app.put("/order-items/{order_item_id}", response_model=schemas.OrderItemRead)
# def update_order_item(order_item_id: int, quantity: int, session: Session = Depends(get_session)):
#     order_item = crud.update_order_item(session, order_item_id, quantity)
#     if not order_item:
#         raise HTTPException(status_code=404, detail="OrderItem not found")
#     return order_item

# @app.delete("/order-items/{order_item_id}")
# def remove_order_item(order_item_id: int, session: Session = Depends(get_session)):
#     crud.remove_order_item(session, order_item_id)
#     return {"message": "OrderItem removed successful"}

