from datetime import datetime
from sqlmodel import SQLModel, Field # type: ignore

# class OrderItem(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True)
#     order_id: int = Field(foreign_key="order.id")
#     product_id: int
#     quantity: int
#     price: float
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # updated_at: datetime = Field(default_factory=datetime.utcnow)

    # order: "Order" = Relationship(back_populates="items")

class Order(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    product_id: int
    user_id: int
    total_price: float
    quantity: int
    status: str
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # updated_at: datetime = Field(default_factory=datetime.utcnow)

    # items: list[OrderItem] = Relationship(back_populates="order")


class UpdateOrder(SQLModel):
    product_id: int
    user_id: int
    quantity: int
    total_price: float
    status: str
    # created_at: datetime = Field(default_factory=datetime.utcnow)


    


# class OrderItemBase(SQLModel):
#     order_id: int
#     product_id: int
#     quantity: int
#     price: float

# class OrderItemCreate(OrderItemBase):
#     pass

# class OrderItemRead(OrderItemBase):
#     id: int
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         orm_mode = True

# class OrderBase(SQLModel):
#     user_id: int
#     total_amount: float
#     status: str

# class OrderCreate(OrderBase):
#     items: list[OrderItemCreate]

# class OrderRead(OrderBase):
#     id: int
#     created_at: datetime
#     updated_at: datetime
#     items: list[OrderItemRead]

#     class Config:
#         orm_mode = True



