from sqlalchemy import create_engine
from ryu.app.qos.models import Base
from sqlalchemy.orm import sessionmaker

from ryu.app.qos.models import *

class QoSTracker:

    def __init__(self):
        self.topology = None
        self.engine = create_engine('sqlite:///my_db.db')
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        session = Session()
        Base.metadata.create_all(self.engine)        
        print "HELLO THERE"


    def add_links(self, link_data):
        for link in link_data:
            new_link = QosLink(src_port=link[0], dst_port=link[1], bandwidth=10)

    
    def add_switches(self, switch_data):
        print "***** ADD SWITCHES"
        print switch_data
