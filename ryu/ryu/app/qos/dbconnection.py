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


    def get_all_links(self):
        return self.session.query(QoSLink).all()


    def add_record(self, record):
        self.session.commit(record)
        return record
