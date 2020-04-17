"""
This defines a the Server's generic session object. This object represents
a connection to the outside world but don't know any details about how the
connection actually happens (so it's the same for telnet, web, ssh etc).

It is stored on the Server side (as opposed to protocol-specific sessions which
are stored on the Portal side)
"""
import time
from django.conf import settings
from evennia.comms.models import ChannelDB
from evennia.utils import logger
from evennia.utils.utils import make_iter, lazy_property
from evennia.commands.cmdsethandler import CmdSetHandler
from evennia.server.session import Session
from evennia.typeclasses.attributes import AttributeHandler, InMemoryAttributeBackend, DbHolder

_GA = object.__getattribute__
_SA = object.__setattr__
_ObjectDB = None
_ANSI = None


# -------------------------------------------------------------
# Server Session
# -------------------------------------------------------------


class ServerSession(Session):
    """
    This class represents an account's session and is a template for
    individual protocols to communicate with Evennia.

    Each account gets a session assigned to them whenever they connect
    to the game server. All communication between game and account goes
    through their session.

    """
    # Link sort is used for the Session Link system. It knows that Session commands comes before
    # puppet.
    _link_sort = -1000

    def __init__(self):
        """Initiate to avoid AttributeErrors down the line"""
        self.sessid = None
        self.logged_in = None
        self.conn_time = None
        self.django = None
        self.cmd_last_visible = None
        self.cmd_last = None
        self.cmd_total = None
        self.protocol_flags = dict()
        self.server_data = dict()
        self.sessionhandler = None
        self.address = None
        self.game_session = None
        self.cmdset_storage_string = ""
        self.cmdset = CmdSetHandler(self, True)

    def __cmdset_storage_get(self):
        return [path.strip() for path in self.cmdset_storage_string.split(",")]

    def __cmdset_storage_set(self, value):
        self.cmdset_storage_string = ",".join(str(val).strip() for val in make_iter(value))

    cmdset_storage = property(__cmdset_storage_get, __cmdset_storage_set)

    @property
    def id(self):
        return self.sessid

    def at_sync(self):
        """
        This is called whenever a ServerSession has been resynced with the
        portal.  At this point all relevant attributes have already
        been set and self.account been assigned (if applicable).

        Since this is often called after a server restart we need to
        set up the session as it was.

        """
        super().at_sync()

    def at_disconnect(self, reason=None):
        """
        Hook called by ServerSessionHandler when disconnecting this ServerSession.

        """
        if self.game_session:
            self.game_session.remove(self, reason=reason)

    def log(self, message, channel=True):
        """
        Emits session info to the appropriate outputs and info channels.

        Args:
            message (str): The message to log.
            channel (bool, optional): Log to the CHANNEL_CONNECTINFO channel
                in addition to the server log.

        """
        cchan = channel and settings.CHANNEL_CONNECTINFO
        if cchan:
            try:
                cchan = ChannelDB.objects.get_channel(cchan["key"])
                cchan.msg("[%s]: %s" % (cchan.key, message))
            except Exception:
                logger.log_trace()
        logger.log_info(message)

    def get_client_size(self):
        """
        Return eventual eventual width and height reported by the
        client. Note that this currently only deals with a single
        client window (windowID==0) as in a traditional telnet session.

        """
        flags = self.protocol_flags
        width = flags.get("SCREENWIDTH", {}).get(0, settings.CLIENT_DEFAULT_WIDTH)
        height = flags.get("SCREENHEIGHT", {}).get(0, settings.CLIENT_DEFAULT_HEIGHT)
        return width, height

    def update_session_counters(self, idle=False):
        """
        Hit this when the user enters a command in order to update
        idle timers and command counters.

        """
        # Idle time used for timeout calcs.
        self.cmd_last = time.time()

        # Store the timestamp of the user's last command.
        if not idle:
            # Increment the user's command counter.
            self.cmd_total += 1
            # Account-visible idle time, not used in idle timeout calcs.
            self.cmd_last_visible = self.cmd_last

    def update_flags(self, **kwargs):
        """
        Update the protocol_flags and sync them with Portal.

        Kwargs:
            key, value - A key:value pair to set in the
                protocol_flags dictionary.

        Notes:
            Since protocols can vary, no checking is done
            as to the existene of the flag or not. The input
            data should have been validated before this call.

        """
        if kwargs:
            self.protocol_flags.update(kwargs)
            self.sessionhandler.session_portal_sync(self)

    def data_out(self, **kwargs):
        """
        Sending data from Evennia->Client

        Kwargs:
            text (str or tuple)
            any (str or tuple): Send-commands identified
                by their keys. Or "options", carrying options
                for the protocol(s).

        """
        self.sessionhandler.data_out(self, **kwargs)

    def data_in(self, **kwargs):
        """
        Receiving data from the client, sending it off to
        the respective inputfuncs.

        Kwargs:
            kwargs (any): Incoming data from protocol on
                the form `{"commandname": ((args), {kwargs}),...}`
        Notes:
            This method is here in order to give the user
            a single place to catch and possibly process all incoming data from
            the client. It should usually always end by sending
            this data off to `self.sessionhandler.call_inputfuncs(self, **kwargs)`.
        """
        self.sessionhandler.call_inputfuncs(self, **kwargs)

    def execute_cmd(self, raw_string, session=None, **kwargs):
        """
        Do something as this object. This method is normally never
        called directly, instead incoming command instructions are
        sent to the appropriate inputfunc already at the sessionhandler
        level. This method allows Python code to inject commands into
        this stream, and will lead to the text inputfunc be called.

        Args:
            raw_string (string): Raw command input
            session (Session): This is here to make API consistent with
                Account/Object.execute_cmd. If given, data is passed to
                that Session, otherwise use self.
        Kwargs:
            Other keyword arguments will be added to the found command
            object instace as variables before it executes.  This is
            unused by default Evennia but may be used to set flags and
            change operating paramaters for commands at run-time.

        """
        # inject instruction into input stream
        kwargs["text"] = ((raw_string,), {})
        self.sessionhandler.data_in(session or self, **kwargs)

    def __eq__(self, other):
        """Handle session comparisons"""
        try:
            return self.address == other.address
        except AttributeError:
            return False

    def __hash__(self):
        """
        Python 3 requires that any class which implements __eq__ must also
        implement __hash__ and that the corresponding hashes for equivalent
        instances are themselves equivalent.

        """
        return hash(self.address)

    def __ne__(self, other):
        try:
            return self.address != other.address
        except AttributeError:
            return True

    def __str__(self):
        """
        String representation of the user session class. We use
        this a lot in the server logs.

        """
        symbol = ""
        if self.logged_in and hasattr(self, "account") and self.account:
            symbol = "(#%s)" % self.account.id
        try:
            if hasattr(self.address, "__iter__"):
                address = ":".join([str(part) for part in self.address])
            else:
                address = self.address
        except Exception:
            address = self.address
        return "%s%s@%s" % (self.uname, symbol, address)

    def __repr__(self):
        return "%s" % str(self)

    # Dummy API hooks for use during non-loggedin operation

    def at_cmdset_get(self, **kwargs):
        """
        A dummy hook all objects with cmdsets need to have
        """

        pass

    # Mock db/ndb properties for allowing easy storage on the session
    # (note that no databse is involved at all here. session.db.attr =
    # value just saves a normal property in memory, just like ndb).

    @lazy_property
    def nattributes(self):
        return AttributeHandler(self, InMemoryAttributeBackend)

    @lazy_property
    def attributes(self):
        return self.nattributes

    # @property
    def ndb_get(self):
        """
        A non-persistent store (ndb: NonDataBase). Everything stored
        to this is guaranteed to be cleared when a server is shutdown.
        Syntax is same as for the _get_db_holder() method and
        property, e.g. obj.ndb.attr = value etc.

        """
        try:
            return self._ndb_holder
        except AttributeError:
            self._ndb_holder = DbHolder(self, "nattrhandler", manager_name="nattributes")
            return self._ndb_holder

    # @ndb.setter
    def ndb_set(self, value):
        """
        Stop accidentally replacing the db object

        Args:
            value (any): A value to store in the ndb.

        """
        string = "Cannot assign directly to ndb object! "
        string += "Use ndb.attr=value instead."
        raise Exception(string)

    # @ndb.deleter
    def ndb_del(self):
        """Stop accidental deletion."""
        raise Exception("Cannot delete the ndb object!")

    ndb = property(ndb_get, ndb_set, ndb_del)
    db = property(ndb_get, ndb_set, ndb_del)

    # Mock access method for the session (there is no lock info
    # at this stage, so we just present a uniform API)
    def access(self, *args, **kwargs):
        """Dummy method to mimic the logged-in API."""
        return True
