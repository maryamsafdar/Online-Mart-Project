from pydantic import BaseModel


class CreatePaymentIntentRequest(BaseModel):
    amount: int
    currency: str

class CreatePaymentIntentResponse(BaseModel):
    client_secret: str