from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange, dumpNodeConnections
from mininet.log import setLogLevel

class Switches4HostsTopo(Topo):

    def __init__(self, **opts):
        super(Switches4HostsTopo, self).__init__(**opts)

        host0 = self.addHost('h0')
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')
        host3 = self.addHost('h3')

        switch0 = self.addSwitch('s0')
        switch1 = self.addSwitch('s1')

        self.addLink(host0, switch0, bw=10)
        self.addLink(host1, switch0, bw=10)
        self.addLink(host2, switch1, bw=10)
        self.addLink(host3, switch1, bw=10)
        self.addLink(switch0, switch1, bw=3)

topos = {'2switch4host': (lambda: Switches4HostsTopo())}

if __name__ == '__main__':
    topo = Switches4HostsTopo()
    net = Mininet(topo=topo, switch=OVSKernelSwitch, mac=None)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    net.start()
