from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange, dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import OVSKernelSwitch, RemoteController

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

def start_network():
    topo = Switches4HostsTopo()
    net = Mininet(topo=None, switch=OVSKernelSwitch, link=TCLink, autoSetMacs=True)
    net.addController(name="c0", controller=RemoteController, ip='10.6.1.85', port=6633)
    net.topo = topo
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    start_network()
