import uuid
from typing import List

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UUID, ForeignKey, PrimaryKeyConstraint, text
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)
import json


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    verified: Mapped[bool] = mapped_column(default=False)
    bio: Mapped[str] = mapped_column(nullable=True, default=None)
    image: Mapped[bytes] = mapped_column(BYTEA, nullable=True, default=None, deferred=True)


class Podcast(Base):
    __tablename__ = "podcast"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    cover: Mapped[bytes] = mapped_column(BYTEA, deferred=True)
    name: Mapped[str] = mapped_column(unique=True)
    summary: Mapped[str]
    description: Mapped[str]
    id_author: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    author: Mapped[User] = relationship(init=False)
    category: Mapped[str] = mapped_column(nullable=True, default=None)


class Episode(Base):
    __tablename__ = "episode"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )

    audio: Mapped[bytes] = mapped_column(BYTEA, deferred=True)
    title: Mapped[str]
    description: Mapped[str]
    id_podcast: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("podcast.id", ondelete="CASCADE")
    )
    tags: Mapped[str] = mapped_column(nullable=True, default=None)

    def set_tags(self, tags):
        self.tags = json.dumps(tags)

    def get_tags(self):
        return json.loads(self.tags) if self.tags else []


class Section(Base):
    __tablename__ = "section"

    begin: Mapped[int]  # represents seconds
    end: Mapped[int]
    title: Mapped[str]
    description: Mapped[str]
    id_episode: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("episode.id", ondelete="CASCADE")
    )

    # create a composite primary key
    __table_args__ = (PrimaryKeyConstraint("title", "id_episode"),)


class User_episode(Base):
    """
    This table allows us to retrieve the minute were a given
    user stopped watching an episode
    """

    __tablename__ = "user_episode"

    id_episode: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("episode.id", ondelete="CASCADE")
    )
    id_user: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    current_sec: Mapped[int]  # represents seconds

    # create a composite primary key
    __table_args__ = (PrimaryKeyConstraint("id_episode", "id_user"),)


class StreamLater(Base):
    __tablename__ = "stream_later"

    id_episode: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("episode.id", ondelete="CASCADE")
    )
    id_user: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    episode: Mapped[Episode] = relationship(init=False)

    __table_args__ = (PrimaryKeyConstraint("id_episode", "id_user"),)


class Favorite(Base):
    __tablename__ = "favorite"

    id_podcast: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("podcast.id", ondelete="CASCADE")
    )
    id_user: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    podcast: Mapped[Podcast] = relationship(init=False)

    __table_args__ = (PrimaryKeyConstraint("id_podcast", "id_user"),)


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    content: Mapped[str]
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("now()"), init=False
    )
    id_user: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    id_episode: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("episode.id", ondelete="CASCADE")
    )
    user: Mapped[User] = relationship(init=False)
    episode: Mapped[Episode] = relationship(init=False)
    replies: Mapped[List["Reply"]] = relationship(
        init=False,
        back_populates="comment",
        order_by="Reply.created_at",
        cascade="all, delete-orphan",
    )


class Reply(Base):
    __tablename__ = "reply"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    content: Mapped[str]
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("now()"), init=False
    )
    id_user: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    id_comment: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("comment.id", ondelete="CASCADE")
    )
    user: Mapped[User] = relationship(init=False)
    comment: Mapped[Comment] = relationship(init=False, back_populates="replies")


class Follow(Base):
    __tablename__ = "follow"

    id_follower: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    id_followed: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    
    followed: Mapped[User] = relationship(init=False, foreign_keys=[id_followed])

    __table_args__ = (PrimaryKeyConstraint("id_follower", "id_followed"),)


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    id_user: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    type: Mapped[str]
    object: Mapped[dict[str, any]] =  mapped_column(JSONB)
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("now()"), init=False
    )


db = SQLAlchemy(model_class=Base)
