from django.contrib.sessions.base_session import BaseSessionManager
from evennia.typeclasses.managers import TypeclassManager


class TypedSessionManager(BaseSessionManager, TypeclassManager):
    """
    This is bone simple. Just combining the two classes.
    """
