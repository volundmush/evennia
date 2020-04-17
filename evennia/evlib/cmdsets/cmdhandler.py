"""
Command handler

This module contains the infrastructure for accepting commands on the
command line. The processing of a command works as follows:

1. The calling object (caller) is analyzed based on its callertype.
2. Cmdsets are gathered from different sources:
   - channels:  all available channel names are auto-created into a cmdset, to allow
     for giving the channel name and have the following immediately
     sent to the channel. The sending is performed by the CMD_CHANNEL
     system command.
   - object cmdsets: all objects at caller's location are scanned for non-empty
     cmdsets. This includes cmdsets on exits.
   - caller: the caller is searched for its own currently active cmdset.
   - account: lastly the cmdsets defined on caller.account are added.
3. The collected cmdsets are merged together to a combined, current cmdset.
4. If the input string is empty -> check for CMD_NOINPUT command in
   current cmdset or fallback to error message. Exit.
5. The Command Parser is triggered, using the current cmdset to analyze the
   input string for possible command matches.
6. If multiple matches are found -> check for CMD_MULTIMATCH in current
   cmdset, or fallback to error message. Exit.
7. If no match was found -> check for CMD_NOMATCH in current cmdset or
   fallback to error message. Exit.
8. A single match was found. If this is a channel-command (i.e. the
   ommand name is that of a channel), --> check for CMD_CHANNEL in
   current cmdset or use channelhandler default. Exit.
9. At this point we have found a normal command. We assign useful variables to it that
   will be available to the command coder at run-time.
12. We have a unique cmdobject, primed for use. Call all hooks:
   `at_pre_cmd()`, `cmdobj.parse()`, `cmdobj.func()` and finally `at_post_cmd()`.
13. Return deferred that will fire with the return from `cmdobj.func()` (unused by default).
"""

from collections import defaultdict
from weakref import WeakValueDictionary
from traceback import format_exc
from copy import copy
import types
from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.internet.defer import inlineCallbacks, returnValue
from django.conf import settings
from evennia.evlib.utils import logger, utils
from evennia.evlib.utils.utils import string_suggestions, class_from_module


from django.utils.translation import gettext as _

_IN_GAME_ERRORS = settings.IN_GAME_ERRORS

__all__ = ("cmdhandler", "InterruptCommand")

_CMDSET_MERGE_CACHE = WeakValueDictionary()

# tracks recursive calls by each caller
# to avoid infinite loops (commands calling themselves)
_COMMAND_NESTING = defaultdict(lambda: 0)
_COMMAND_RECURSION_LIMIT = 10

# This decides which command parser is to be used.
# You have to restart the server for changes to take effect.
_COMMAND_PARSER = utils.variable_from_module(*settings.COMMAND_PARSER.rsplit(".", 1))

# System command names - import these variables rather than trying to
# remember the actual string constants. If not defined, Evennia
# hard-coded defaults are used instead.

# command to call if user just presses <return> with no input
CMD_NOINPUT = "__noinput_command"
# command to call if no command match was found
CMD_NOMATCH = "__nomatch_command"
# command to call if multiple command matches were found
CMD_MULTIMATCH = "__multimatch_command"
# command to call if found command is the name of a channel
CMD_CHANNEL = "__send_to_channel_command"
# command to call as the very first one when the user connects.
# (is expected to display the login screen)
CMD_LOGINSTART = "__unloggedin_look_command"

# Function for handling multiple command matches.
_SEARCH_AT_RESULT = utils.variable_from_module(*settings.SEARCH_AT_RESULT.rsplit(".", 1))

# Output strings. The first is the IN_GAME_ERRORS return, the second
# is the normal "production message to echo to the account.

_ERROR_UNTRAPPED = (
    """
An untrapped error occurred.
""",
    """
An untrapped error occurred. Please file a bug report detailing the steps to reproduce.
""",
)

_ERROR_CMDSETS = (
    """
A cmdset merger-error occurred. This is often due to a syntax
error in one of the cmdsets to merge.
""",
    """
A cmdset merger-error occurred. Please file a bug report detailing the
steps to reproduce.
""",
)

_ERROR_NOCMDSETS = (
    """
No command sets found! This is a critical bug that can have
multiple causes.
""",
    """
No command sets found! This is a sign of a critical bug.  If
disconnecting/reconnecting doesn't" solve the problem, try to contact
the server admin through" some other means for assistance.
""",
)

