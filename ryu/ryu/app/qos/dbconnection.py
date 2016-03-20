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
                                           .where(QoSLink.dst==link_data["dst_port"])).scalar()
        if not exist:
            link = QoSLink(src=link_data["src_port"], dst=link_data["dst_port"],
                           bandwidth=link_data["bw"])
            return self.add_record(link)


    def add_port(self, port):
        exist = self.session.query(exists().where(QoSPort.switch==port.dpid)
                                           .where(QoSPort.port_no==port.port_no)).scalar()
        if not exist:
            port = QoSPort(switch=port.dpid, port_no=port.port_no)
            return self.add_record(port)


    def add_host(self, host_data, port_id):
        exist = self.session.query(exists().where(QoSHost.mac==host_data["mac"])).scalar()
        if not exist:
            host = QoSHost(mac=host_data["mac"], ip=host_data["ip"], port=port_id)
            return self.add_record(host)


    def add_switch(self, switch, host_data):
        exist = self.session.query(exists().where(QoSSwitch.dpid==switch.dp.id)).scalar()
        if not exist:
            qos_switch = QoSSwitch(dpid=switch.dp.id)
            for port in switch.ports:
                port = self.add_port(port)
                print host_data
                if int(port.port_no) in host_data:
                    host = self.add_host(host_data[port.port_no], port.id)
            return self.add_record(qos_switch)


    def add_reservation(self, rsv):
        """
        rsv: dict containing reservation info
        """
        exist = self.session.query(exists().where(QoSReservation.src==rsv["src"])
                                           .where(QoSReservation.dst==rsv["dst"])).scalar()
        if not exist:
            reservation = QoSReservation(src=rsv["src"], dst=rsv["dst"], bw=rsv["bw"])
            return self.add_record(reservation)


    def add_port_reservation(self, prsv):
        """
        prsv: dict containing port reservation info
        """
        exist = self.session.query(exists().where(QoSPortReservation.reservation==prsv["reservation"])
                                           .where(QoSPortReservation.port==prsv["port"])).scalar()
        if not exist:
            p_reservation = QoSPortReservation(port=prsv["port"], reservation=prsv["reservation"])
            return self.add_record(p_reservation)


    def get_all_links(self):
        return self.session.query(QoSLink).all()


    def get_all_switches(self):
        return self.session.query(QoSSwitch).all()


    def get_all_ports(self):
        return self.session.query(QoSPort).all()


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
        return self.session.query(QoSPort).filter(QoSPort.switch==dpid).first()


    def get_ports_for_link(self, link):
        return self.session.query(QoSPort).filter(QoSPort.link==link).first()


    def get_switch_for_port(self, port):
        return self.session.query(QoSSwitch).filter(QoSSwitch.dpid==port.switch).first()


    def get_reservation_for_src_dst(self, src, dst):
        return self.session.query(QoSReservation).filter(QoSReservation.src==src and QoSReservation.dst==dst).first()


    def get_reservation_for_id(self, res_id):
        return self.session.query(QoSReservation).filter(QoSReservation.id==id).first()


    def update_reservation(self, res_id, new_bw):
        res = self.get_reservation_for_id(res_id)
        if not res:
            return None
        res.bw = new_bw
        self.session.commit()
        return res


    def add_record(self, record):
        print "ADDING " + str(record) + " TO DATABASE"
        self.session.add(record)
        self.session.commit()
        return record
