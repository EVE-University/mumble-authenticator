# coding: utf-8
from sqlalchemy import Column, ForeignKey, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class Mumbleuser(Base):
    __tablename__ = 'mumble_mumbleuser'

    username = Column(String(254), nullable=False, unique=True)
    pwhash = Column(String(80), nullable=False)
    groups = Column(String)
    user_id = Column(ForeignKey('auth_user.id'), primary_key=True)
    hashfn = Column(String(20), nullable=False)
