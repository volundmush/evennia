from twisted.application.service import MultiService


class EvenniaService(MultiService):
    """
    Sub-class of Twisted Service meant for Evennia's use. Application is meant to be assembled as
    a tree structure of Services.
    """
    # When launching application, the load order of the services determines the order in which they're
    # instantiated and added to the Application.
    load_order = 0

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
