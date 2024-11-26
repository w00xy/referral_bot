from sqlalchemy import String, BigInteger, Float, Integer, ForeignKey, DateTime, func, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    user_first_name: Mapped[str] = mapped_column((String(40)), nullable=True)
    username: Mapped[str] = mapped_column((String(60)), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False)

    history: Mapped["UserHistory"] = relationship("UserHistory", back_populates="user", cascade="all, delete, delete-orphan", lazy="select")
    referral: Mapped["Referral"] = relationship("Referral", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined")

    # positions: Mapped[list["Position"]] = relationship("Position", back_populates="user", lazy="joined")
    # referral: Mapped["Referral"] = relationship("Referral", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined")


class Referral(Base):
    __tablename__ = 'referrals'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    referer_id: Mapped[int] = mapped_column(BigInteger, nullable=True, default=None)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="referral", lazy="joined")


class UserHistory(Base):
    __tablename__ = 'user_history'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    token: Mapped[str] = mapped_column((String(40)), nullable=True)
    address: Mapped[str] = mapped_column((String(120)), nullable=True)
    status: Mapped[str] = mapped_column((String(40)), nullable=True)
    answer: Mapped[str] = mapped_column((String(240)), nullable=True, default=None)

    user: Mapped["User"] = relationship("User", back_populates="history")

class Channel(Base):
    __tablename__ = 'channels'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    channel_name: Mapped[str] = mapped_column((String(80)), nullable=True)
    channel_address: Mapped[str] = mapped_column((String(80)), nullable=True)
    channel_link: Mapped[str] = mapped_column(String(140), nullable=False)

class ChannelRequests(Base):
    __tablename__ = 'channel_requests'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)


class HelpMessage(Base):
    __tablename__ = 'help_messages'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, default="")
