import requests
import json
import struct
import time
import threading

from models import *
from topology_1_constants import *
from topology import TopologyManager
from ryu import RyuManager
from dbconnection import DBConnection
#from ryu.topology.api import get_all_switch, get_all_link, get_switch
#from ryu.ofproto import ether
#from ryu.lib.ip import ipv4_to_bin
from IPython import embed


class QoSTracker:

    def __init__(self):
        self.db = DBConnection('sqlite:///my_db.db')
        self.topology_manager = TopologyManager(self.db)
        self.ryu = RyuManager(self.db)
        self._current_mpls_label = 0
        self._flows_added = 0

    def start(self):
        self.db.delete_reservations()
        self.db.delete_queues()
        switches = self.db.get_all_switches()
        for switch in switches:
            self.ryu.put_ovsdb_addr(switch.dpid)

    # def add_port_queue(self, switch, port_no, queues):
    #     switch_id = self.get_switch_id_for_dpid(switch.dpid)
    #     port_name = self.get_port_name_for_port_no(port_no, switch.dpid)

    #     for queue in queues:
    #         if "max_rate" in queue:
    #             max_rate = queue["max_rate"]
    #         else:
    #             max_rate = None
    #         if "min_rate" in queue:
    #             min_rate = queue["min_rate"]
    #         else:
    #             min_rate = None

    #         data = {
    #             "port_name": port_name,
    #             "type": OVS_LINK_TYPE,
    #             "max_rate": str(max_rate),
    #             "queues": queues
    #         }

    #         url = LOCALHOST + QOS_QUEUES_URI + switch_id
    #         request = requests.post(url, data=json.dumps(data))
    #         print "Request returned(port_queue_init): " + str(request.text)

    # def get_max_bw_for_topo(self):
    #     links = self.db.get_all_links()
    #     max_bw = 0
    #     for link in links:
    #         max_bw = max(max_bw, link.bandwidth)
    #     return max_bw

    # def get_reservation_for_src_dst(self, src, dst):
    #     return self.db.get_reservation_for_src_dst(src, dst)

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

    def add_switches(self, switch_data):
        for switch in switch_data:
            s = self.db.add_switch(switch, HOST_MAP[str(switch.dp.id)])

    def add_reservation(self, rsv):
        reservation = self.db.add_reservation(rsv, self.generate_mpls_label())

        in_port = self.db.get_port_for_id(reservation.in_port)
        in_switch = self.db.get_switch_for_port(in_port)

        last_port = self.db.get_port_for_id(reservation.out_port)
        last_switch = self.db.get_switch_for_port(last_port)

        path = self.topology_manager.get_route_to_host(rsv["dst"], in_switch)
        total_bw = self.topology_manager.get_max_bandwidth_for_path(path)
        print "Total Bandwidth: " + str(total_bw)

        available_bw = self.topology_manager.get_available_bandwidth_for_path(path)
        print "Available Bandwidth: " + str(available_bw)
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

    # def add_queue_flow(self, switch, port, src, dst, queue_id=HIGH_PRIORITY_QUEUE_ID):
    #     switch_id = self.get_switch_id_for_dpid(switch.dpid)
    #     data = {
    #         "match": {
    #             "nw_dst": dst,
    #             "nw_src": src,
    #             "nw_proto": "UDP"
    #     #        "dl_type": "IPv4"
    #         },
    #         "actions": {
    #             "queue": queue_id
    #         }
    #     }
    #     url = LOCALHOST + QOS_RULES_URI + switch_id
    #     request = requests.post(url, data=json.dumps(data))
    #     print "Request returned(queue_init): " + str(request.text)

    def add_ingress_rules(self, switch, out_port_no, src_ip, dst_ip, bw, max_bw):
        # Add queues
        queues = [{"max_rate": str(max_bw)}, {"min_rate": str(bw)}]
        self.ryu.add_egress_port_queue(switch, out_port_no, queues, max_bw)

        # Mark the packets on their way in
        self.ryu.add_packet_marking_flow(switch, src_ip, dst_ip)

    def add_switch_rules(self, switch, out_port_no, src_ip, dst_ip, bw, max_bw):
        # Add queues
        queues = [{"max_rate": str(max_bw)}, {"min_rate": str(bw)}]
        self.ryu.add_egress_port_queue(switch, out_port_no, queues, max_bw)

        self.ryu.add_packet_checking_flow(switch)
