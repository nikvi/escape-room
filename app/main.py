from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
import time

"""
1. Hold System: Reserve a slot temporarily (5-min auto-expiration)
2. Confirm/Release: Convert hold to booking or explicitly release
3. Testing: 2-3 tests focusing on expiration and race conditions
Assumptions: slots ids are unique and point to slots that map to schedules and calendar

"""

app = FastAPI(title="Escape Room Booking System")
hold_engine = redis.Redis(host='redis', port=6379, decode_responses=True)

engine = create_engine("sqlite:///./escape_room.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BookingRecord(Base):
    __tablename__ = "Bookings"
    slot_id = Column(String, primary_key=True, index=True)
    team_name = Column(String)
    creation_date = Column(Float, default=time.time)

Base.metadata.create_all(bind=engine)

class BookingRequest(BaseModel):
    slot_id : str
    team_name: str

@app.post("/hold")
# teams should be able to hold for 5 mins
# we are not checking if this slot is already booked and in the sql table
def hold_slot(req: BookingRequest):
    hold_key = f"hold:{req.slot_id}"
    is_set = hold_engine.set(hold_key, req.team_name, nx=True, ex=300)
    if is_set:
        return { "status": "slot held", "time_remaining_seconds": 300}
    raise HTTPException(status_code=400, detail="Slot already held or booked")

#teams should be able to confirm and book
# confirm and book is just writing  to the db and deleting the hold
@app.post("/confirm")
def confirm_booking(req: BookingRequest):
  hold_key = f"hold:{req.slot_id}"
  current_holder = hold_engine.get(hold_key)
  if current_holder != req.team_name:
      raise HTTPException(status_code=400, detail="Slot already held or booked")
  db = SessionLocal()
  try:
    new_booking = BookingRecord(slot_id=req.slot_id, team_name=req.team_name)
    db.add(new_booking)
    db.commit()
    hold_engine.delete(hold_key) 
    return {"status": "confirmed"}
  except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
  finally:
        db.close()
      
    
@app.post("/release")
# teams should be able to release a booking
# assumption the release if only for the 5 min hold release
# deleting a booking will be deleting the slot id from the database
def release_booking(req: BookingRequest):
    hold_key = f"hold:{req.slot_id}"
    hold_value = hold_engine.get(hold_key)
    if hold_value == req.team_name:
        hold_engine.delete(hold_key)
        return {"status": "released"}
    raise HTTPException(status_code=400, detail="No active hold found for this team")




