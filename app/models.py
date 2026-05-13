from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    badge = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    role = Column(String, default="basic")
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # 'active', 'inactive', 'deactivated'
    pin = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    walkaround_submissions = relationship("WalkaroundSubmission", back_populates="employee")
    sessions = relationship("SessionRecord", back_populates="employee", cascade="all, delete-orphan")

class SessionRecord(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)  # session token
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    employee = relationship("Employee", back_populates="sessions")

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_miles = Column(Float, default=2.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ObservationForm(Base):
    __tablename__ = "observation_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("ObservationQuestion", back_populates="form", cascade="all, delete-orphan")

class ObservationQuestion(Base):
    __tablename__ = "observation_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("observation_forms.id"), nullable=False)
    text = Column(String, nullable=False)
    question_type = Column(String, default="text")
    required = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    form = relationship("ObservationForm", back_populates="questions")

class WalkaroundForm(Base):
    __tablename__ = "walkaround_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pdf_path = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sections = relationship("WalkaroundSection", back_populates="form", cascade="all, delete-orphan")
    submissions = relationship("WalkaroundSubmission", back_populates="form")

class WalkaroundSection(Base):
    __tablename__ = "walkaround_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("walkaround_forms.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    form = relationship("WalkaroundForm", back_populates="sections")
    questions = relationship("WalkaroundQuestion", back_populates="section", cascade="all, delete-orphan")

class WalkaroundQuestion(Base):
    __tablename__ = "walkaround_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("walkaround_sections.id"), nullable=False)
    text = Column(String, nullable=False)
    question_type = Column(String, default="pass_fail")
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    section = relationship("WalkaroundSection", back_populates="questions")

class WalkaroundSubmission(Base):
    __tablename__ = "walkaround_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("walkaround_forms.id"), nullable=False)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    responses = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    employee = relationship("Employee", back_populates="walkaround_submissions")
    form = relationship("WalkaroundForm", back_populates="submissions")


