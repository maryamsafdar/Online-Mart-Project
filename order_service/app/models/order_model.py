# models.py
from sqlmodel import SQLModel, Field

# Order Microservice Models
class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    product_id: int
    quantity: int
    status: str
