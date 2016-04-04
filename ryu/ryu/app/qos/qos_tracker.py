import requests
import json

from ryu.app.qos.models import *
from ryu.app.qos.dbconnection import DBConnection

from ryu.topology.api import get_all_switch, get_all_link, get_switch

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

    def __init__(self, ryu_app):
        self.ryu_app = ryu_app
        self.db = DBConnection('sqlite:///my_db.db')
        self._current_mpls_label = 0

    def get_reservation_for_src_dst(self, src, dst):
        return self.db.get_reservation_for_src_dst(src, dst)

    def get_switch_for_dpid(self, dpid):
        return self.db.get_switch_for_dpid(dpid)

    def generate_mpls_label(self):
        self._current_mpls_label += 1
        return self._current_mpls_label

    def add_links(self, link_data):
        # TODO: Not great way to do this
        for link in link_data:
            bw = SWITCH_MAP[str(link.src.dpid)][3]["bw"]
            self.db.add_link({
                "src_port": link.src.dpid,
                "dst_port": link.dst.dpid,
                "bw": bw
            })

    def update_flows(self):
        # TODO: udpates all switch flow tables
        pass

    def refresh_flows(self):
        switches = self.db.get_all_switches()
        for s in switches:
            self.init_flows(s, SWITCH_MAP)

    def init_flows(self, switch, switch_map):
        # TODO: test on different topology!!!!!
        nearby_hosts = self.db.get_hosts_for_switch(switch.dpid)
        for host in nearby_hosts:
            out_port = self.db.get_port_for_host(host)
            for other_host in nearby_hosts:
                if other_host.ip != host.ip:
                    ryu_switch = self.get_ryu_switch_for_dpid(switch.dpid)
                    datapath = ryu_switch.dp
                    parser = datapath.ofproto_parser

                    match = parser.OFPMatch(eth_dst=host.mac)
                    actions = [parser.OFPActionOutput(out_port.port_no)]
                    self.add_flow(ryu_switch.dp, 1, match, actions)

                    match = parser.OFPMatch(arp_tpa=host.ip)
                    actions = [parser.OFPActionOutput(out_port.port_no)]
                    self.add_flow(ryu_switch.dp, 1, match, actions)

        nearby_ips = [str(h.ip) for h in nearby_hosts]
        all_hosts = self.db.get_all_hosts()
        for near_host in nearby_hosts:
            for host in all_hosts:
                if host.ip not in nearby_ips:
                # For all hosts except the local ones
                    path = self.get_route_to_host(host.ip, switch)
                    # Find a path to the host
                    if path and len(path) > 1:
                        prev_switch = path[0]
                        for i in range(1, len(path)):
                            in_port = self.db.get_in_port_no_between_switches(prev_switch, path[i], SWITCH_MAP)
                            if i == len(path) - 1:
                                out_port = self.db.get_port_for_id(host.port).port_no
                            else:
                                out_port = self.db.get_out_port_no_between_switches(prev_switch, path[i], SWITCH_MAP)

                            ryu_switch = self.get_ryu_switch_for_dpid(path[i].dpid)
                            datapath = ryu_switch.dp
                            parser = datapath.ofproto_parser

                            match = parser.OFPMatch(eth_dst=host.mac)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(ryu_switch.dp, 1, match, actions)

                            match = parser.OFPMatch(ipv4_dst=host.ip)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(ryu_switch.dp, 1, match, actions)

                            params = {
                                "dpid": int(path[i].dpid),
                                "match": {
                                    "arp_tpa": host.ip,
                                    "eth_type": 2054
                                },
                                "priority": 1,
                                "actions": [{
                                    "type": "OUTPUT",
                                    "port": out_port
                                }]
                            }
                            self.add_rest_flow(params)

                            # match = parser.OFPMatch(arp_tpa=host.ip)
                            # actions = [parser.OFPActionOutput(out_port)]
                            # self.add_flow(ryu_switch.dp, 1, match, actions)

                            prev_switch = path[i]

    def add_switches(self, switch_data):
        for switch in switch_data:
            if str(switch.dp.id) in HOST_MAP:
                s = self.db.add_switch(switch, HOST_MAP[str(switch.dp.id)])

        switches = self.db.get_all_switches()
        for switch in switches:
            self.init_flows(switch, SWITCH_MAP)

    def add_rest_flow(self, params):
        response = requests.post(LOCALHOST+ADD_FLOW_URI, data=json.dumps(params))

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        print "ADDING FLOW FOR DPID: " + str(datapath.id) + " MATCH: " + str(match) + " ACTIONS: " + str(actions)
        self.ryu_app.add_flow(datapath, priority, match, actions, buffer_id)

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
            if route is not None:
                route.insert(0, switch)
                break

        return route

    def add_reservation(self, rsv):
        """
        rsv: dict containing reservation info
        """
        reservation = self.db.add_reservation(rsv)

        in_port = self.db.get_port_for_id(reservation.in_port)
        in_switch = self.db.get_switch_for_port(in_port)
        out_port = self.db.get_port_for_id(reservation.out_port)
        out_switch = self.db.get_switch_for_port(out_port)

        path = self.get_route_to_host(rsv["dst"], in_switch)

        if not path:
            print "BAD: NO PATH TO HOST"
            return

        if len(path) <= 1:
            print "1 Switch"

        else:
            in_port_reservation = self.db.add_port_reservation(reservation.id, in_port.id)
            out_port_reservation = self.db.add_port_reservation(reservation.id, out_port.id)
            for i in range(1, len(path) - 1):
                print i
                print path[i]
            self.add_ingress_mpls_rule(in_port, reservation.mpls_label,
                reservation.src, reservation.dst)
            # TODO: Add flow to remove MPLS lable to out_port


    def add_ingress_mpls_rule(self, port, mpls_label, src_ip, dst_ip):
        switch = self.db.get_switch_for_port(port)
        ryu_switch = self.get_ryu_switch_for_dpid(switch.dpid)
        datapath = ryu_switch.dp
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(ipv4_src=src_ip, ipv4_dst=dst_ip)
        actions = [parser.OFPActionPushMpls(),
            parser.OFPActionSetField(mpls_label=mpls_label)]
        self.add_flow(datapath, 1, match, actions)

    def add_egress_mpls_rule(self, port, mpls_label, src_ip, dst_ip):
        switch = self.db.get_switch_for_port(port)
        ryu_switch = self.get_ryu_switch_for_dpid(switch.dpid)
        datapath = ryu_switch.dp
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(ipv4_src=src_ip, ipv4_dst=dst_ip)
        actions = [parser.OFPActionPopMpls()]
        self.add_flow(datapath, 1, match, actions)

    def get_ryu_switch_for_dpid(self, dpid):
        switch = get_switch(self.ryu_app, dpid=int(dpid))
        # switches = get_all_switch(self.ryu_app)
        # print "GOODBYE"
        # print "GET_RYU_SWITCH: " + str(switch)
        return switch[0]
