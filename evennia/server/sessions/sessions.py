from evennia.sessions.models import SessionDB
from evennia.typeclasses.models import TypeclassBase
from evennia.commands.cmdsethandler import CmdSetHandler
from evennia.utils.utils import lazy_property
from evennia.sessions.connectionhandler import SessionConnectionHandler
from evennia.sessions.sessionlinkhandler import LinkHandler
from evennia.utils.create import create_session


class DefaultSession(SessionDB, metaclass=TypeclassBase):

    @classmethod
    def create(cls, **kwargs):
        """
        Creates a new game Session for managing player activities.

        Must include an account kwarg. See evennia.utils.create.create_session
        for full arguments.

        Returns:
            Session (DefaultSession): The new DefaultSession.
        """
        return create_session(typeclass=cls, **kwargs)

    def at_session_creation(self):
        pass

    def at_cmdset_get(self, **kwargs):
        """
        A dummy hook all objects with cmdsets need to have
        """
        pass

    @lazy_property
    def connections(self):
        """
        This handler governs Sessions-to-Connections. Like Telnet sessions.
        """
        return SessionConnectionHandler(self)

    @lazy_property
    def links(self):
        """
        This handler governs Sessions-to-Entities connections. Like Accounts and
        Puppets.
        """
        return LinkHandler(self)

    def basetype_setup(self):
        # the default security setup fallback for a generic
        # session. Overload in child for a custom setup. Also creation
        # commands may set this (create an item and you should be its
        # controller, for example)

        self.locks.add(
            ";".join(
                [
                    "control:perm(Developer)",  # edit locks/permissions, delete
                    "examine:perm(Admin)",  # examine properties
                    "edit:perm(Admin)",  # edit properties/attributes
                    "delete:perm(Admin)",  # delete object
                ]
            )
        )  # lock down puppeting only to staff by default

    def basetype_posthook_setup(self):
        pass

    def at_first_save(self):
        """
        This is called by the typeclass system whenever an instance of
        this class is saved for the first time. It is a generic hook
        for calling the startup hooks for the various game entities.
        When overloading you generally don't overload this but
        overload the hooks called by this method.

        """
        self.basetype_setup()
        self.at_session_creation()

        if hasattr(self, "_createdict"):
            # this will only be set if the utils.create function
            # was used to create the object. We want the create
            # call's kwargs to override the values set by hooks.
            cdict = self._createdict
            updates = []

            account = cdict.get('account')

            if not cdict.get("key"):
                if not self.db_key:
                    self.db_key = f"{account.username}#{self.dbid}"
                    updates.append("db_key")
            elif self.key != cdict.get("key"):
                updates.append("db_key")
                self.db_key = cdict["key"]
            if updates:
                self.save(update_fields=updates)

            if cdict.get("permissions"):
                self.permissions.batch_add(*cdict["permissions"])
            if cdict.get("locks"):
                self.locks.add(cdict["locks"])
            if cdict.get("aliases"):
                self.aliases.batch_add(*cdict["aliases"])
            if cdict.get("tags"):
                # this should be a list of tags, tuples (key, category) or (key, category, data)
                self.tags.batch_add(*cdict["tags"])
            if cdict.get("attributes"):
                # this should be tuples (key, val, ...)
                self.attributes.batch_add(*cdict["attributes"])
            if cdict.get("nattributes"):
                # this should be a dict of nattrname:value
                for key, value in cdict["nattributes"]:
                    self.nattributes.add(key, value)

            del self._createdict

        self.basetype_posthook_setup()

    @lazy_property
    def cmdset(self):
        return CmdSetHandler(self, True)

    def at_deliberate_logout(self, **kwargs):
        """
        This signifies that a deliberate logout has been triggered, either by
        player desire or admin desire. This should disconnect all ServerSessions
        and clean up game state, or start some kind of timer that will do so on
        our behalf.

        """
        pass

    def at_unexpected_logout(self, **kwargs):
        """
        This hook should only be called in an event such as all ServerSessions
        losing connection. The intentions of the player are unknown - perhaps they lost
        internet, force-closed their client, or crashed. This will likely call the
        same code path as deliberate logouts, but some games may want it to do
        things differently. This is usually called "going link-dead" in MU* parlance.
        """
        pass

    def get_account(self):
        """
        Get the account associated with this session.

        Returns:
            account (Account): The associated Account.

        """
        return self.links.get('account')

    def get_puppet(self):
        """
        Get the in-game character associated with this session.

        Returns:
            puppet (Object): The puppeted object, if any.

        """
        return self.links.get('puppet')

    get_character = get_puppet

    def get_puppet_or_account(self):
        """
        Get puppet or account.

        Returns:
            controller (Object or Account): The puppet if one exists,
                otherwise return the account.

        """
        puppet = self.get_puppet()
        if puppet:
            return puppet
        else:
            return self.get_account()

    @property
    def account(self):
        return self.get_account()

    @property
    def puppet(self):
        return self.get_puppet()

    @property
    def character(self):
        return self.get_puppet()

    def msg(self, text=None, **kwargs):
        """
        Wrapper to mimic msg() functionality of Objects and Accounts.

        Args:
            text (str): String input.

        Kwargs:
            any (str or tuple): Send-commands identified
                by their keys. Or "options", carrying options
                for the protocol(s).

        """
        # this can happen if this is triggered e.g. a command.msg
        # that auto-adds the session, we'd get a kwarg collision.
        kwargs.pop("session", None)
        kwargs.pop("from_obj", None)
        if text is not None:
            for conn in self.connections.all():
                conn.data_out(text=text, **kwargs)
        else:
            for conn in self.connections.all():
                conn.data_out(**kwargs)
