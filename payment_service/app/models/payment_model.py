from sqlmodel import SQLModel, Field


class Payment(SQLModel):
    id: int = Field(default=None, primary_key=True)
    amount: float
    currency: str
    status: str
    payment_method: str
    payment_date: str
    payment_id: str
    user_id: int

