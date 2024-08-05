# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from app.consumer.product_consumer import consume_messages
from sqlmodel import Field, Session, SQLModel, select, Sequence
from fastapi import FastAPI, Depends, HTTPException
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio
import json
from app import settings
from app.db_engine import engine
from app.deps import get_kafka_producer, get_session
from app.models.product_model import Product, ProductUpdate
from app.crud.product_crud import get_all_products, delete_product_by_id, update_product_by_id, get_product_by_id
from app.shared_auth import GetCurrentUserDep, LoginForAccessTokenDep




def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Creating tables.........")
    task = asyncio.create_task(consume_messages(settings.KAFKA_ORDER_TOPIC, 'broker:19092'))

    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Product Service API", version="0.0.1")

@app.get("/")
def read_root():
    return {"Product": "Service"}

@app.post("/auth/login")
def login(token: LoginForAccessTokenDep):
    return token

@app.post("/products/", response_model=Product)
async def create_new_product(
    product: Product,
    session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
    current_user: GetCurrentUserDep
):
    # Add product to the database
    session.add(product)
    session.commit()
    session.refresh(product)
    
    # Send product data to Kafka topic
    product_dict = {field: getattr(product, field) for field in product.dict()}
    product_json = json.dumps(product_dict).encode("utf-8")
    await producer.send_and_wait(settings.KAFKA_ORDER_TOPIC, product_json)
    
    # Send notification message about the new product
    notification_message = {
        "user_id": current_user['id'],
        "title": "New Product Added",
        "message": f"Product {product.name} has been successfully added.",
        "recipient": current_user['email'],
        "status": "pending"
    }
    notification_json = json.dumps(notification_message).encode("utf-8")
    await producer.send_and_wait(settings.KAFKA_NOTIFICATION_TOPIC, notification_json)

    return product

@app.get("/products/", response_model=list[Product])
def read_products(
    session: Annotated[Session, Depends(get_session)],
    current_user: GetCurrentUserDep
):
    """ Get all products from the database"""
    return get_all_products(session)

@app.get("/products/{product_id}", response_model=Product)
def read_single_product(
    product_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: GetCurrentUserDep
):
    """Read a single product"""
    try:
        return get_product_by_id(product_id=product_id, session=session)
    except HTTPException as e:
        raise e

@app.delete("/products/{product_id}")
async def delete_products(
    product_id: int,
    session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
    current_user: GetCurrentUserDep
):
    """ Delete a single product by ID"""
    try:
        deleted_product = delete_product_by_id(product_id=product_id, session=session)
        
        # Send notification message about the deleted product
        notification_message = {
            "user_id": current_user['id'],
            "title": "Product Deleted",
            "message": f"Product ID {product_id} has been successfully deleted.",
            "recipient": current_user['email'],
            "status": "deleted"
        }
        notification_json = json.dumps(notification_message).encode("utf-8")
        await producer.send_and_wait(settings.KAFKA_NOTIFICATION_TOPIC, notification_json)
        
        return deleted_product
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/products/{product_id}", response_model=Product)
async def update_single_product(
    product_id: int,
    product: ProductUpdate,
    session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
    current_user: GetCurrentUserDep
):
    """ Update a single product by ID"""
    try:
        updated_product = update_product_by_id(product_id=product_id, to_update_product_data=product, session=session)
        
        # Send notification message about the updated product
        notification_message = {
            "user_id": current_user['id'],
            "title": "Product Updated",
            "message": f"Product ID {product_id} has been successfully updated.",
            "recipient": current_user['email'],
            "status": "updated"
        }
        notification_json = json.dumps(notification_message).encode("utf-8")
        await producer.send_and_wait(settings.KAFKA_NOTIFICATION_TOPIC, notification_json)
        
        return updated_product
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
