from enum import Enum
from sqlalchemy import (Column, ForeignKey, Integer, String, create_engine,
                        Float, Boolean)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class QoSSwitch(Base):
    """
    Class to represent a switch.
    """
    __tablename__ = "switch"

    dpid = Column(Integer, primary_key=True)
    ports = relationship("QoSPort")


class QoSPort(Base):
    """
    Class to represent a port.
    """
    __tablename__ = "port"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link = relationship("QoSLink")
    switch = Column(Integer, ForeignKey("switch.dpid"))
    port_no = Column(Integer)
    reservations = relationship("QoSPortReservation")


class QoSLink(Base):
    """
    Class to represent a link between to ports.
    """
    __tablename__ = "link"

    id = Column(Integer, primary_key=True, autoincrement=True)
    src = Column(ForeignKey("switch.id"))
    dst = Column(ForeignKey("switch.id"), nullable=True)
    bandwidth = Column(Integer)


class QoSReservation(Base):
    """
    Class to represent a bandwidth allocation.
    """
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    src = Column(String)
    dst = Column(String)
    bw = Column(Float)
    ports = relationship("QoSPortReservation")


class QoSPortReservation(Base):
    """
    Class to represent an allocation for a specific port.
    """
    __tablename__ = "port_reservation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    port = Column(Integer, ForeignKey("port.id"))
    reservation = Column(Integer, ForeignKey("reservation.id"))
