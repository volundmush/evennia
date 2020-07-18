from twisted.application.service import MultiService


class EvenniaService(MultiService):
    load_order = 0

    def __init__(self, name, app):
        super().__init__()
        self.name = name
        self.app = app
        self.settings = app.settings
