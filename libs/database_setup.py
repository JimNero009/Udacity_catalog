import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Catagory(Base):
    __tablename__ = 'catagory'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class CatalogItem(Base):
    __tablename__ = 'catalog_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(80))
    catagory_id = Column(String(80), ForeignKey("catagory.id"), nullable=False)
    added = Column(Date, nullable=False)
    catagory = relationship(Catagory)
    user_id = Column(String(80), ForeignKey("user.id"), nullable=False)
    user = relationship(User)


engine = create_engine('sqlite:///catalog.db?check_same_thread=False')


Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)