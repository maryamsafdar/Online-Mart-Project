from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import stripe
from app.settings import STRIP_API_KEY
from app.schemas import CreatePaymentIntentRequest, CreatePaymentIntentResponse
from app.deps import create_db_and_tables

# Lifespan manager to handle startup and shutdown of the app
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables.......")
    create_db_and_tables()
    yield

# Replace with your Stripe secret key
stripe.api_key = STRIP_API_KEY

# Initialize FastAPI app with custom lifespan
app = FastAPI(
    lifespan=lifespan,
    title="Payment_service_API", 
    version="0.0.1",
    # root_path="/payment",
    # servers=[
    #     {
    #         "url": "http://127.0.0.1:8008",
    #         "description": "Development Server"
    #     }
    # ]
)

# 01 Define the route to read root
@app.get("/")
def read_root():
    return {"Welcome": "Payment_service_API"}


# 02 Create payment intent endpoint
@app.post("/create-payment-intent", response_model=CreatePaymentIntentResponse)
async def create_payment_intent(request: CreatePaymentIntentRequest):
    try:
        # Create a Payment Intent using the Stripe API
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            payment_method_types=["card"],  # You can add more payment methods if needed
        )

        return CreatePaymentIntentResponse(client_secret=intent.client_secret)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))