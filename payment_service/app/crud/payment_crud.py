from sqlmodel import Session , select
from fastapi import HTTPException
from app.models.payment_model import Payment,PaymentUpdate


# Add a New Payment to the Database
def add_new_payment(payment: Payment, session: Session):
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


# Get All Payments from the Database
def get_all_payments(session: Session):
    payments = session.exec(select(Payment)).all()
    return payments


# Get Payment by ID
def get_payment_by_id(payment_id: int, session: Session):
    payment = session.exec(select(Payment).where(Payment.id == payment_id)).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# Delete Payment by ID
def delete_payment_by_id(payment_id: int, session: Session):
    payment = session.exec(select(Payment).where(Payment.id == payment_id)).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    session.delete(payment)
    session.commit()
    return {"message": "Payment Deleted Successfully"}


# Update Payment by ID
def update_payment_by_id(payment_id: int, to_update_payment_data: PaymentUpdate, session: Session):
    payment = session.exec(select(Payment).where(Payment.id == payment_id)).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment_data = to_update_payment_data.model_dump(exclude_unset=True)
    payment.sqlmodel_update(payment_data)
    session.add(payment)
    session.commit()
    return payment



    