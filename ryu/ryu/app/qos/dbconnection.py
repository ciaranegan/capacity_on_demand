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
        exists = self.session.query(QoSLink).filter(QoSLink.src_port==link_data["src_port"] \
                                    and QoSLink.dst_port==link_data["dst_port"]).exists()
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


    def get_all_links(self):
        return self.session.query(QoSLink).all()


    def get_all_switches(self):
        return self.session.query(QoSSwitch).all()


    def get_all_ports(self):
        return self.session.query(QoSLink).all()


    def get_ports_for_switch(self, dpid):
        return self.session.query(QoSPort).filter(QoSPort.switch==dpid)


    def get_ports_for_link(self, link):
        return self.session.query(QoSPort).filter(QoSPort.link==link)


    def add_record(self, record):
        self.session.commit(record)
        return record
