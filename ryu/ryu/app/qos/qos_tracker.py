import requests
import json

from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection

from ryu.app.qos.test_reservations import get_reservations_for_2_4_topo

from IPython import embed

ADD_FLOW_URI = "/stats/flowentry/add"
LOCALHOST = "http://0.0.0.0:8080"

s0_DPID = "16"
s1_DPID = "32"

# Mapping of port numbers to mac addresses
HOST_MAP = {
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

# Mapping of links to port_nos and their bandwidth
SWITCH_MAP = {
    s0_DPID: {
        3: {
            "dpid": s1_DPID,
            "bw": 3
        }
    },
    s1_DPID: {
        3: {
            "dpid": s0_DPID,
            "bw": 3
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

    def get_reservation_for_src_dst(self, src, dst):
        return self.db.get_reservation_for_src_dst(src, dst)

    def get_switch_for_dpid(self, dpid):
        return self.db.get_switch_for_dpid(dpid)

    def add_links(self, link_data):
        for link in link_data:
            # TODO: fix this
            self.db.add_link({
                "src_port": link.src.dpid,
                "dst_port": link.dst.dpid,
                "bw": 10
            })

    def update_flows(self):
        # TODO: udpates all switch flow tables
        pass

    def init_flows(self, switch, switch_map):
        nearby_hosts = self.db.get_hosts_for_switch(switch.dpid)
        for host in nearby_hosts:
            # TODO: Add local flow entries
            out_port = self.db.get_port_for_host(host)
            print out_port
            print host
            params = {
                "dpid": int(switch.dpid),
                "match": {
                    "nw_dst": host.ip
                },
                "actions": [{
                    "type": "OUTPUT",
                    "port": out_port.port_no
                }]
            }
            self.add_flow(params)

        nearby_ips = [str(h.ip) for h in nearby_hosts]
        all_hosts = self.db.get_all_hosts()
        hosts = []
        for h in all_hosts:
            if h.ip not in nearby_ips:
                hosts.append(h)
                # TODO: add non-local flow entries

    def add_switches(self, switch_data):
        for switch in switch_data:
            if str(switch.dp.id) in HOST_MAP:
                s = self.db.add_switch(switch, HOST_MAP[str(switch.dp.id)])
                # TODO: at this point, flow entries should be added. Hopefully
                # using REST interface.
                self.init_flows(s, SWITCH_MAP)

        switches = self.db.get_all_switches()
        for switch in switches:
            self.init_flows(switch, SWITCH_MAP)

    def add_flow(self, params):
        request = requests.post(LOCALHOST+ADD_FLOW_URI, data=json.dumps(params))
        print request.content

    def get_route_to_host(self, dst_ip, switch, prev_switch=None):
        # TODO: account for cycles
        # TODO: check for other topologies
        # Check if host is already connected to the switch
        hosts = self.db.get_hosts_for_switch(switch.dpid)
        if dst_ip in [host.ip for host in hosts]:
            # We've found our host
            for h in hosts:
                if h.ip == dst_ip:
                    return [h, switch]

        # Get any connected switches
        if prev_switch:
            neighbours = self.db.get_switch_neighbours(switch.dpid, exclude=prev_switch)
        else:
            neighbours = self.db.get_switch_neighbours(switch.dpid)

        if len(neighbours) <= 0:
            return None

        for n in neighbours:
            route = self.get_route_to_host(dst_ip, n, switch)
            if route is not None and type(route[0]) is QoSHost:
                route.append(switch)
                break

        if route:
            return route
        else:
            return None
