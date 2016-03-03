from sqlalchemy import create_engine
from ryu.app.qos.models import Base
from sqlalchemy.orm import sessionmaker

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
        print "*****ADD LINKS"
        print link_data

    
    def add_switches(self, switch_data):
        print "***** ADD SWITCHES"
        print switch_data
