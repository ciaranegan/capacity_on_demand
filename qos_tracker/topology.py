
s0_DPID = "16"
s1_DPID = "32"
s2_DPID = "48"

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

class TopologyManager:

    def __init__(self, db):
        self.db = db

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
