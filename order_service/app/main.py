# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated,Any
from sqlmodel import Field, Session, SQLModel, select, Sequence # type: ignore
from fastapi import FastAPI, Depends,HTTPException # type: ignore
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer #type:ignore
import asyncio
import json
from app import settings
from app.db_engine import engine
from app.deps import get_kafka_producer,get_session
from app.models.order_model import Order,OrderUpdate,OrderBase,OrderCreate,OrderRead
from app.crud.order_cruds import place_order,get_all_orders,get_order,delete_order,update_order,send_order_to_kafka,get_product_price,update_order_status
import requests
from app.consumer.order_check_reponse import consume_order_response_messages
from app.shared_auth import get_current_user,get_login_for_access_token

GetCurrentUserDep = Annotated[ Any, Depends(get_current_user)]
LoginForAccessTokenDep = Annotated[dict, Depends(get_login_for_access_token)]


def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
    #listens the order-check-response topic
    task = asyncio.create_task(consume_order_response_messages("order-check-response", 'broker:19092'))
    create_db_and_tables()
    yield 


app = FastAPI(lifespan=lifespan, title="Order API with DB", 
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
    return {"Welcome": "order_service"}


@app.post("/auth/login")
def login(token:LoginForAccessTokenDep):
    return token


@app.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)], current_user: GetCurrentUserDep):
    product_price = get_product_price(order.product_id)
    print("Product Price:", product_price)
    order_data = Order(**order.dict(exclude={"user_id"}), user_id=current_user["id"])
    new_order = send_order_to_kafka(session, order_data, product_price)

    order_dict = {field: getattr(order_data, field) for field in new_order.dict()}
    order_json = json.dumps(order_dict).encode("utf-8")
    print("orderJSON:", order_json)
    await producer.send_and_wait("order_placed", order_json)
    return new_order

@app.get("/orders/{order_id}", response_model=OrderRead)
def read_order(order_id: int, session: Session = Depends(get_session), current_user: Any = Depends(get_current_user)):
    return get_order(session, order_id, current_user["id"])

@app.get("/orders/", response_model=list[OrderRead])
def list_orders(session: Session = Depends(get_session), current_user: Any = Depends(get_current_user)):
    return get_all_orders(session, current_user["id"])

# @app.patch("/orders/{order_id}", response_model=OrderRead)
# def update_order_item(order_id: int, order: OrderUpdate, session: Annotated[Session, Depends(get_session)], current_user: GetCurrentUserDep ):
#     return update_order(session=session, order_id=order_id, user_id=current_user["id"], to_update_order=order)

@app.delete("/orders/{order_id}")
def delete_order_by_id(order_id: int, session: Annotated[Session, Depends(get_session)], current_user: Any = Depends(get_current_user)):
    return delete_order(session=session, order_id=order_id, user_id=current_user["id"])
        
@app.patch("/orders/{order_id}", response_model=Order)
def update_status(order_id: int, status: str, session: Annotated[Session, Depends(get_session)], current_user: GetCurrentUserDep):
    order = update_order_status(session, order_id, current_user["id"], status)
    return order

