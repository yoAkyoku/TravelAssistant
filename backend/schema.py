from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    travel_theme = Column(String, nullable=True)
    description = Column(String, nullable=True)
    departure_location = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    num_peoples = Column(Integer, default=1)
    duration = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    features = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)

    # 修正多餘的逗號
    days = relationship("PlanDay", back_populates="plan", cascade="all, delete-orphan", order_by="PlanDay.day")

class PlanDay(Base):
    __tablename__ = "plan_days"

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    daily_theme = Column(String)
    itinerary_location = Column(String)
    day = Column(Date)
    transportation = Column(Text)

    plan = relationship("Plan", back_populates="days")
    segments = relationship("PlanSegment", back_populates="day", cascade="all, delete-orphan", order_by="PlanSegment.id")
    accommodation = relationship("Accommodation", uselist=False, back_populates="day", cascade="all, delete-orphan")

class PlanSegment(Base):
    __tablename__ = "plan_segments"

    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("plan_days.id"))
    time_slot = Column(String)

    day = relationship("PlanDay", back_populates="segments")
    activities = relationship("Activity", back_populates="segment", cascade="all, delete-orphan", order_by="Activity.id")

class Activity(Base):
    __tablename__ = "plan_activities"

    id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey("plan_segments.id"))
    activity_name = Column(String)
    type = Column(String)
    activity_location = Column(String)
    description = Column(Text)
    estimated_duration = Column(String)
    notes = Column(Text)

    segment = relationship("PlanSegment", back_populates="activities")

class Accommodation(Base):
    __tablename__ = "plan_accommodation"

    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("plan_days.id"))
    hotel_id = Column(Integer, nullable=True)
    name = Column(String)
    url = Column(String)
    address = Column(String)
    price = Column(Float)
    currency = Column(String)
    review_score = Column(Float)
    review_count = Column(Integer)
    arrival_date = Column(Date)
    departure_date = Column(Date)

    day = relationship("PlanDay", back_populates="accommodation")