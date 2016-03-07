from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection


class QoSTracker:

    def __init__(self):
        self.topology = None
        self.db = DBConnection('sqlite:///my_db.db')
        print "HELLO THERE"


    def get_all_links(self):
        return self.db.get_all_links()
    
    
    def get_all_switches(self):
        return self.db.get_all_switches()


    def add_links(self, link_data):
        for link in link_data:
            print "-----------------------------"
            print link.src
            print link.dst
            print "-----------------------------"
            # new_link = QosLink(src_port=link[0], dst_port=link[1], bandwidth=10)
            self.db.add_link({"src_port": link.src.dpid, "dst_port": link.dst.dpid,
                "bw": 10}) # TODO: fix this

    
    def add_switches(self, switch_data):
        print "***** ADD SWITCHES"
        print switch_data

        for switch in switch_data:
            print switch
            self.db.add_switch(switch)
