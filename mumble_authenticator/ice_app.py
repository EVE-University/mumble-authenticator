import Ice
import logging
from threading import Timer
from .conf import settings
from .decorators import ice_protect, check_secret
from .authenticator import MurmurAdapter
from . import Murmur


logger = logging.getLogger(__name__)


class AuthenticatorApp(Ice.Application):
    def __init__(self):
        super().__init__()
        self.meta = None
        self.meta_callback = None
        self.watchdog = None
        self.adapter = None
        self.connected = False
        self.adapters = dict()

    def run(self, args):
        self.shutdownOnInterrupt()

        # Initialise connection
        self.connect()

        if settings.ice.watchdog:
            self.heartbeat()

        self.communicator().waitForShutdown()
        self.watchdog.cancel()

        if self.interrupted():
            logger.warning('Interrupted, shutting down')
            for s, adapter in self.adapters.items():
                # Call all the shutdown functions
                logger.debug('Shutting down server {}'.format(s))
                adapter.auth.shutdown()

    def connect(self):
        ice = self.communicator()

        try:
            ice.getImplicitContext().put("secret", settings.ice.secret)
        except AttributeError:
            logger.warning('Ice secret not configured. This is an insecure connection')

        logger.info('Connecting to Ice server {}:{}', settings.ice.host, settings.ice.port)
        base = ice.stringToProxy('Meta:tcp -h {} -p {}'.format(settings.ice.host, settings.ice.port))

        self.meta = Murmur.MetaPrx.uncheckedCast(base)

        self.adapter = ice.createObjectAdapterWithEndpoints('Callback.Client', 'tcp -h {}'.format(settings.ice.host))
        self.adapter.activate()

        meta_callback_proxy = self.adapter.addWithUUID(MetaCallback(self))
        self.meta_callback = Murmur.MetaCallbackPrx.uncheckedCast(meta_callback_proxy)

        self.meta.addCallback(self.meta_callback)

        # Attach authenticators for started servers
        for server in self.meta.getBootedServers():
            self.meta_callback.attach_authenticator(server)

        self.connected = True
        return True

    def heartbeat(self):
        """
        Reattach callbacks to cover for murmur restarts and disconnects
        """
        if not settings.ice.watchdog:
            return
        try:
            self.meta.addCallback(self.meta_callback)
            self.reattach_authenticators()
        except Ice.Exception as e:
            logger.error('Watchdog failed, retrying in {} seconds'.format(settings.ice.watchdog))

        self.watchdog = Timer(settings.ice.watchdog, self.heartbeat)
        self.watchdog.start()

    def attach_authenticator(self, server):
        """
        Attach authenticator to started server
        """
        server_id = server.id()
        if server_id in settings.murmur.servers:
            server = settings.murmur.servers.get(server_id)
        else:
            server = settings.murmur.servers.get(settings.murmur.default_conf)

        logger.info('Setting authenticator {} for virtual server {}'.format(server.auth_class, server_id))
        auth = self.import_klass(server.auth_class)(server_id)
        adapter = MurmurAdapter(auth)
        try:
            server.setAuthenticator(adapter)
            self.adapters[server_id] = adapter
        except (Murmur.InvalidSecretException, Ice.UnknownUserException):
            logger.error('Invalid Ice secret')

    def reattach_authenticators(self):
        """
        Reattaches all registered authentication adapters
        :return:
        """
        for server in self.meta.getBootedServers():
            server_id = server.id()
            if server_id in self.adapters:
                logger.debug('Reattaching adapter for server {}'.format(server_id))
                server.setAuthenticator(self.adapters.get(server_id))
            else:
                logger.debug('No adapter for server {}'.format(server_id))

    @staticmethod
    def import_klass(name):
        components = name.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod


class MetaCallback(Murmur.MetaCallback):
    def __init__(self, app):
        super().__init__(self)
        self.app = app

    @ice_protect
    @check_secret
    def started(self, server):
        """
        Virtual server started
        """
        self.app.attach_authenticator(server)

    @ice_protect
    @check_secret
    def stopped(self, server):
        """
        Virtual server stopped
        """

        if not self.app.connected:
            return

        try:
            server_id = server.id()
            if server_id in settings.murmur.servers:
                logger.info('Authenticated virtual server {} stopped'.format(server_id))
                self.app.adapters.pop(server_id)
            else:
                logger.debug('Virtual server {} stopped'.format(server_id))
        except Ice.ConnectionRefusedException:
            self.app.connected = False
