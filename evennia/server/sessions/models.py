from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.contrib.sessions.base_session import AbstractBaseSession
from django.contrib.sessions.base_session import BaseSessionManager

from django.utils.translation import gettext as _

from evennia.typeclasses.models import TypedObject, SharedMemoryModel
from evennia.sessions.manager import TypedSessionManager


class DjangoSession(AbstractBaseSession):
    """
    Django uses its own Sessions as a way to identify users of the website and clients.
    Evennia also generates DjangoSessions for telnet users, for consistency. It is
    possible for multiple Connections to share the same session_key.
    """

    # Normally the session_key would be the primary key. Here we change it
    # to be just Unique so that an AutoField is generated. This doesn't interfere
    # with session generation, but it allows us to refer to sessions incrementally
    # internally so the string isn't duplicated across every foreign key.
    session_key = models.CharField(_('session key'), max_length=40, unique=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    # One Django Connection can be linked to at most one SessionDB
    session_game = models.ForeignKey('sessions.SessionDB', related_name='django_sessions',
                                     on_delete=models.CASCADE, null=True)

    objects = BaseSessionManager()

    @classmethod
    def get_session_store_class(cls):
        return SessionStore


class SessionStore(DBStore):
    """
    The other part of the Session engine Django needs. SessionStore is used to generate new
    sessions.
    """

    @classmethod
    def get_model_class(cls):
        return DjangoSession

    def create_model_instance(self, data):
        obj = super().create_model_instance(data)
        try:
            account_id = int(data.get('_auth_user_id'))
        except (ValueError, TypeError):
            account_id = None
        obj.account_id = account_id
        return obj


class SessionDB(TypedObject):
    """
    The GameSession is responsible for hanging on to all data concerning
    a player's overall experience - the Account they're logged into, the
    character they're using. It keeps track of everything regarding entering
    and leaving the game. If the SessionDB loses all Connections,
    then it must process logic for removing avatars from the game world.
    Etc.
    """
    __settingsclasspath__ = settings.BASE_SESSION_TYPECLASS
    __defaultclasspath__ = "evennia.sessions.sessions.DefaultSession"
    __applabel__ = "sessions"

    objects = TypedSessionManager()

    # database storage of persistant cmdsets.
    db_cmdset_storage = models.CharField(
        "cmdset",
        max_length=255,
        null=True,
        blank=True,
        help_text="optional python path to a cmdset class.",
    )

    # Not sure what else yet... if anything.


class SessionLink(models.Model):
    """
    This table links Sessions to any number of other database entities using
    generic relations. This is used for linking Accounts and Puppets to the
    CmdSet Gather system. Sessions sit at the heart of it.

    This is a normal model because it doesn't need any special behavior, and caching
    may interfere with GenericForeignKey.
    """
    session = models.ForeignKey(SessionDB, related_name='session_links', on_delete=models.CASCADE)

    # This trio of fields is used to construct the GenericForeignKey.
    # GenericForeignKey (db_entity) will appear to be None
    # should the linked objects be deleted. However, we don't want to
    # rely on that. Always call session.delete() to ensure this is cleaned up.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    entity = GenericForeignKey('content_type', 'object_id')

    # This adds an identifier to the kind of Link. 'puppet', 'account', etc.
    kind = models.CharField(max_length=50, null=False, blank=False)

    class Meta:
        verbose_name = 'SessionLink'
        verbose_name_plural = 'SessionLinks'
        unique_together = (('session', 'content_type', 'object_id'), ('session', 'kind'))


class Connection(models.Model):
    """
    As this is one of the two tables that the Portal and Server must both talk to, it is NOT
    a SharedMemoryModel. This is used for info storage. The actual in-memory objects represent the
    true Protocols and networking going on.
    """
    uuid = models.UUIDField(unique=True)
    django_session = models.ForeignKey(DjangoSession, related_name='connections', on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    address = models.GenericIPAddressField()
    protocol_key = models.CharField(max_length=40, null=False, blank=False)
    game_session = models.ForeignKey(SessionDB, related_name='connections', null=True, on_delete=models.SET_NULL)
