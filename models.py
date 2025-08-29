from database import Base
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from enum import Enum

class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.USER)