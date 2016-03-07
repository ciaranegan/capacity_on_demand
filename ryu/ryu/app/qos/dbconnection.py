from ryu.app.qos.models import *

from sqlalchemy import create_engine
from sqlalchemy.sql import exists
from ryu.app.qos.models import Base
from sqlalchemy.orm import sessionmaker


class DBConnection:

    def __init__(self, db_path):
        self.engine = create_engine(db_path)
        Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = Session()



    def add_link(self, link_data):
        exist = self.session.query(exists().where(QoSLink.src==link_data["src_port"])
                                            .where(QoSLink.dst==link_data["dst_port"]))
        if not exist:
            link = QoSLink(src=link_data["src_port"].dpid, dst=["dst_port"].dpid,
                           bandwidth=link_data["bw"])
            return self.add_record(link)


    def add_port(self, port):
        exist = self.session.query(exists().where(QoSPort.switch==port.dpid)
                                           .where(QoSPort.port_no==port.port_no))
        if not exist:
            port = QoSPort(switch=port.dpid, port_no=port.port_no)
            return self.session.add_record(port)


    def add_switch(self, switch):
        exist = self.session.query(exists().where(QoSSwitch.dpid==switch.dpid))
        if not exist:
            switch = QoSSwitch(dpid=switch.dpid)
            for port in switch.ports:
                self.add_port(port)
            return self.session.add_record(switch)


    def add_reservation(self, rsv):
        """
        rsv: dict containing reservation info
        """
        exist = self.session.query(exists().where(QoSReservation.src==rsv["src"])
                                           .where(QoSReservation.dst==rsv["src"]))
        if not exist:
            reservation = QoSReservation(src=rsv["src"], dst=rsv["dst"], bw=rsv["bw"])
            return self.session.commit(reservation)


    def add_port_reservation(self, prsv):
        exist = self.session.query(exists().where(QoSPortReservation.reservation==prsv["reservation"])
                                           .where(QoSPortReservation.port==prsv["port"]))
        if not exist:
            p_reservation = QoSPortReservation(port=prsv["port"], reservation=prsv["reservation"])
            return self.session.add_record(p_reservation)


    def get_all_links(self):
        return self.session.query(QoSLink).all()


    def get_all_switches(self):
        return self.session.query(QoSSwitch).all()


    def get_all_ports(self):
        return self.session.query(QoSLink).all()


    def get_all_reservations(self):
        return self.session.query(QoSReservation).all()


    def get_all_port_reservations(self):
        return self.session.query(QoSPortReservation).all()


    def get_port_reservations_for_reservation(self, reservation):
        return self.session.query(QoSPortReservation).filter(QoSPortReservation.reservation==reservation)


    def get_switches_for_reservation(self, reservation):
        port_reservations = self.get_port_reservations_for_reservation(reservation)
        switches = []
        for p_reserve in port_reservations:
            port = p_reserve.port
            switches.append(self.get_switch_for_port)
        return switches


    def get_ports_for_switch(self, dpid):
        return self.session.query(QoSPort).filter(QoSPort.switch==dpid)


    def get_ports_for_link(self, link):
        return self.session.query(QoSPort).filter(QoSPort.link==link)


    def get_switch_for_port(self, port):
        return self.session.query(QoSSwitch).filter(QoSSwitch.dpid==port.switch)


    def add_record(self, record):
        print "ADDING RECORD: " + str(record)
        self.session.execute(record)
        return record
