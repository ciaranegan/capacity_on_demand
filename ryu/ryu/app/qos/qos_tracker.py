from sqlalchemy import create_engine
from ryu.app.qos.models import Base
from sqlalchemy.orm import sessionmaker

from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection


class QoSTracker:

    def __init__(self):
        self.topology = None
        self.db = DBConnection('sqlite:///my_db.db')
        print "HELLO THERE"


    def get_all_links(self):
        return self.db.get_all_links()


    def add_links(self, link_data):
        for link in link_data:
            # new_link = QosLink(src_port=link[0], dst_port=link[1], bandwidth=10)
            db.add_link({"src_port": link[0], "dst_port": link[1], "bw": 10}) # TODO: fix this

    
    def add_switches(self, switch_data):
        print "***** ADD SWITCHES"
        print switch_data
