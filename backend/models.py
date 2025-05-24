from sqlalchemy import Column, Integer, String, Float
from database import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)  # Изменено на True
    longitude = Column(Float, nullable=True) # Изменено на True
    country = Column(String, nullable=False)
    region = Column(String, nullable=False)
    certifications = Column(String)
    labor_practices = Column(String)
    environmental_practices = Column(String)
    last_audit_date = Column(String)
    contact_email = Column(String)
    website = Column(String)
    notes = Column(String)