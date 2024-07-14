from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from sqlmodel import Session, SQLModel
from fastapi import FastAPI, Depends, HTTPException
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json
import httpx

from app import settings
from app.db_engine import engine
from app.models.order_model import Order
from app.crud.order_cruds import create_new_order, get_all_orders, get_order_by_id, delete_order_by_id
from app.deps import get_session, get_kafka_producer

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

async def consume_messages(topic, bootstrap_servers):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="my-order-consumer-group",
    )

    await consumer.start()
    try:
        async for message in consumer:
            order_data = json.loads(message.value.decode())
            async with get_session() as session:
                db_insert_order = create_new_order(order_data=Order(**order_data), session=session)
    finally:
        await consumer.stop()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    task = asyncio.create_task(consume_messages(settings.KAFKA_ORDER_TOPIC, 'broker:19092'))
    create_db_and_tables()
    yield
    task.cancel()

app = FastAPI(
    lifespan=lifespan,
    title="Order Service API",
    version="0.0.1",
)

@app.get("/")
def read_root():
    return {"Hello": "Order Service"}

async def check_user_exists(user_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://user-service:8000/users/{user_id}")
            response.raise_for_status()
            return response.status_code == 200
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise HTTPException(status_code=e.response.status_code, detail="Error checking user service")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request error: {e}")

async def check_product_availability(product_id: int, quantity: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://product-service:8000/products/{product_id}/availability?quantity={quantity}")
            response.raise_for_status()
            return response.status_code == 200 and response.json().get("available", False)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise HTTPException(status_code=e.response.status_code, detail="Error checking product service")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request error: {e}")

async def update_inventory(product_id: int, quantity: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"http://inventory-service:8000/inventory/update", json={"product_id": product_id, "quantity": quantity})
            response.raise_for_status()
            return response.status_code == 200
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Error updating inventory")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request error: {e}")

@app.post("/orders/", response_model=Order)
async def create_order(order: Order, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    if not await check_user_exists(order.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if not await check_product_availability(order.product_id, order.quantity):
        raise HTTPException(status_code=404, detail="Product not found or unavailable")

    if not await update_inventory(order.product_id, order.quantity):
        raise HTTPException(status_code=400, detail="Failed to update inventory")

    order_dict = order.dict()
    order_json = json.dumps(order_dict).encode("utf-8")

    await producer.send_and_wait("CreateOrder", order_json)
    new_order = create_new_order(order, session)
    return new_order

@app.get("/orders/", response_model=list[Order])
def read_orders(session: Annotated[Session, Depends(get_session)]):
    return get_all_orders(session)

@app.get("/orders/{order_id}", response_model=Order)
def read_single_order(order_id: int, session: Annotated[Session, Depends(get_session)]):
    try:
        return get_order_by_id(order_id=order_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/orders/{order_id}", response_model=dict)
def delete_single_order(order_id: int, session: Annotated[Session, Depends(get_session)]):
    try:
        return delete_order_by_id(order_id=order_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
