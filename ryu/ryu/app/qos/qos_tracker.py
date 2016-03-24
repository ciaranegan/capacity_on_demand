import requests
import json

from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection

from ryu.app.qos.test_reservations import get_reservations_for_2_4_topo

from IPython import embed

LOCALHOST = "http://0.0.0.0:8080"
ADD_FLOW_URI = "/stats/flowentry/add"
GET_FLOWS_URI = "/stats/flow/{}"
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
        flows = self.get_flows_for_switch(switch)
        nearby_hosts = self.db.get_hosts_for_switch(switch.dpid)
        for host in nearby_hosts:
            out_port = self.db.get_port_for_host(host)
            for other_host in nearby_hosts:
                if other_host != host:
                    print "ADDING FLOW FOR " + str(host.ip) + " to " + str(other_host.ip)
                    params = {
                        "dpid": int(switch.dpid),
                        "match": {
                            "eth_dst": host.mac,
                            "in_port": other_host.port
                        },
                        "priority": 1,
                        "actions": [{
                            "type": "OUTPUT",
                            "port": out_port.port_no
                        }]
                    }
                    self.add_flow(params)

        self.get_flows_for_switch(switch)
        nearby_ips = [str(h.ip) for h in nearby_hosts]
        all_hosts = self.db.get_all_hosts()
        for ip in nearby_ips:
            for host in all_hosts:
                if ip != host.ip:
                    path = self.get_route_to_host(host.ip, switch)
                    if path:
                        if len(path) > 1:
                            prev_switch = switch
                            for i in range(1, len(path)):
                                if prev_switch.dpid != path[i].dpid:
                                    self.db.get_out_port_between_switches(prev_switch, path[i], SWITCH_MAP)
                        else:
                            print "LOCALHOST: " + str(host.ip)


        # TODO: add non-local flow entries

    def add_switches(self, switch_data):
        for switch in switch_data:
            if str(switch.dp.id) in HOST_MAP:
                s = self.db.add_switch(switch, HOST_MAP[str(switch.dp.id)])

        switches = self.db.get_all_switches()
        for switch in switches:
            self.init_flows(switch, SWITCH_MAP)

    def add_flow(self, params):
        response = requests.post(LOCALHOST+ADD_FLOW_URI, data=json.dumps(params))

    def get_flows_for_switch(self, switch):
        response = requests.get((LOCALHOST+GET_FLOWS_URI).format(str(switch.dpid)))

    def get_route_to_host(self, dst_ip, switch, prev_switch=None):
        # TODO: account for cycles
        # TODO: check for other topologies
        # Check if host is already connected to the switch
        hosts = self.db.get_hosts_for_switch(switch.dpid)
        if dst_ip in [host.ip for host in hosts]:
            # We've found our host
            for h in hosts:
                if h.ip == dst_ip:
                    return [switch]

        # Get any connected switches
        if prev_switch:
            neighbours = self.db.get_switch_neighbours(switch.dpid, exclude=prev_switch)
        else:
            neighbours = self.db.get_switch_neighbours(switch.dpid)

        if len(neighbours) <= 0:
            return None

        for n in neighbours:
            route = self.get_route_to_host(dst_ip, n, switch)
            print route
            if route is not None:
                route.insert(0, switch)
                print route
                break

        return route
