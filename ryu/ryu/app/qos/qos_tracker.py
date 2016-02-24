from enum import Enum

INGRESS = "ingress"
EGRESS = "egress"

class QoSTracker:

	def __init__(self):
		self.reservations = []
		self.topology = None

	def add_reservation(self, src, dst, bw):
		self.reservations.append(QoSReservation(src, dst, bw))

	def remove_reservation(self, res):
		self.reservations.remove(res)


class QoSReservation:
	"""
	Class to represent a bandwidth allocation.
	"""
	def __init__(self, src, dst, bw, mpls_label=None):
		self.src = src
		self.dst = dst
		self.bw = bw
		self.mpls_label = mpls_label

class QoSReservationPort:
	"""
	Class to represent an allocation for a specific port.
	"""
	def __init__(self, port_id, bw, reserv_id):
		self.port_id = port_id
		self.bw = bw
		self.reservation = reserv_id


class QoSSwitch:
	"""
	Class to represent a switch.
	"""
	SWITCH_TYPE = Enum(INGRESS, EGRESS)

	def __init__(self, dpid, switch_type=SWITCH_TYPE.EGRESS):
		self.dpid = dpid
		self.switch_type = switch_type


class QoSPort:
	"""
	Class to represent a port.
	"""
	PORT_TYPE = Enum(INGRESS, EGRESS)

	def __init__(self, port_no, dpid, bw, port_type=PORT_TYPE.EGRESS):
		self.no = port_no
		self.dpid = dpid
		self.bw = bw
		self.port_type = port_type

