# crud.py
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models.order_model import Order

# Create a New Order in the Database
def create_new_order(order_data: Order, session: Session):
    print("Adding Order to Database")
    session.add(order_data)
    session.commit()
    session.refresh(order_data)
    return order_data

# Get All Orders from the Database
def get_all_orders(session: Session):
    all_orders = session.exec(select(Order)).all()
    return all_orders

# Get an Order by ID
def get_order_by_id(order_id: int, session: Session):
    order = session.exec(select(Order).where(Order.id == order_id)).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Delete an Order by ID
def delete_order_by_id(order_id: int, session: Session):
    # Step 1: Get the Order by ID
    order = session.exec(select(Order).where(Order.id == order_id)).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    # Step 2: Delete the Order
    session.delete(order)
    session.commit()
    return {"message": "Order Deleted Successfully"}
