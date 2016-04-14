import sys
import os
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange, dumpNodeConnections, dumpPorts, dumpNodeConnections
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

        switch0 = self.addSwitch('s0', dpid='0000000000000010')
        switch1 = self.addSwitch('s1', dpid='0000000000000020')
        switch2 = self.addSwitch('s2', dpid='0000000000000030')

        self.addLink(host0, switch0, bw=100)
        self.addLink(host1, switch0, bw=100)

        self.addLink(host2, switch1, bw=100)
        self.addLink(host3, switch1, bw=100)

        # 50 Mbps bandwidth
        self.addLink(switch0, switch2, bw=50)
        self.addLink(switch1, switch2, bw=50)

topos = {'2switch4host': (lambda: Switches4HostsTopo())}

def start_network(controller_ip):
    topo = Switches4HostsTopo()
    net = Mininet(topo=None, switch=OVSKernelSwitch, link=TCLink, autoSetMacs=True)
    net.addController(name="c0", controller=RemoteController, ip=controller_ip, port=6633)
    net.topo = topo
    net.start()
    CLI(net)
    print topo.links()
    print topo.linkinfo()
    net.stop()
    os.system('sudo mn -c')

if __name__ == '__main__':
    setLogLevel('info')
    controller_ip = str(sys.argv[1])
    start_network(controller_ip)
