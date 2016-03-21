from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection

from ryu.app.qos.test_reservations import get_reservations_for_2_4_topo

s0_DPID = "16"
s1_DPID = "32"

# Mapping of port numbers to mac addresses
TOPO_MAP = {
    s0_DPID: {
        2: {
            "mac": '00:00:00:00:00:02',
            "ip": '10.0.0.2'
        },
        1: {
            "mac": '00:00:00:00:00:01',
            "ip": '10.0.0.1'
        }
    },
    s1_DPID: {
        1: {
            "mac": '00:00:00:00:00:03',
            "ip": '10.0.0.3'
        },
        2: {
            "mac": '00:00:00:00:00:04',
            "ip": '10.0.0.4'
        }
    }
}


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
            # TODO: fix this
            self.db.add_link({
                "src_port": link.src.dpid,
                "dst_port": link.dst.dpid,
                "bw": 10
            })

    def add_switches(self, switch_data):
        for switch in switch_data:
            if str(switch.dp.id) in TOPO_MAP:
                self.db.add_switch(switch, TOPO_MAP[str(switch.dp.id)])
                # TODO: at this point, flow entries should be added. Hopefully
                # using REST interface.

    def get_route_to_host(self, dst_ip, switch):
        # TODO: account for cycles
        # Check if host is already connected to the switch
        hosts = self.db.get_hosts_for_switch(switch.dpid)
        if dst_ip in [host.ip for host in hosts]:
            # We've found our host
            for h in hosts:
                if h.dst == dst_ip:
                    host = h
            return [h, switch]
        # Get any connected switches
        neighbours = self.db.get_switch_neighbours(switch)
        if len(neighbours) > 0:
            for neighbour in neighbours:
                route = self.get_route_to_host(dst_ip, neighbour)
                if route is not None:
                    return route.append(switch)
        return None
