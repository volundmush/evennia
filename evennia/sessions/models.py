from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models
from evennia.sessions.manager import TypedSessionManager
from django.utils.translation import gettext as _

from evennia.typeclasses.models import TypedObject


class SessionDB(TypedObject, AbstractBaseSession):
    """
    The GameSession is responsible for hanging on to all data concerning
    a player's overall experience - the Account they're logged into, the
    character they're using. It keeps track of everything regarding entering
    and leaving the game. If the GameSessionDB loses all Connections,
    then it must process logic for removing avatars from the game world.
    Etc.
    """
    __settingsclasspath__ = settings.BASE_SESSION_TYPECLASS
    __defaultclasspath__ = "evennia.sessions.sessions.DefaultSession"
    __applabel__ = "sessions"

    session_key = models.CharField(_('session key'), max_length=40, unique=True)

    objects = TypedSessionManager()

    @classmethod
    def get_session_store_class(cls):
        return SessionStore


class SessionStore(DBStore):

    @classmethod
    def get_model_class(cls):
        return SessionDB

    def create_model_instance(self, data):
        obj = super().create_model_instance(data)
        try:
            account_id = int(data.get('_auth_user_id'))
        except (ValueError, TypeError):
            account_id = None
        obj.account_id = account_id
        return obj
