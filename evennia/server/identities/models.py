from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.contrib.sessions.base_session import AbstractBaseSession
from django.contrib.sessions.base_session import BaseSessionManager

from django.utils.translation import gettext as _

from evennia.typeclasses.models import TypedObject, SharedMemoryModel
from evennia.identities.managers import IdentityManager


class IdentityDB(TypedObject):
    """
    The GameSession is responsible for hanging on to all data concerning
    a player's overall experience - the Account they're logged into, the
    character they're using. It keeps track of everything regarding entering
    and leaving the game. If the SessionDB loses all Connections,
    then it must process logic for removing avatars from the game world.
    Etc.
    """
    __settingsclasspath__ = settings.BASE_IDENTITY_TYPECLASS
    __defaultclasspath__ = "evennia.identities.identities.DefaultIdentity"
    __applabel__ = "identities"

    objects = IdentityManager()

    # database storage of persistant cmdsets.
    db_cmdset_storage = models.CharField(
        "cmdset",
        max_length=255,
        null=True,
        blank=True,
        help_text="optional python path to a cmdset class.",
    )
