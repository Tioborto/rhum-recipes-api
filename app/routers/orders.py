from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, UTC

from app.database import get_session
from app.models import (
    BottleOrder,
    BottleOrderCreate,
    BottleOrderRead,
    BottleOrderUpdate,
    StockEntry,
    OrderStatus
)

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/", response_model=list[BottleOrderRead])
def get_orders(session: Session = Depends(get_session)):
    return session.exec(select(BottleOrder)).all()

@router.get("/{order_id}", response_model=BottleOrderRead)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(BottleOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/", response_model=BottleOrderRead)
def create_order(order_in: BottleOrderCreate, session: Session = Depends(get_session)):
    order = BottleOrder.model_validate(order_in)
    
    # If the order is linked to a stock entry, decrease the stock immediately
    if order.stock_entry_id:
        stock = session.get(StockEntry, order.stock_entry_id)
        if not stock:
            raise HTTPException(status_code=404, detail="Linked Stock Entry not found")
        if stock.quantity < order.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock available")
        stock.quantity -= order.quantity
        session.add(stock)

    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.put("/{order_id}", response_model=BottleOrderRead)
def update_order(order_id: int, order_in: BottleOrderUpdate, session: Session = Depends(get_session)):
    order = session.get(BottleOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_data = order_in.model_dump(exclude_unset=True)
    
    # Handle stock restoration/deduction if quantity changes or stock entry changes
    # For simplicity, we won't fully implement complex cross-stock updates here,
    # but we will handle simple quantity changes on the same stock_entry.
    old_quantity = order.quantity
    
    for key, value in order_data.items():
        setattr(order, key, value)
        
    order.updated_at = datetime.now(UTC)

    if order.stock_entry_id and 'quantity' in order_data:
        stock = session.get(StockEntry, order.stock_entry_id)
        if stock:
            diff = order.quantity - old_quantity
            if stock.quantity < diff:
                raise HTTPException(status_code=400, detail="Not enough stock to increase order")
            stock.quantity -= diff
            session.add(stock)

    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(BottleOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Restore stock
    if order.stock_entry_id:
        stock = session.get(StockEntry, order.stock_entry_id)
        if stock:
            stock.quantity += order.quantity
            session.add(stock)

    session.delete(order)
    session.commit()
    return None
