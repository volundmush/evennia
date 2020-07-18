from twisted.internet.protocol import ServerFactory
from twisted.internet import ssl

from evennia.application import EvenniaService
from evennia.utils.utils import class_from_module


class EvenniaServerFactory(ServerFactory):

    def __init__(self):
        super().__init__()
        self.service = None


class ServerService(EvenniaService):
    """
    This Service is a container for a Protocol Factory and a listener.
    """

    def __init__(self, factory, interface, port, protocol, tls):
        super().__init__()
        self.factory = factory.forProtocol(protocol)
        self.factory.service = self
        self.interface = interface
        self.port = port
        self.protocol = protocol
        self.tls = tls
        self.listener = None

    def startService(self):
        if self.running:
            return
        if self.tls:
            self.listener = self.reactor.listenSSL(self.port, self.factory, self.tls, interface=self.interface)
        else:
            self.listener = self.reactor.listenTCP(self.port, self.new_server, interface=self.interface)
        self.running = 1

    def stopService(self):
        if not self.running:
            return
        results = self.listener.stopListening()
        self.listener = None
        self.running = 0
        return results


class ConnectService(EvenniaService):
    """
    This Service is responsible for launching all the configured game client servers.
    """

    def __init__(self):
        super().__init__()
        self.server_classes = dict()
        self.factory_classes = dict()
        self.protocol_classes = dict()
        self.ssl_context = dict()

    def create_server(self, name, interface, port, server_class, factory_class, protocol_class, tls):
        if name in self.namedServices:
            raise ValueError("That name conflicts with an existing server!")
        if not (srv_class := self.server_classes.get(server_class, None)):
            raise ValueError(f"Server Class {server_class} has not been registered!")
        if not (fac_class := self.factory_classes.get(factory_class, None)):
            raise ValueError(f"Factory Class {factory_class} has not been registered!")
        if not (prot_class := self.protocol_classes.get(protocol_class, None)):
            raise ValueError(f"Protocol Class {protocol_class} has not been registered!")
        if tls and not self.ssl_context:
            raise ValueError("TLS is not properly configured. Cannot start TLS server.")
        if tls and self.ssl_context:
            tls = self.ssl_context
        new_server = srv_class(self, fac_class, interface, port, prot_class, tls)
        new_server.setName(name)
        new_server.setServiceParent(self)
        new_server.setApplication(self.app)
        new_server.loadSettings()
        new_server.setup()

    def setup(self):
        if not self.settings:
            raise RuntimeError(f"{self} has no settings. Cannot setup!")
        for k, v in self.settings.SERVER_CLASSES.items():
            self.server_classes[k] = class_from_module(v)
        for k, v in self.settings.PROTOCOL_CLASSES.items():
            self.protocol_classes[k] = class_from_module(v)
        # do TLS init down here...

        for k, v in self.app.settings.SERVERS.items():
            self.create_server(k, v['interface'], v['port'], v['server_class'], v['factory_class'], v['protocol_class'],
                               v['tls'])


class AmpService(EvenniaService):
    """
    This Service runs the AMP Server that the Server uses to link up to the Portal.
    """



class WebService(EvenniaService):
    """
    This Service runs the Evennia WebSite.
    """
