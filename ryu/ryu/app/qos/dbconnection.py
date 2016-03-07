from ryu.app.qos.models import *

from sqlalchemy import create_engine
from ryu.app.qos.models import Base
from sqlalchemy.orm import sessionmaker


class DBConnection:

    def __init__(self, db_path):
        self.engine = create_engine(db_path)
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)


    def add_link(self, link_data):
        exists = self.session.query(QoSLink).filter(QoSLink.src_port==link_data["src_port"].dpid \
                                    and QoSLink.dst_port==link_data["dst_port"].dpid).exists()
        if not exists:
            link = QoSLink(src=link_data["src_port"].dpid, dst=["dst_port"].dpid,
                           bandwidth=link_data["bw"])
            return self.add_record(link)


    def add_port(self, port):
        exists = self.session.query(QoSPort).filter(QoSPort.switch==port.dpid \
                                    and QoSPort.port_no==port.port_no).exists()
        if not exists:
            port = QoSPort(switch=port.dpid, port_no=port.port_no)
            return self.session.add_record(port)


    def add_switch(self, switch):
        exists = self.session.query(QoSSwitch).filter(QoSSwitch.dpid==switch.dpid).exists()
        if not exists:
            switch = QoSSwitch(dpid=switch.dpid)
            return self.session.add_record(switch)


    def add_reservation(self, rsv):
        """
        rsv: dict containing reservation info
        """
        exists = self.session.query(QoSReservation).filter(QoSReservation.src==rsv["src"] \
                                    and QoSReservation.dst==rsv["dst"]).exists()
        if not exists:
            reservation = QoSReservation(src=rsv["src"], dst=rsv["dst"], bw=rsv["bw"])
            return self.session.commit(reservation)


    def add_port_reservation(self, prsv):
        exists = self.session.query(QoSPortReservation).filter(
                    QoSPortReservation.reservation==prsv["reservation"] \
                    and QoSPortReservation.port==prsv["port"]).exists()
        if not exists:
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
        self.session.commit(record)
        return record
