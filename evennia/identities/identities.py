from evennia.identities.models import IdentityDB
from evennia.typeclasses.models import TypeclassBase
from evennia.commands.cmdsethandler import CmdSetHandler
from evennia.utils.utils import lazy_property


class DefaultIdentity(IdentityDB, metaclass=TypeclassBase):
    pass

