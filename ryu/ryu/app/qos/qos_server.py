import json
import logging

from ryu.app.qos import qos_switch

from webob import Response
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib

simple_switch_instance_name = "simple_switch_api_app"
url = "/simpleswitch/mactable/{dpid}"
hello_url = "/hello"

class QoSSwitchRest13(qos_switch.QoSSwitch13):

    _CONTEXTS = { "wsgi": WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(QoSSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs["wsgi"]
        wsgi.register(QoSController, {simple_switch_instance_name : self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(QoSSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})

class QoSController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(QoSController, self).__init__(req, link, data, **config)
        self.simpl_switch_spp = data[simple_switch_instance_name]


    @route("hello", hello_url, methods=["GET"])
    def list_mac_table(self, req, **kwargs):
        simple_switch = self.simpl_switch_spp
        request_data = {
            "src": "10.0.0.1",
            "dst": "10.0.0.4",
            "bw": 20
        }

        simple_switch.qos.add_reservation(request_data)
        # mac_table = simple_switch.mac_to_port.get(dpid, {})
        body = json.dumps({"mac_table": "hi"})
        return Response(content_type="application/json", body=body)
