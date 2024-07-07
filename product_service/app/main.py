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
from app.models.product_model import Product,ProductUpdate
from app.crud.product_crud import add_new_product,get_all_products,delete_product_by_id,update_product_by_id,get_product_by_id


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
                
            # print(f"Received message: {message.value.decode()} on topic {message.topic}")
            # Here you can add code to process each message.
            # Example: parse the message, store it in a database, etc.
    # finally:
    #     # Ensure to close the consumer when done.
    #     await consumer.stop()


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
# loop = asyncio.get_event_loop()
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
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
    return {"Product": "Service"}



@app.post("/products/", response_model=Product)
async def create_new_product(product: Product, session: Annotated[Session, Depends(get_session)],producer:Annotated[AIOKafkaProducer,Depends(get_kafka_producer)]):
    # product_dict = {field: getattr(product, field) for field in product.dict()}
    # product_json = json.dumps(product_dict).encode("utf-8")
    # print("productJSON:", product_json)
    # # Produce message
    # await producer.send_and_wait(settings.KAFKA_ORDER_TOPIC, product_json)
    new_product = add_new_product(product,session)
    return new_product

@app.get("/products/", response_model=list[Product])
def read_products(session: Annotated[Session, Depends(get_session)]):
    """ Get all products from the database"""
    return get_all_products(session)

@app.get("/products/{product_id}", response_model=Product)
def read_single_product(product_id: int, session: Annotated[Session, Depends(get_session)]):
    """Read a single product"""
    try:
        return get_product_by_id(product_id=product_id, session=session)
    except HTTPException as e:
        raise e




@app.delete("/products/{product_id}")
def delete_products(product_id:int , session: Annotated[Session, Depends(get_session)]):
    """ Delete a single product by ID"""
    try:
        return delete_product_by_id(product_id=product_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/products/{product_id}", response_model=ProductUpdate)
def update_single_product(product_id: int, product: ProductUpdate, session: Annotated[Session, Depends(get_session)]):
    """ Update a single product by ID"""
    try:
        return update_product_by_id(product_id=product_id, to_update_product_data=product, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))