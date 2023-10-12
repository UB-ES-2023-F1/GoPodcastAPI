import uuid

from sqlalchemy import UUID, text
from sqlalchemy.orm import (DeclarativeBase, Mapped, MappedAsDataclass,
                            mapped_column)

from database import Base


# class Base(MappedAsDataclass, DeclarativeBase):
#     pass


class User(Base):
    __tablename__ = 'user'

    username: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    email: Mapped[str]
    password: Mapped[str]
    verified: Mapped[bool] = mapped_column(default=False)