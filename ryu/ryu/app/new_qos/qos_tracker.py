import requests
import json
import struct
import time
import threading

from ryu.app.new_qos.models import *
from ryu.app.new_qos.dbconnection import DBConnection
from ryu.topology.api import get_all_switch, get_all_link, get_switch
from ryu.ofproto import ether
from ryu.lib.ip import ipv4_to_bin
from IPython import embed

# LOCALHOST = "http://0.0.0.0:8080"
LOCALHOST = "http://localhost:8080"
CONF_SWITCH_URI = "/v1.0/conf/switches/"
QOS_QUEUES_URI = "/qos/queue/"
QOS_RULES_URI = "/qos/rules/"

s0_DPID = "16"
s1_DPID = "32"
s2_DPID = "48"

PIR_TABLE_ID = 0
CIR_TABLE_ID = 1
FLOW_TABLE_ID = 2

PORT_NAME_STR = "s{}-eth{}"

SWITCH_NUMBER_TABLE = {
    s0_DPID: 0,
    s1_DPID: 1,
    s2_DPID: 2
}

OVS_LINK_TYPE = "linux-htb"

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
    },
    s2_DPID: {
    }
}

SWITCH_LOOKUP = {
    s0_DPID: "0000000000000010",
    s1_DPID: "0000000000000020",
    s2_DPID: "0000000000000030"
}

BEST_EFFORT_QUEUE_ID = 0
HIGH_PRIORITY_QUEUE_ID = 1

# Mapping of links to port_nos and their bandwidth
SWITCH_MAP = {
    s0_DPID: { # DPID: 16
        3: {
            "dpid": s2_DPID,
            "bw": 1000000
        }
    },
    s1_DPID: { # DPID: 32
        3: {
            "dpid": s2_DPID,
            "bw": 1000000
        }
    },
    s2_DPID: {
        1: {
            "dpid": s0_DPID,
            "bw": 1000000
        },
        2: {
            "dpid": s1_DPID,
            "bw": 1000000
        }
    }
}

OVSDB_ADDR = "tcp:127.0.0.1:6632"

