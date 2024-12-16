from sqlalchemy import (
    func,
    String, 
    Integer, 
    BigInteger, 
    DateTime, 
    ForeignKey,
    Enum as SQLEnum,
    Text,
    Boolean,
    Numeric,

    Table,
    Column,
    )
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from enum import Enum


class AllRares(str, Enum):
    LEGENDARY = "Легендарный"
    EPIC = "Эпический"
    RARE = "Редкий"
    SIMPLE = "Обычный"


class ShopTypes(str, Enum):
    GLOBAL = "Глобальный"
    LOCAL = "Локальный"


class UserStatus(str, Enum):
    SUPER_VIP = "Супер VIP"
    MIDDLE_VIP = "Средний VIP"
    BASE_VIP = "Малый VIP"

    NOT_VIP = "Обычный пользователь"


class Sex(str, Enum):
    MALE = "Мужчина"
    WOMEN = "Женщина"

    NOT_SETUP = "Не указан"


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# Промежуточная таблица для связи "многие-ко-многим"
user_wife_association = Table(
    "user_wife_association",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.id"), primary_key=True),
    Column("wife_id", BigInteger, ForeignKey("wifes.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    username: Mapped[str] = mapped_column(String, default="Не задано")
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus, name="user_status"),
                                                default=UserStatus.NOT_VIP)

    balance: Mapped[Decimal] = mapped_column(Numeric(precision=25, scale=2), default=Decimal('0.00'))
    profile_imgs: Mapped[str] = mapped_column(String, nullable=False)

    characters: Mapped[list["Wife"]] = relationship(
        "Wife",
        secondary=user_wife_association,
        back_populates="users"
    )

    slots_for_sale: Mapped[list["Slot"]] = relationship("Slot", back_populates="seller")
    sent_trades: Mapped[list["Trade"]] = relationship("Trade", foreign_keys="Trade.from_id", back_populates="from_")

    received_trades: Mapped[list["Trade"]] = relationship("Trade", foreign_keys="Trade.to_id", back_populates="to_")


class Wife(Base):
    __tablename__ = "wifes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    rare: Mapped[AllRares] = mapped_column(SQLEnum(AllRares, name="all_rares"), nullable=False)

    wife_imgs: Mapped[str] = mapped_column(String, nullable=False)
    from_: Mapped[str] = mapped_column(String, nullable=False)
    sex: Mapped[Sex] = mapped_column(SQLEnum(Sex, name="sex"), default=Sex.NOT_SETUP)
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_wife_association,
        back_populates="characters"
    )

    slot: Mapped["Slot"] = relationship("Slot", back_populates="wife", uselist=False)

    trades_sent: Mapped[list["Trade"]] = relationship(
        "Trade",
        foreign_keys="Trade.change_from_id",
        back_populates="change_from"
    )

    trades_received: Mapped[list["Trade"]] = relationship(
        "Trade",
        foreign_keys="Trade.change_to_id",
        back_populates="change_to"
    )


class Shop(Base):
    __tablename__ = "shop"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[ShopTypes] = mapped_column(SQLEnum(ShopTypes, name="shop_types"), nullable=False)
    
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    slots: Mapped[list["Slot"]] = relationship("Slot", back_populates="shop")


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    price: Mapped[float] = mapped_column(Numeric(precision=25, scale=2), default=0.00)

    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    selled: Mapped[bool] = mapped_column(Boolean, default=False)

    wife_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wifes.id"), nullable=False)
    shop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("shop.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    seller: Mapped["User"] = relationship("User", back_populates="slots_for_sale")
    wife: Mapped["Wife"] = relationship("Wife", back_populates="slot")
    shop: Mapped["Shop"] = relationship("Shop", back_populates="slots")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    from_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    to_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    change_from_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wifes.id"), nullable=False)
    change_to_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wifes.id"), nullable=False)

    from_: Mapped["User"] = relationship("User", foreign_keys=[from_id], back_populates="sent_trades")
    to_: Mapped["User"] = relationship("User", foreign_keys=[to_id], back_populates="received_trades")

    change_from: Mapped["Wife"] = relationship("Wife", foreign_keys=[change_from_id], back_populates="trades_sent")
    change_to: Mapped["Wife"] = relationship("Wife", foreign_keys=[change_to_id], back_populates="trades_received")

    sucess: Mapped[bool] = mapped_column(Boolean, default=False)


class BannedUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)


class Promo(Base):
    __tablename__ = 'promocodes'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promo: Mapped[str] = mapped_column(String)
    bonus: Mapped[float] = mapped_column(Numeric(precision=25, scale=2), default=0.00)