from ryu.app.qos.models import *


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
            link = QoSLink(src_port=link_data["src_port"], dst_port=["dst_port"],
                           bandwidth=link_data["bw"])
            return self.add_record(link)


    def get_all_links(self):
        return self.session.query(QoSLink).all()


    def add_record(self, record):
        self.session.commit(record)
        return record