class QoSTracker:

    def __init__(self, ryu_app):
        self.ryu_app = ryu_app
        self.db = DBConnection('sqlite:///my_db.db')
        self._current_mpls_label = 0
        self._flows_added = 0
        t = threading.Thread(target=self.delayed_start)
        t.start()

    def get_port_name_for_port_no(self, port_no, dpid):
        switch_no = str(SWITCH_NUMBER_TABLE[str(dpid)])
        return PORT_NAME_STR.format(switch_no, port_no)

    def delayed_start(self):
        time.sleep(5)
        self.start()

    def start(self):
        self.db.delete_reservations()
        self.db.delete_queues()
        switches = self.db.get_all_switches()
        for switch in switches:
            self.put_ovsdb_addr(switch.dpid, OVSDB_ADDR)

        reservation = {
            "src": "10.0.0.4",
            "dst": "10.0.0.1",
            "bw": 750000 
        }
        self.add_reservation_1(reservation)

    def add_egress_port_queue(self, switch, port_no, queues, max_bw):
        switch_id = self.get_switch_id_for_dpid(switch.dpid)
        port_name = self.get_port_name_for_port_no(port_no, switch.dpid)
      
        data = {
            "port_name": port_name,
            "type": OVS_LINK_TYPE,
            "max_rate": str(max_bw),
            "queues": queues
        }
        url = LOCALHOST + QOS_QUEUES_URI + switch_id
        request = requests.post(url, data=json.dumps(data))
        print "Egress port request returned: " + str(request.text)

    def add_port_queue(self, switch, port_no, queues):
        switch_id = self.get_switch_id_for_dpid(switch.dpid)
        port_name = self.get_port_name_for_port_no(port_no, switch.dpid)
        print "PORT NAME: " + str(port_name)

        for queue in queues:
            if "max_rate" in queue:
                max_rate = queue["max_rate"]
            else:
                max_rate = None
            if "min_rate" in queue:
                min_rate = queue["min_rate"]
            else:
                min_rate = None
    #        queue = self.db.add_queue(port, HIGH_PRIORITY_QUEUE_ID,
    #            max_rate=max_rate, min_rate=min_rate)

            data = {
                "port_name": port_name,
                "type": OVS_LINK_TYPE,
                "max_rate": str(max_rate),
                "queues": queues
            }

            url = LOCALHOST + QOS_QUEUES_URI + switch_id
            request = requests.post(url, data=json.dumps(data))
            print "Request returned(port_queue_init): " + str(request.text)

    def get_max_bw_for_topo(self):
        links = self.db.get_all_links()
        max_bw = 0
        for link in links:
            max_bw = max(max_bw, link.bandwidth)
        return max_bw

    def put_ovsdb_addr(self, dpid, ovsdb_addr):
        switch_id = self.get_switch_id_for_dpid(dpid)
        url = LOCALHOST + CONF_SWITCH_URI + switch_id + "/ovsdb_addr"
        r = requests.put(url, data=json.dumps(ovsdb_addr))

    def get_switch_id_for_dpid(self, dpid):
        return SWITCH_LOOKUP[str(dpid)]

    def get_reservation_for_src_dst(self, src, dst):
        return self.db.get_reservation_for_src_dst(src, dst)

    def get_switch_for_dpid(self, dpid):
        return self.db.get_switch_for_dpid(dpid)

    def generate_mpls_label(self):
        self._current_mpls_label += 1
        return self._current_mpls_label

    def get_bw_for_src_dst(self, src, dst):
        src_map = SWITCH_MAP[str(src)]
        for port in src_map:
            if str(SWITCH_MAP[str(src)][port]["dpid"]) == str(dst):
                return SWITCH_MAP[str(src)][port]["bw"]

    def add_links(self, link_data):
        # TODO: Not great way to do this
        for link in link_data:
            bw = self.get_bw_for_src_dst(link.src.dpid, link.dst.dpid)
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
                    self.add_flow(ryu_switch.dp, 2, match, actions, FLOW_TABLE_ID)

                    match = parser.OFPMatch(arp_tpa=host.ip, eth_type=2054)
                    actions = [parser.OFPActionOutput(out_port.port_no)]
                    self.add_flow(ryu_switch.dp, 2, match, actions, FLOW_TABLE_ID)

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
                            if i == len(path) - 1:
                                out_port = self.db.get_port_for_id(host.port).port_no
                            else:
                                out_port = self.db.get_out_port_no_between_switches(path[i], path[i+1], SWITCH_MAP)
                            ryu_switch = self.get_ryu_switch_for_dpid(path[i].dpid)
                            datapath = ryu_switch.dp
                            parser = datapath.ofproto_parser

                            match = parser.OFPMatch(eth_dst=host.mac)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(ryu_switch.dp, 2, match, actions, FLOW_TABLE_ID)

                            match = parser.OFPMatch(ipv4_dst=host.ip, eth_type=2048)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(ryu_switch.dp, 2, match, actions, FLOW_TABLE_ID)

                            match = parser.OFPMatch(arp_tpa=host.ip, eth_type=2054)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(ryu_switch.dp, 2, match, actions, FLOW_TABLE_ID)

                            prev_switch = path[i]

    def add_switches(self, switch_data):
        for switch in switch_data:
            s = self.db.add_switch(switch, HOST_MAP[str(switch.dp.id)])

        switches = self.db.get_all_switches()
        #for switch in switches:
        #    self.init_flows(switch, SWITCH_MAP)

    def add_flow(self, datapath, priority, match, actions, table_id, buffer_id=None):
        self._flows_added += 1
        print "ADDING FLOW FOR: dpid=" + str(datapath.id) + " actions=" + str(actions) + " match=" + str(match)
        self.ryu_app.add_flow(datapath, priority, match, actions, buffer_id)

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
        reservation = self.db.add_reservation(rsv, self.generate_mpls_label())

        in_port = self.db.get_port_for_id(reservation.in_port)
        in_switch = self.db.get_switch_for_port(in_port)
        out_port = self.db.get_port_for_id(reservation.out_port)
        out_switch = self.db.get_switch_for_port(out_port)

        path = self.get_route_to_host(rsv["dst"], in_switch)

        total_bw = self.get_max_bandwidth_for_path(path)

        available_bw = self.get_available_bandwidth_for_path(path)
        if not path or len(path) <= 1:
            return
        else:
            in_port_reservation = self.db.add_port_reservation(reservation.id, in_port.id)
            out_port_reservation = self.db.add_port_reservation(reservation.id, out_port.id)

            in_switch_out_port_no = self.db.get_out_port_no_between_switches(in_switch, path[1], SWITCH_MAP)
            print "^^^^^^^^^^^^^^ Out port no returned: " + str(in_switch_out_port_no) + " should be 3"
            self.add_ingress_mpls_rule(in_port, in_switch_out_port_no,
                reservation.mpls_label, reservation.src, reservation.dst)

            out_switch_in_port_no = self.db.get_in_port_no_between_switches(path[len(path) - 2], out_switch, SWITCH_MAP)
            out_switch_in_port = self.db.get_port_for_port_no(out_switch_in_port_no, out_switch.dpid)

            last_port = self.db.get_port_for_id(out_port_reservation.port)
            self.add_egress_mpls_rule(out_switch, last_port.port_no,
                reservation.mpls_label, reservation.src, reservation.dst)

            # TODO: remove this
            # max_bw = self.get_max_bw_for_topo()
            max_bw = 500
            queues = [{"max_rate": str(max_bw)}, {"min_rate": str(reservation.bw)}]
            in_switch_out_port = self.db.get_port_for_port_no(in_switch_out_port_no, in_switch.dpid)
            print "^^^^^^^^^^^^^^^^ in_switch_out_port_no: " + str(in_switch_out_port.port_no) + " should be 3"
            self.add_port_queue(in_switch, in_switch_out_port_no, queues)
            
            self.add_queue_flow(in_switch, in_port, reservation.src, reservation.dst)
            

            # Add flow to port on the way out.
            for i in range(1, len(path) - 1):
                # TODO: change this to include all switches
                ryu_switch = self.get_ryu_switch_for_dpid(path[i].dpid)
                dp = ryu_switch.dp
                parser = dp.ofproto_parser

                in_port_no = self.db.get_in_port_no_between_switches_1(path[i-1], path[i], SWITCH_MAP)
                in_port = self.db.get_port_for_port_no(in_port_no, path[i].dpid)

                out_port = self.db.get_out_port_no_between_switches(path[i], path[i+1], SWITCH_MAP)
                eth_MPLS = ether.ETH_TYPE_MPLS

                nw_src = struct.unpack('!I', ipv4_to_bin(reservation.src))[0]
                nw_dst = struct.unpack('!I', ipv4_to_bin(reservation.dst))[0]
                # match = parser.OFPMatch(mpls_label=reservation.mpls_label, eth_type=eth_MPLS)
                eth_IP = ether.ETH_TYPE_IP
                match = parser.OFPMatch(eth_type=eth_IP, ipv4_dst=nw_dst, ipv4_src=nw_src)
                # match.set_dl_type(eth_MPLS)
                # match.set_mpls_label(reservation.mpls_label)

                actions = [parser.OFPActionOutput(out_port)]
                    # parser.OFPActionOutput(dp.ofproto.OFPP_CONTROLLER)]

                out_p = self.db.get_port_for_port_no(out_port, path[i].dpid)
                # self.add_flow(dp, 3, match, actions, table_id=FLOW_TABLE_ID)
                self.add_port_queue(path[i], out_p.port_no, queues)
                self.add_queue_flow(path[i], in_port, reservation.src, reservation.dst)
                print "**** Mid-path switch: dpid=" + str(path[i].dpid) + " in_port=" + str(in_port_no) + " out_port=" + str(out_port)

            in_port_no = self.db.get_in_port_no_between_switches(path[-1], path[-2], SWITCH_MAP)
            in_port = self.db.get_port_for_port_no(in_port_no, path[i].dpid)
            self.add_queue_flow(path[-1], in_port, reservation.src, reservation.dst)
            self.add_port_queue(path[-1], in_port.port_no, queues)

    def add_reservation_1(self, rsv):
        print "Adding reservation"
        reservation = self.db.add_reservation(rsv, self.generate_mpls_label())

        in_port = self.db.get_port_for_id(reservation.in_port)
        in_switch = self.db.get_switch_for_port(in_port)

        last_port = self.db.get_port_for_id(reservation.out_port)
        last_switch = self.db.get_switch_for_port(last_port)

        path = self.get_route_to_host(rsv["dst"], in_switch)

        total_bw = self.get_max_bandwidth_for_path(path)
        print "Total Bandwidth: " + str(total_bw)
        available_bw = self.get_available_bandwidth_for_path(path)

        if not path or len(path) <= 1:
            return
        else:
            in_port_reservation = self.db.add_port_reservation(reservation.id, in_port.id)
            # TODO: this is stupid
            last_port_reservation = self.db.add_port_reservation(reservation.id, last_port.id)
            
            # Get the out port of the first switch and add the ingress rule
            first_switch_out_port_no = self.db.get_out_port_no_between_switches(in_switch, path[1], SWITCH_MAP)
            self.add_ingress_rules(in_switch, first_switch_out_port_no, reservation.src, reservation.dst, reservation.bw, total_bw)

            for i in range(1, len(path) - 1):
                in_port_no = self.db.get_in_port_no_between_switches_1(path[i-1], path[i], SWITCH_MAP)
                in_port = self.db.get_port_for_port_no(in_port_no, path[i].dpid)

                out_port_no = self.db.get_out_port_no_between_switches(path[i], path[i+1], SWITCH_MAP)
                self.add_switch_rules(path[i], out_port_no, reservation.src, reservation.dst, reservation.bw, total_bw)

        in_port_no = self.db.get_in_port_no_between_switches_1(path[-1], path[-2], SWITCH_MAP)
        in_port = self.db.get_port_for_port_no(in_port_no, path[i].dpid)
        out_port = self.db.get_port_for_id(reservation.out_port)
        self.add_switch_rules(path[-1], out_port.port_no, reservation.src, reservation.dst, reservation.bw, total_bw)

    def add_queue_flow(self, switch, port, src, dst, queue_id=HIGH_PRIORITY_QUEUE_ID):
        switch_id = self.get_switch_id_for_dpid(switch.dpid)
        data = {
            "match": {
                "nw_dst": dst,
                "nw_src": src,
                "nw_proto": "UDP"
        #        "dl_type": "IPv4"
            },
            "actions": {
                "queue": queue_id
            }
        }
        url = LOCALHOST + QOS_RULES_URI + switch_id
        request = requests.post(url, data=json.dumps(data))
        print "Request returned(queue_init): " + str(request.text)

    def add_ingress_queue_rules(self, switch, in_port, src_ip, dst_ip, bw, max_bw):
        pass

    def add_internal_node_queue_rules(self, switch, in_port, mpls_label, bw):
        pass

    def add_packet_checking_flow(self, switch):
        switch_id = self.get_switch_id_for_dpid(switch.dpid)
        data = {
            "match": {
                "ip_dscp": "26"
            },
            "actions": {
                "queue": "1"
            }
        }
        url = LOCALHOST + QOS_RULES_URI + switch_id
        request = requests.post(url, data=json.dumps(data))
        print "Packet checking request returned: " + str(request.text)

    def add_packet_marking_flow(self, switch, src, dst):
        switch_id = self.get_switch_id_for_dpid(switch.dpid)
        data = {
            "match": {
                "nw_dst": dst,
                "nw_src": src,
                "nw_proto": "UDP"
            },
            "actions": {
                "mark": "26",
                "queue": "1"
            }
        }
        url = LOCALHOST + QOS_RULES_URI + switch_id
        request = requests.post(url, data=json.dumps(data))
        print "Packet marking request returned: " + str(request.text)

    def add_ingress_rules(self, switch, out_port_no, src_ip, dst_ip, bw, max_bw):
        # Add queues
        queues = [{"max_rate": str(max_bw)}, {"min_rate": str(bw)}]
        self.add_egress_port_queue(switch, out_port_no, queues, max_bw)

        # Mark the packets on their way in
        self.add_packet_marking_flow(switch, src_ip, dst_ip)

    def add_switch_rules(self, switch, out_port_no, src_ip, dst_ip, bw, max_bw):
        # Add queues
        queues = [{"max_rate": str(max_bw)}, {"min_rate": str(bw)}]
        self.add_egress_port_queue(switch, out_port_no, queues, max_bw)

        self.add_packet_checking_flow(switch)

    def add_ingress_mpls_rule(self, in_port, out_port_no, mpls_label, src_ip, dst_ip):
        switch = self.db.get_switch_for_port(in_port)
        ryu_switch = self.get_ryu_switch_for_dpid(switch.dpid)
        dp = ryu_switch.dp
        parser = dp.ofproto_parser

        eth_IP = ether.ETH_TYPE_IP
        eth_MPLS = ether.ETH_TYPE_MPLS

        nw_src = struct.unpack('!I', ipv4_to_bin(src_ip))[0]
        nw_dst = struct.unpack('!I', ipv4_to_bin(dst_ip))[0]


        match = parser.OFPMatch(eth_type=eth_IP, ipv4_dst=nw_dst, ipv4_src=nw_src)

        # f = dp.ofproto_parser.OFPMatchField.make(
        #     dp.ofproto.OXM_OF_MPLS_LABEL, mpls_label)
        # print "MPLS_LABEL: " + str(mpls_label)

        actions = [
            # parser.OFPActionPushMpls(eth_MPLS),
            # parser.OFPActionSetField(f),
            parser.OFPActionOutput(out_port_no)
        ]

        # self.add_flow(dp, 3, match, actions, FLOW_TABLE_ID)
        print "**** 1st switch: dpid=" + str(switch.dpid) + " in_port=" + str(in_port.port_no) + " out_port=" + str(out_port_no)

    def add_egress_mpls_rule(self, switch, out_port_no, mpls_label, dst, src):
        # switch = self.db.get_switch_for_port(in_port)
        ryu_switch = self.get_ryu_switch_for_dpid(switch.dpid)
        datapath = ryu_switch.dp
        parser = datapath.ofproto_parser

        nw_src = struct.unpack('!I', ipv4_to_bin(src))[0]
        nw_dst = struct.unpack('!I', ipv4_to_bin(dst))[0]
        eth_IP = ether.ETH_TYPE_IP

        match = parser.OFPMatch(eth_type=eth_IP, ipv4_dst=nw_dst, ipv4_src=nw_src)

        # eth_MPLS = ether.ETH_TYPE_MPLS
        # print "MPLS_LABEL: " + str(mpls_label)
        # match = parser.OFPMatch(mpls_label=mpls_label, eth_type=eth_MPLS)
        # match.set_dl_type(eth_MPLS)
        # match.set_mpls_label(mpls_label)

        # actions = [parser.OFPActionPopMpls(eth_MPLS),
        actions = [
            parser.OFPActionOutput(out_port_no),
            parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER)]
        # self.add_flow(datapath, 3, match, actions, FLOW_TABLE_ID)
        print "**** Last switch: dpid=" + str(switch.dpid) + " out_port=" + str(out_port_no)

    def get_ryu_switch_for_dpid(self, dpid):
        return get_switch(self.ryu_app, dpid=int(dpid))[0]

    def get_max_bandwidth_for_path(self, path):
        # TODO: doesn't work for smaller paths
        bw = None
        if len(path) > 2:
            prev_switch = path[0]
            for i in range(1, len(path)):
                link = self.db.get_link_between_switches(prev_switch, path[i])
                if bw is None:
                    bw = link.bandwidth
                # Take the smallest as the max reservation can only be as high as the smallest link
                bw = min(bw, link.bandwidth)
                prev_switch = path[i]
        else:
            print "SHORT PATH, LEN=" + str(len(path))

        return bw

    def get_available_bandwidth_for_path(self, path):
        # TODO: doesn't work for smaller paths
        total_bw = self.get_max_bandwidth_for_path(path)
        if len(path) > 2:
            prev_switch = path[0]
            avail_link_bw = []
            for i in range(1, len(path)):
                link = self.db.get_link_between_switches(prev_switch, path[i])
                link_bw = link.bandwidth
                port_reservations = self.db.get_port_reservations_for_link(link, SWITCH_MAP)
                if port_reservations:
                    reservations = []
                    for p in port_reservations:
                        reservation = self.db.get_reservation_for_id(p.reservation)
                        reservations.append(reservation)
                    for r in reservations:
                        link_bw -= reservation.bw
                avail_link_bw.append(link_bw)
                prev_switch = path[i]

        return min(avail_link_bw)