_ERROR_CMDHANDLER = (
    """
A command handler bug occurred. If this is not due to a local change,
please file a bug report with the Evennia project, including the
traceback and steps to reproduce.
""",
    """
A command handler bug occurred. Please notify staff - they should
likely file a bug report with the Evennia project.
""",
)

_ERROR_RECURSION_LIMIT = (
    "Command recursion limit ({recursion_limit}) " "reached for '{raw_cmdname}' ({cmdclass})."
)


# delayed imports
_GET_INPUT = None


class NoCmdSets(Exception):
    "No cmdsets found. Critical error."
    pass


class ExecSystemCommand(Exception):
    "Run a system command"

    def __init__(self, syscmd, sysarg):
        self.args = (syscmd, sysarg)  # needed by exception error handling
        self.syscmd = syscmd
        self.sysarg = sysarg


class ErrorReported(Exception):
    "Re-raised when a subsructure already reported the error"

    def __init__(self, raw_string):
        self.args = (raw_string,)
        self.raw_string = raw_string


# helper functions
class CmdHandler:

    def __init__(self, cmdobj):
        self.cmdobj = cmdobj

    def _msg_err(self, receiver, stringtuple):
        """
        Helper function for returning an error to the caller.

        Args:
            receiver (Object): object to get the error message.
            stringtuple (tuple): tuple with two strings - one for the
                _IN_GAME_ERRORS mode (with the traceback) and one with the
                production string (with a timestamp) to be shown to the user.

        """
        string = "{traceback}\n{errmsg}\n(Traceback was logged {timestamp})."
        timestamp = logger.timeformat()
        tracestring = format_exc()
        logger.log_trace()
        if _IN_GAME_ERRORS:
            receiver.msg(
                string.format(
                    traceback=tracestring, errmsg=stringtuple[0].strip(), timestamp=timestamp
                ).strip()
            )
        else:
            receiver.msg(
                string.format(
                    traceback=tracestring.splitlines()[-1],
                    errmsg=stringtuple[1].strip(),
                    timestamp=timestamp,
                ).strip()
            )


    def _progressive_cmd_run(self, cmd, generator, response=None):
        """
        Progressively call the command that was given in argument. Used
        when `yield` is present in the Command's `func()` method.

        Args:
            cmd (Command): the command itself.
            generator (GeneratorType): the generator describing the processing.
            reponse (str, optional): the response to send to the generator.

        Raises:
            ValueError: If the func call yields something not identifiable as a
                time-delay or a string prompt.

        Note:
            This function is responsible for executing the command, if
            the func() method contains 'yield' instructions.  The yielded
            value will be accessible at each step and will affect the
            process.  If the value is a number, just delay the execution
            of the command.  If it's a string, wait for the user input.

        """
        global _GET_INPUT
        if not _GET_INPUT:
            from evennia.utils.evmenu import get_input as _GET_INPUT

        try:
            if response is None:
                value = next(generator)
            else:
                value = generator.send(response)
        except StopIteration:
            pass
        else:
            if isinstance(value, (int, float)):
                utils.delay(value, self._progressive_cmd_run, cmd, generator)
            elif isinstance(value, str):
                _GET_INPUT(cmd.caller, value, self._process_input, cmd=cmd, generator=generator)
            else:
                raise ValueError("unknown type for a yielded value in command: {}".format(type(value)))


    def _process_input(self, caller, prompt, result, cmd, generator):
        """
        Specifically handle the get_input value to send to _progressive_cmd_run as
        part of yielding from a Command's `func`.

        Args:
            caller (Character, Account or Connection): the caller.
            prompt (str): The sent prompt.
            result (str): The unprocessed answer.
            cmd (Command): The command itself.
            generator (GeneratorType): The generator.

        Returns:
            result (bool): Always `False` (stop processing).

        """
        # We call it using a Twisted deferLater to make sure the input is properly closed.
        deferLater(reactor, 0, self._progressive_cmd_run, cmd, generator, response=result)
        return False

    @inlineCallbacks
    def _get_channel_cmdset(self, caller, account_or_obj, raw_string):
        """
        Helper-method; Get channel-cmdsets
        """
        # Create cmdset for all account's available channels
        try:
            channel_cmdset = yield CHANNELHANDLER.get_cmdset(account_or_obj)
            returnValue([channel_cmdset])
        except Exception:
            self._msg_err(caller, _ERROR_CMDSETS)
            raise ErrorReported(raw_string)

    @inlineCallbacks
    def get_cmdsets(self, caller, raw_string, merged_current=None, merged_stack=None):
        """
        Helper method; Get cmdset while making sure to trigger all
        hooks safely. Returns the stack and the valid options.
        """
        try:
            yield self.cmdobj.at_cmdset_get()
        except Exception:
            self._msg_err(caller, _ERROR_CMDSETS)
            raise ErrorReported(raw_string)
        if merged_current is None:
            merged_current = self.cmdobj.cmdset.current
        else:
            merged_current = merged_current + self.cmdobj.cmdset.current
        stack = list()
        stack.extend(self.cmdobj.cmdset.gather())
        if merged_stack is None:
            merged_stack = stack
        else:
            merged_stack.extend(stack)
        returnValue((merged_current, merged_stack))

    def get_extra_cmdsets(self, caller, merged_current):
        """
        'Extra' CmdSets are those provided by something other than the direct CmdSetHandler on
        a cmdobj. Examples include Exits, items in inventory, an Object's location, and Channels.

        Args:
            caller (cmdobj): The Executor of the command.

        Returns:
            cmdsets (list): The CmdSets to check.
        """
        return []

    @inlineCallbacks
    def get_and_merge_cmdsets(self, caller, ordered_objects, raw_string, error_to):
        """
        Gather all relevant cmdsets and merge them.

        Args:
            caller (Connection, Account or Object): The entity executing the command. Which
                type of object this is depends on the current game state; for example
                when the user is not logged in, this will be a Connection, when being OOC
                it will be an Account and when puppeting an object this will (often) be
                a Character Object. In the end it depends on where the cmdset is stored.
            ordered_objects (list): A list of objects that have a CmdSetHandler as .cmdset
                and implement the CmdSetHandler API. This will generally be [Connection, Account,
                PuppetObject] as explained in caller. Order isn't generally important for
                merging, but is preserved from CmdHandler.execute()
            raw_string (str): The input string. This is only used for error reporting.
            error_to (obj): An Evennia object that implements .msg(). For error reporting.

        Returns:
            cmdset (Deferred): This deferred fires with the merged cmdset
            result once merger finishes.

        Notes:
            The cdmsets are merged in order or generality, so that the
            Object's cmdset is merged last (and will thus take precedence
            over same-named and same-prio commands on Account and Connection).

        """
        try:
            current, cmdsets = None, None
            for obj in ordered_objects:
                current, cmdsets = yield obj.cmd.get_cmdsets(caller, raw_string, current, cmdsets)

            # weed out all non-found sets
            cmdsets = yield [cmdset for cmdset in cmdsets if cmdset and cmdset.key != "_EMPTY_CMDSET"]
            # report cmdset errors to user (these should already have been logged)
            yield [
                error_to.msg(cmdset.errmessage) for cmdset in cmdsets if cmdset.key == "_CMDSET_ERROR"
            ]

            if cmdsets:
                # faster to do tuple on list than to build tuple directly
                mergehash = tuple([id(cmdset) for cmdset in cmdsets])
                if mergehash in _CMDSET_MERGE_CACHE:
                    # cached merge exist; use that
                    cmdset = _CMDSET_MERGE_CACHE[mergehash]
                else:
                    # we group and merge all same-prio cmdsets separately (this avoids
                    # order-dependent clashes in certain cases, such as
                    # when duplicates=True)
                    tempmergers = {}
                    for cmdset in cmdsets:
                        prio = cmdset.priority
                        if prio in tempmergers:
                            # merge same-prio cmdset together separately
                            tempmergers[prio] = yield tempmergers[prio] + cmdset
                        else:
                            tempmergers[prio] = cmdset

                    # sort cmdsets after reverse priority (highest prio are merged in last)
                    cmdsets = yield sorted(list(tempmergers.values()), key=lambda x: x.priority)

                    # Merge all command sets into one, beginning with the lowest-prio one
                    cmdset = cmdsets[0]
                    for merging_cmdset in cmdsets[1:]:
                        cmdset = yield cmdset + merging_cmdset
                    # store the full sets for diagnosis
                    cmdset.merged_from = cmdsets
                    # cache
                    _CMDSET_MERGE_CACHE[mergehash] = cmdset
            else:
                cmdset = None
            local_obj_cmdsets = [cset for cset in cmdsets if cset.cmdsetobj not in ordered_objects and cset.object_cmdset]
            for cset in (cset for cset in local_obj_cmdsets if cset):
                cset.duplicates = cset.old_duplicates
            returnValue(cmdset)
        except ErrorReported:
            raise
        except Exception:
            self._msg_err(caller, _ERROR_CMDSETS)
            raise
            # raise ErrorReported

    @inlineCallbacks
    def _run_command(self, caller, cmd, cmdname, args, raw_cmdname, cmdset, cmdobjects, raw_string,
                     unformatted_raw_string, testing, **kwargs):
        """
        Helper function: This initializes and runs the Command
        instance once the parser has identified it as either a normal
        command or one of the system commands.

        Args:
            caller (cmdobj): A Connection, Account, Puppet, etc....
            cmd (Command): Command object
            cmdname (str): Name of command
            args (str): extra text entered after the identified command
            raw_cmdname (str): Name of Command, unaffected by eventual
                prefix-stripping (if no prefix-stripping, this is the same
                as cmdname).
            cmdset (CmdSet): Command sert the command belongs to (if any)..
            session (Connection): Connection of caller (if any).
            account (Account): Account of caller (if any).

        Returns:
            deferred (Deferred): this will fire with the return of the
                command's `func` method.

        Raises:
            RuntimeError: If command recursion limit was reached.

        """
        global _COMMAND_NESTING

        try:
            # Assign useful variables to the instance
            cmd.caller = caller
            cmd.cmdname = cmdname
            cmd.raw_cmdname = raw_cmdname
            cmd.cmdstring = cmdname  # deprecated
            cmd.args = args
            cmd.cmdset = cmdset
            cmd.session = cmdobjects.get('session', None)
            cmd.account = cmdobjects.get('account', None)
            cmd.puppet = cmdobjects.get('puppet', None)
            cmd.cmdobjects = cmdobjects
            cmd.raw_string = unformatted_raw_string
            # cmd.obj  # set via on-object cmdset handler for each command,
            # since this may be different for every command when
            # merging multuple cmdsets

            if hasattr(cmd, "obj") and hasattr(cmd.obj, "scripts"):
                # cmd.obj is automatically made available by the cmdhandler.
                # we make sure to validate its scripts.
                yield cmd.obj.scripts.validate()

            if testing:
                # only return the command instance
                returnValue(cmd)

            # assign custom kwargs to found cmd object
            for key, val in kwargs.items():
                setattr(cmd, key, val)

            _COMMAND_NESTING[caller] += 1
            if _COMMAND_NESTING[caller] > _COMMAND_RECURSION_LIMIT:
                err = _ERROR_RECURSION_LIMIT.format(
                    recursion_limit=_COMMAND_RECURSION_LIMIT,
                    raw_cmdname=raw_cmdname,
                    cmdclass=cmd.__class__,
                )
                raise RuntimeError(err)

            # pre-command hook
            abort = yield cmd.at_pre_cmd()
            if abort:
                # abort sequence
                returnValue(abort)

            # Parse and execute
            yield cmd.parse()

            # main command code
            # (return value is normally None)
            ret = cmd.func()
            if isinstance(ret, types.GeneratorType):
                # cmd.func() is a generator, execute progressively
                self._progressive_cmd_run(cmd, ret)
                yield None
            else:
                ret = yield ret

            # post-command hook
            yield cmd.at_post_cmd()

            if cmd.save_for_next:
                # store a reference to this command, possibly
                # accessible by the next command.
                caller.ndb.last_cmd = yield copy(cmd)
            else:
                caller.ndb.last_cmd = None

            # return result to the deferred
            returnValue(ret)

        except InterruptCommand:
            # Do nothing, clean exit
            pass
        except Exception:
            self._msg_err(caller, _ERROR_UNTRAPPED)
            raise ErrorReported(raw_string)
        finally:
            _COMMAND_NESTING[caller] -= 1

    def sort_cmdobjects(self, cmdobjects):
        return sorted([val for key, val in cmdobjects.items() if val], key=lambda obj: obj._cmd_sort)

    def error_cmdobjects(self, cmdobjects):
        """
        Returns which object shall have errors reported to it during command processing
        This is generally the 'deepest' in a stack of connections. Connection->Account->Object.

        Args:
            cmdobjects (list): The ordered list of cmdobjects generated in .execute().

        Returns:
            What object will be used for error reporting.
        """
        return cmdobjects[-1]

    def get_cmdobjects(self, session=None):
        if session is None:
            session = self.session
        return {'session': session}

    # Main command-handler function
    @inlineCallbacks
    def execute(self, raw_string, testing=False, cmdclass=None, cmdclass_key=None, error_to=None, session=None, **kwargs):
        """
        This is the main mechanism that handles any string sent to the engine.

        Args:
            caller (Connection, Account or Object): Object from which this
                command was called. which this was called from.  What this is
                depends on the game state.
            cmdobjects (dict): The Keys are string-names of the 'object types' of all
                the objects that should have their CmdSets retrieved. the Value is the objects
                themselves. example {'session': <obj>, 'account': <account>}
            raw_string (str): The command string as given on the command line.
            _testing (bool, optional): Used for debug purposes and decides if we
                should actually execute the command or not. If True, the
                command instance will be returned.
            session (Connection, optional): Relevant if callertype is "account" - the session will help
                retrieve the correct cmdsets from puppeted objects.
            cmdobj (Command, optional): If given a command instance, this will be executed using
                `called_by` as the caller, `raw_string` representing its arguments and (optionally)
                `cmdobj_key` as its input command name. No cmdset lookup will be performed but
                all other options apply as normal. This allows for running a specific Command
                within the command system mechanism.
            cmdobj_key (string, optional): Used together with `cmdobj` keyword to specify
                which cmdname should be assigned when calling the specified Command instance. This
                is made available as `self.cmdstring` when the Command runs.
                If not given, the command will be assumed to be called as `cmdobj.key`.

        Kwargs:
            kwargs (any): other keyword arguments will be assigned as named variables on the
                retrieved command object *before* it is executed. This is unused
                in default Evennia but may be used by code to set custom flags or
                special operating conditions for a command as it executes.

        Returns:
            deferred (Deferred): This deferred is fired with the return
            value of the command's `func` method.  This is not used in
            default Evennia.

        """

        cmdobjects = self.get_cmdobjects(session)

        # The first element in this list will probably be a ServerConnection. The last, in default Evennia,
        # would be a Connection, Account, or Puppet. The 'last' is used for Error reporting, to preserve
        # character mirroring.
        ordered_objects = self.sort_cmdobjects(cmdobjects)

        if error_to is None:
            error_to = self.error_cmdobjects(ordered_objects)
            if error_to is None:
                error_to = self.cmdobj

        # The caller is always the last in the link chain. Later code may change what's set on commands, but
        # command handler goes 'bottom up' to reach that point.
        caller = ordered_objects[-1]

        try:  # catch bugs in cmdhandler itself
            try:  # catch special-type commands
                if cmdclass:
                    # the command object is already given
                    cmd = cmdclass() if callable(cmdclass) else cmdclass
                    cmdname = cmdclass_key if cmdclass_key else cmd.key
                    args = raw_string
                    unformatted_raw_string = "%s%s" % (cmdname, args)
                    cmdset = None
                    raw_cmdname = cmdname
                    # session = session
                    # account = account

                else:
                    # no explicit cmdobject given, figure it out
                    cmdset = yield self.get_and_merge_cmdsets(
                        caller, ordered_objects, raw_string, error_to
                    )
                    if not cmdset:
                        # this is bad and shouldn't happen.
                        raise NoCmdSets
                    # store the completely unmodified raw string - including
                    # whitespace and eventual prefixes-to-be-stripped.
                    unformatted_raw_string = raw_string
                    raw_string = raw_string.strip()
                    if not raw_string:
                        # Empty input. Test for system command instead.
                        syscmd = yield cmdset.get(CMD_NOINPUT)
                        sysarg = ""
                        raise ExecSystemCommand(syscmd, sysarg)
                    # Parse the input string and match to available cmdset.
                    # This also checks for permissions, so all commands in match
                    # are commands the caller is allowed to call.
                    matches = yield _COMMAND_PARSER(raw_string, cmdset, caller)
                    # Deal with matches

                    if len(matches) > 1:
                        # We have a multiple-match
                        syscmd = yield cmdset.get(CMD_MULTIMATCH)
                        sysarg = _("There were multiple matches.")
                        if syscmd:
                            # use custom CMD_MULTIMATCH
                            syscmd.matches = matches
                        else:
                            # fall back to default error handling
                            sysarg = yield _SEARCH_AT_RESULT(
                                [match[2] for match in matches], caller, query=matches[0][0]
                            )
                        raise ExecSystemCommand(syscmd, sysarg)

                    cmdname, args, cmd, raw_cmdname = "", "", None, ""
                    if len(matches) == 1:
                        # We have a unique command match. But it may still be invalid.
                        match = matches[0]
                        cmdname, args, cmd, raw_cmdname = (match[0], match[1], match[2], match[5])

                    if not matches:
                        # No commands match our entered command
                        syscmd = yield cmdset.get(CMD_NOMATCH)
                        if syscmd:
                            # use custom CMD_NOMATCH command
                            sysarg = raw_string
                        else:
                            # fallback to default error text
                            sysarg = _("Command '%s' is not available.") % raw_string
                            suggestions = string_suggestions(
                                raw_string,
                                cmdset.get_all_cmd_keys_and_aliases(caller),
                                cutoff=0.7,
                                maxnum=3,
                            )
                            if suggestions:
                                sysarg += _(" Maybe you meant %s?") % utils.list_to_string(
                                    suggestions, _("or"), addquote=True
                                )
                            else:
                                sysarg += _(' Type "help" for help.')
                        raise ExecSystemCommand(syscmd, sysarg)

                    # Check if this is a Channel-cmd match.
                    if hasattr(cmd, "is_channel") and cmd.is_channel:
                        # even if a user-defined syscmd is not defined, the
                        # found cmd is already a system command in its own right.
                        syscmd = yield cmdset.get(CMD_CHANNEL)
                        if syscmd:
                            # replace system command with custom version
                            cmd = syscmd
                        cmd.session = session
                        sysarg = "%s:%s" % (cmdname, args)
                        raise ExecSystemCommand(cmd, sysarg)

                # A normal command.
                ret = yield self._run_command(caller, cmd, cmdname, args, raw_cmdname, cmdset, cmdobjects, raw_string,
                                              unformatted_raw_string, testing, **kwargs)
                returnValue(ret)

            except ErrorReported as exc:
                # this error was already reported, so we
                # catch it here and don't pass it on.
                logger.log_err("User input was: '%s'." % exc.raw_string)

            except ExecSystemCommand as exc:
                # Not a normal command: run a system command, if available,
                # or fall back to a return string.
                syscmd = exc.syscmd
                sysarg = exc.sysarg

                if syscmd:
                    ret = yield self._run_command(
                        caller, syscmd, syscmd.key, sysarg, unformatted_raw_string, cmdset, cmdobjects, raw_string,
                                              unformatted_raw_string, testing, **kwargs
                    )
                    returnValue(ret)
                elif sysarg:
                    # return system arg
                    error_to.msg(exc.sysarg)

            except NoCmdSets:
                # Critical error.
                logger.log_err("No cmdsets found: %s" % caller)
                error_to.msg(_ERROR_NOCMDSETS)

            except Exception:
                # We should not end up here. If we do, it's a programming bug.
                self._msg_err(error_to, _ERROR_UNTRAPPED)

        except Exception:
            # This catches exceptions in cmdhandler exceptions themselves
            self._msg_err(error_to, _ERROR_CMDHANDLER)


