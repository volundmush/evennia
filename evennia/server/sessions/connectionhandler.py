class SessionConnectionHandler:

    def __init__(self, session):
        self.session = session
        self._connections = list()
        self._conn_dict = dict()

    def all(self):
        return list(self._connections)

    def count(self):
        return len(self._connections)

    def do_add(self, connection):
        pass

    def do_remove(self, connection):
        pass

    def add(self, connection, sync=False, reason=None):
        pass

    def remove(self, connection, sync=False, reason=None, logout=False):
        pass

