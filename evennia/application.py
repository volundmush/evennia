import os

from twisted.application.service import MultiService, Application
from twisted.python.log import ILogObserver

from evennia.utils.utils import class_from_module
from evennia.utils import logger


class EvenniaService(MultiService):
    """
    Sub-class of Twisted Service meant for Evennia's use. Application is meant to be assembled as
    a tree structure of Services.
    """
    # When launching application, the load order of the services determines the order in which they're
    # instantiated and added to the Application.
    load_order = 0
    setup_order = 0

    def __init__(self):
        super().__init__()
        self.app = None
        self.settings = None
        self.reactor = None

    def setApplication(self, app):
        self.app = app
        self.reactor = app.reactor

    def loadSettings(self, settings=None):
        """
        Loads/caches/links settings from provided argument or from the Application if set.
        """
        if settings is None:
            if not self.app:
                raise RuntimeError(f"{self} has no Application to obtain settings from!")
            settings = self.app.settings
        self.settings = settings

    def setup(self):
        """
        Overrideable method used to configure the Service once it has been linked
        to the application and given proper settings.
        """


class ApplicationFactory:
    """
    Used for creating an Evennia Application built atop of Twisted's Application Framework.
    """
    services_property = None

    def __init__(self, name, reactor, settings, args):
        self.app = Application(name)
        self.settings = settings
        self.app.settings = settings
        self.app.reactor = reactor
        self.args = args

    def setup(self):
        pass

    def setup_logging(self):
        if "--nodaemon" not in self.args:
            logfile = logger.WeeklyLogFile(
                os.path.basename(self.settings.PORTAL_LOG_FILE),
                os.path.dirname(self.settings.PORTAL_LOG_FILE),
                day_rotation=self.settings.PORTAL_LOG_DAY_ROTATION,
                max_size=self.settings.PORTAL_LOG_MAX_SIZE,
            )
            self.app.setComponent(ILogObserver, logger.PortalLogObserver(logfile).emit)

    def initialize_services(self):
        for k, v in sorted(getattr(self.settings, self.services_property, dict()), key=lambda x: x[1].get('load_order', 0)):
            srv_class = class_from_module(v)
            service = srv_class()
            service.setName(k)
            service.setServiceParent(self.app)
            service.setApplication(self.app)
            service.loadSettings()

        for service in sorted(self.app.services, key=lambda x: getattr(x, 'setup_order', 0)):
            service.setup()

    def build(self):
        return self.app
