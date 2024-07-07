from sqlmodel import SQLModel, Field


class Payment(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    order_id: int
    user_id: int
    amount: float
    currency: str
    status: str
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # updated_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentUpdate(SQLModel):
    order_id: int
    user_id: int
    amount: float | None = None
    currency: str | None = None
    status: str | None = None

