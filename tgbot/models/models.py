from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, BigInteger, func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String)
    phone = Column(BigInteger, nullable=False)
    taxi_id = Column(String, nullable=False)
    at_created = Column(DateTime(timezone=True), server_default=func.now())
