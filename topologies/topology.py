from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange, dumpNodeConnections
from mininet.log import setLogLevel

class LinearTopo(Topo):

	def __init__(self, num_switches=3, **opts):
		super(LinearTopo, self).__init__(**opts)

		self.num_switches = num_switches

		previous = None
		for i in range(1, num_switches):
			# Create and connect a host and a switch
			host = self.addHost('h%s' % i)
			switch = self.addSwitch('s%s' % i)
			self.addLink(host, switch)

			if previous:
				# Connect the switch to the previous switch
				self.addLink(switch, previous)
			previous = switch


def test():
	topo = LinearTopo(k=4)
	net = Mininet(topo)
	net.start()
	dumpNodeConnections(net.hosts)
	net.pingAll()
	net.stop()


if __name__ == '__main__':
	setLogLevel('info')
	test()
