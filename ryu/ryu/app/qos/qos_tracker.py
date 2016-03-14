from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection

from ryu.app.qos.test_reservations import get_reservations_for_2_4_topo
class QoSTracker:

    def __init__(self):
        self.topology = None
        self.db = DBConnection('sqlite:///my_db.db')
        test_reservations = get_reservations_for_2_4_topo()
        for res in test_reservations:
            self.db.add_reservation(res)


    def get_all_links(self):
        return self.db.get_all_links()
    
    
    def get_all_switches(self):
        return self.db.get_all_switches()

    
    def get_all_ports(self):
        return self.db.get_all_ports()


    def get_reservation_for_src_dst(self, src, dst):
        return self.db.get_reservation_for_src_dst(src, dst)


    def add_links(self, link_data):
        for link in link_data:
            self.db.add_link({"src_port": link.src.dpid, "dst_port": link.dst.dpid, "bw": 10}) # TODO: fix this

    
    def add_switches(self, switch_data):
        for switch in switch_data:
            self.db.add_switch(switch)
