from __future__ import annotations
from typing import Dict

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_keyed_dict


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))

    # user/user_keyword_associations relationship, mapping
    # user_keyword_associations with a dictionary against "special_key" as key.
    user_keyword_associations: Mapped[Dict[str, UserKeywordAssociation]] = relationship(
        back_populates="user",
        collection_class=attribute_keyed_dict("special_key"),
        cascade="all, delete-orphan",
    )
    # proxy to 'user_keyword_associations', instantiating
    # UserKeywordAssociation assigning the new key to 'special_key',
    # values to 'keyword'.
    keywords: AssociationProxy[Dict[str, Keyword]] = association_proxy(
        "user_keyword_associations",
        "keyword",
        creator=lambda k, v: UserKeywordAssociation(special_key=k, keyword=v),
    )

    def __init__(self, name: str):
        self.name = name


class UserKeywordAssociation(Base):
    __tablename__ = "user_keyword"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keyword.id"), primary_key=True)
    special_key: Mapped[str]

    user: Mapped[User] = relationship(
        back_populates="user_keyword_associations",
    )
    keyword: Mapped[Keyword] = relationship()


class Keyword(Base):
    __tablename__ = "keyword"
    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(64))

    def __init__(self, keyword: str):
        self.keyword = keyword

    def __repr__(self) -> str:
        return f"Keyword({self.keyword!r})"
