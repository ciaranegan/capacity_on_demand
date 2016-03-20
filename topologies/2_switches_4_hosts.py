import sys
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
        switch0.setMAC('00:00:00:00:00:06')
        switch1 = self.addSwitch('s1')
        switch1.setMAC('00:00:00:00:00:07')

        self.addLink(host0, switch0, bw=10)
        self.addLink(host1, switch0, bw=10)
        self.addLink(host2, switch1, bw=10)
        self.addLink(host3, switch1, bw=10)
        self.addLink(switch0, switch1, bw=3)

topos = {'2switch4host': (lambda: Switches4HostsTopo())}

def start_network(controller_ip):
    topo = Switches4HostsTopo()
    net = Mininet(topo=None, switch=OVSKernelSwitch, link=TCLink, autoSetMacs=True)
    net.addController(name="c0", controller=RemoteController, ip=controller_ip, port=6633)
    net.topo = topo
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    controller_ip = str(sys.argv[1])
    start_network(controller_ip)
