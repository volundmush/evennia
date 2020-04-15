from evennia.sessions.models import SessionDB
from evennia.typeclasses.models import TypeclassBase


class DefaultSession(SessionDB, metaclass=TypeclassBase):
    pass