class SessionCmdHandler(CmdHandler):

    def __init__(self, cmdobj):
        self.cmdobj = cmdobj
        self.session = cmdobj

    def get_cmdobjects(self, session=None):
        if not session:
            session = self.cmdobj
        base = {
            'session': session
        }
        base.update(session.linked)
        return base


class AccountCmdHandler(CmdHandler):
    session = None

    def get_cmdobjects(self, session=None):
        cmdobjects = super().get_cmdobjects(session)
        cmdobjects['account'] = self.cmdobj
        return cmdobjects


class CharacterCmdHandler(CmdHandler):
    session = None

    def get_cmdobjects(self, session=None):
        cmdobjects = super().get_cmdobjects(session)
        cmdobjects['character'] = self.cmdobj
        if (session := cmdobjects.get('session', None)):
            cmdobjects['account'] = session.get_account()
            cmdobjects['puppet'] = session.get_puppet()
        return cmdobjects


class PuppetCmdHandler(CmdHandler):
    session = None

    def get_cmdobjects(self, session=None):
        cmdobjects = super().get_cmdobjects(session)
        cmdobjects['puppet'] = self.cmdobj
        if (session := cmdobjects.get('session', None)):
            cmdobjects['account'] = session.get_account()
            cmdobjects['character'] = session.get_pcharacter()
        return cmdobjects







