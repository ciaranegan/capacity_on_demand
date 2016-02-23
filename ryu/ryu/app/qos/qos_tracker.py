class QoSTracker:

	def __init__(self):
		self.reservations = []
		self.topology = None

	def add_reservation(self, src, dst, bw):
		self.reservations.append(QoSReservation(src, dst, bw))

	def remove_reservation(self, res):
		self.reservations.remove(res)


class QoSReservation:

	def __init__(self, src, dst, bw, start_time=None, end_time=None):
		self.src = src
		self.dst = dst
		self.bw = bw
		self.start_time = start_time
		self.end_time = end_time
