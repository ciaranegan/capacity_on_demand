from models import QoSSwitch, QoSPort

class QoSTracker:

    def __init__(self):
        self.reservations = []
        self.topology = None

    def add_switch(self, dpid, ports=None, switch_type=QoSSwitch.TYPE.EGRESS):
        switch = QoSSwitch(dpid=dpid, switch_type=switch_type)
        for port in ports:
            p = QoSPort(port_no=port["port_no"], switch=switch.dpid, total_bw=port["bw"],
                        port_type=QoSPort.TYPE.EGRESS)
