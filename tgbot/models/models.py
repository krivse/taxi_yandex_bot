from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, BigInteger, func, Integer, ForeignKey, Boolean, SmallInteger, Text
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String)
    phone = Column(BigInteger, nullable=False, unique=True)
    taxi_id = Column(String, nullable=False)
    at_created = Column(DateTime(timezone=True), server_default=func.now())

    driver_settings = relationship('DriverSettings', back_populates='user', cascade='all, delete')


class DriverSettings(Base):
    __tablename__ = 'driver_settings'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'))
    limit = Column(SmallInteger, default=None)
    access_limit = Column(Boolean, default=False)
    url_driver_limit = Column(String, default=None)
    smz = Column(Boolean, default=False)

    user = relationship('User', back_populates='driver_settings')


class AccountPark(Base):
    __tablename__ = 'account_park'
    id = Column(Integer, primary_key=True)
    password = Column(String)


class Help(Base):
    __tablename__ = 'help'
    id = Column(Integer, primary_key=True)
    text = Column(String)
