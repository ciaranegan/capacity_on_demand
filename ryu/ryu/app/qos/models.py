from enum import Enum
from sqlalchemy import (Column, ForeignKey, Integer, String, create_engine,
                        Float, Enum)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

INGRESS = "ingress"
EGRESS = "egress"


class QoSReservation(Base):
    """
    Class to represent a bandwidth allocation.
    """
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True, auto_increment=True)
    src = Column(String)
    dst = Column(String)
    bw = Column(Float)
    switches = relationship("QoSSwitch")


class QoSPortReservation:
    """
    Class to represent an allocation for a specific port.
    """
    __tablename__ = "port_reservation"

    id = Column(Integer, primary_key=True, auto_increment=True)
    port = Column(Integer, ForeignKey("port.id"))
    bw = Column(Integer)
    reservation = Column(Integer, ForeignKey("reservation.id"))


class QoSSwitch:
    """
    Class to represent a switch.
    """
    __tablename__ = "switch"

    TYPE = Enum(INGRESS, EGRESS)

    dpid = Column(Integer, primary_key=True)
    switch_type = Column(ENUM(*TYPE), default=TYPE.EGRESS)
    ports = relationship("QoSPort")


class QoSPort:
    """
    Class to represent a port.
    """
    __tablename__ = "port"

    TYPE = Enum(INGRESS, EGRESS)

    id = Column(Integer, primary_key=True, auto_increment=True)
    link = relationship("QoSLink")
    switch = Column(Integer, ForeignKey("switch.dpid"))
    port_no = Column(Integer)
    port_type = Column(Enum(*TYPE), default=TYPE.EGRESS)
    reservations = relationship("QoSPortReservation")
    

class QoSLink:
	"""
	Class to represent a link between to ports.
	"""
	__tablename__ = "link"

	id = Column(Integer, primary_key=True, auto_increment=True)
	src_port = Column(ForeignKey("port.id"))
	dst_port = Column(ForeignKey("port.id"))
	bandwidth = Column(Integer)
