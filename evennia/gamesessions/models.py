from django.conf import settings
from django.db import models
from evennia.typeclasses.models import TypedObject


class GameSessionDB(TypedObject):
    """
    The GameSession is responsible for hanging on to all data concerning
    a player's overall experience - the Account they're logged into, the
    character they're using. It keeps track of everything regarding entering
    and leaving the game. If the GameSessionDB loses all Connections,
    then it must process logic for removing avatars from the game world.
    Etc.
    """
    # db_key will probably be some random hash.

