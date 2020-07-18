"""
Master configuration file for Evennia.

NOTE: NO MODIFICATIONS SHOULD BE MADE TO THIS FILE!

All settings changes should be done by copy-pasting the variable and
its value to <gamedir>/server/conf/settings.py.

Hint: Don't copy&paste over more from this file than you actually want
to change.  Anything you don't copy&paste will thus retain its commands
value - which may change as Evennia is developed. This way you can
always be sure of what you have changed and what is commands behaviour.

"""
from evennia.settings_default import *


######################################################################
# Evennia Database config
######################################################################

ATTRIBUTE_STORED_MODEL_RENAME = [
    (("players", "playerdb"), ("accounts", "accountdb")),
    (("typeclasses", "defaultplayer"), ("typeclasses", "defaultaccount")),
]


######################################################################
# Evennia pluggable modules
######################################################################
# Plugin modules extend Evennia in various ways. In the cases with no
# existing commands, there are examples of many of these modules
# in contrib/examples.

# The command parser module to use. See the commands module for which
# functions it must implement
COMMAND_PARSER = "evennia.commands.cmdparser.cmdparser"
# On a multi-match when search objects or commands, the user has the
# ability to search again with an index marker that differentiates
# the results. If multiple "box" objects
# are found, they can by commands be separated as 1-box, 2-box. Below you
# can change the regular expression used. The regex must have one
# have two capturing groups (?P<number>...) and (?P<name>...) - the commands
# parser expects this. It should also involve a number starting from 1.
# When changing this you must also update SEARCH_MULTIMATCH_TEMPLATE
# to properly describe the syntax.
SEARCH_MULTIMATCH_REGEX = r"(?P<name>.*)-(?P<number>[0-9]+)"
# To display multimatch errors in various listings we must display
# the syntax in a way that matches what SEARCH_MULTIMATCH_REGEX understand.
# The template will be populated with data and expects the following markup:
# {number} - the order of the multimatch, starting from 1; {name} - the
# name (key) of the multimatched entity; {aliases} - eventual
# aliases for the entity; {info} - extra info like #dbrefs for staff. Don't
# forget a line break if you want one match per line.
SEARCH_MULTIMATCH_TEMPLATE = " {name}-{number}{aliases}{info}\n"
# The handler that outputs errors when using any API-level search
# (not manager methods). This function should correctly report errors
# both for command- and object-searches. This allows full control
# over the error output (it uses SEARCH_MULTIMATCH_TEMPLATE by commands).
SEARCH_AT_RESULT = "evennia.utils.utils.at_search_result"
# Single characters to ignore at the beginning of a command. When set, e.g.
# cmd, @cmd and +cmd will all find a command "cmd" or one named "@cmd" etc. If
# you have defined two different commands cmd and @cmd you can still enter
# @cmd to exactly target the second one. Single-character commands consisting
# of only a prefix character will not be stripped. Set to the empty
# string ("") to turn off prefix ignore.
CMD_IGNORE_PREFIXES = "@&/+"
# The module holding text strings for the connection screen.
# This module should contain one or more variables
# with strings defining the look of the screen.
CONNECTION_SCREEN_MODULE = "server.conf.connection_screens"
# Delay to use before sending the evennia.syscmdkeys.CMD_LOGINSTART Command
# when a new session connects (this defaults the unloggedin-look for showing
# the connection screen). The delay is useful mainly for telnet, to allow
# client/server to establish client capabilities like color/mxp etc before
# sending any text. A value of 0.3 should be enough. While a good idea, it may
# cause issues with menu-logins and autoconnects since the menu will not have
# started when the autoconnects starts sending menu commands.
DELAY_CMD_LOGINSTART = 0.3
# A module that must exist - this holds the instructions Evennia will use to
# first prepare the database for use. Generally should not be changed. If this
# cannot be imported, bad things will happen.
INITIAL_SETUP_MODULE = "evennia.server.initial_setup"
# An optional module that, if existing, must hold a function
# named at_initial_setup(). This hook method can be used to customize
# the server's initial setup sequence (the very first startup of the system).
# The check will fail quietly if module doesn't exist or fails to load.
AT_INITIAL_SETUP_HOOK_MODULE = "server.conf.at_initial_setup"
# Module containing your custom at_server_start(), at_server_reload() and
# at_server_stop() methods. These methods will be called every time
# the server starts, reloads and resets/stops respectively.
AT_SERVER_STARTSTOP_MODULE = "server.conf.at_server_startstop"
# List of one or more module paths to modules containing a function start_
# plugin_services(application). This module will be called with the main
# Evennia Server application when the Server is initiated.
# It will be called last in the startup sequence.
SERVER_SERVICES_PLUGIN_MODULES = ["server.conf.server_services_plugins"]
# List of one or more module paths to modules containing a function
# start_plugin_services(application). This module will be called with the
# main Evennia Portal application when the Portal is initiated.
# It will be called last in the startup sequence.
PORTAL_SERVICES_PLUGIN_MODULES = ["server.conf.portal_services_plugins"]
# Module holding MSSP meta data. This is used by MUD-crawlers to determine
# what type of game you are running, how many accounts you have etc.
MSSP_META_MODULE = "server.conf.mssp"
# Module for web plugins.
WEB_PLUGINS_MODULE = "server.conf.web_plugins"
# Tuple of modules implementing lock functions. All callable functions
# inside these modules will be available as lock functions.
LOCK_FUNC_MODULES = ("evennia.locks.lockfuncs", "server.conf.lockfuncs")
# Module holding handlers for managing incoming data from the client. These
# will be loaded in order, meaning functions in later modules may overload
# previous ones if having the same name.
INPUT_FUNC_MODULES = ["evennia.server.inputfuncs", "server.conf.inputfuncs"]
# Modules that contain prototypes for use with the spawner mechanism.
PROTOTYPE_MODULES = ["world.prototypes"]
# Modules containining Prototype functions able to be embedded in prototype
# definitions from in-game.
PROT_FUNC_MODULES = ["evennia.muxlib.prototypes.protfuncs"]


######################################################################
# Default command sets and commands
######################################################################

# Command set used on session before account has logged in
CMDSET_UNLOGGEDIN = "commands.default_cmdsets.UnloggedinCmdSet"
# (Note that changing these three following cmdset paths will only affect NEW
# created characters/objects, not those already in play. So if you want to
# change this and have it apply to every object, it's recommended you do it
# before having created a lot of objects (or simply reset the database after
# the change for simplicity)).
# Command set used on the logged-in session
CMDSET_SESSION = "commands.default_cmdsets.SessionCmdSet"
# Default set for logged in account with characters (fallback)
CMDSET_CHARACTER = "commands.default_cmdsets.CharacterCmdSet"
# Command set for accounts without a character (ooc)
CMDSET_ACCOUNT = "commands.default_cmdsets.AccountCmdSet"

# Location to search for cmdsets if full path not given
CMDSET_PATHS = ["commands", "evennia", "evennia.contrib"]
# Fallbacks for cmdset paths that fail to load. Note that if you change the path for your
# commands cmdsets, you will also need to copy CMDSET_FALLBACKS after your change in your
# settings file for it to detect the change.
CMDSET_FALLBACKS = {
    CMDSET_CHARACTER: "evennia.commands.commands.cmdset_character.CharacterCmdSet",
    CMDSET_ACCOUNT: "evennia.commands.commands.cmdset_account.AccountCmdSet",
    CMDSET_SESSION: "evennia.commands.commands.cmdset_session.SessionCmdSet",
    CMDSET_UNLOGGEDIN: "evennia.commands.commands.cmdset_unloggedin.UnloggedinCmdSet",
}
# Parent class for all commands commands. Changing this class will
# modify all commands commands, so do so carefully.
COMMAND_DEFAULT_CLASS = "evennia.commands.commands.muxcommand.MuxCommand"
# Command.arg_regex is a regular expression desribing how the arguments
# to the command must be structured for the command to match a given user
# input. By commands there is no restriction as long as the input string
# starts with the command name.
COMMAND_DEFAULT_ARG_REGEX = None
# By commands, Command.msg will only send data to the Session calling
# the Command in the first place. If set, Command.msg will instead return
# data to all Sessions connected to the Account/Character associated with
# calling the Command. This may be more intuitive for users in certain
# multisession modes.
COMMAND_DEFAULT_MSG_ALL_SESSIONS = False
# The help category of a command if not otherwise specified.
COMMAND_DEFAULT_HELP_CATEGORY = "general"
# The commands lockstring of a command.
COMMAND_DEFAULT_LOCKS = ""
# The Channel Handler is responsible for managing all available channels. By
# commands it builds the current channels into a channel-cmdset that it feeds
# to the cmdhandler. Overloading this can completely change how Channels
# are identified and called.
CHANNEL_HANDLER_CLASS = "evennia.comms.channelhandler.ChannelHandler"
# The (commands) Channel Handler will create a command to represent each
# channel, creating it with the key of the channel, its aliases, locks etc. The
# commands class logs channel messages to a file and allows for /history.  This
# setting allows to override the command class used with your own.
# If you implement CHANNEL_HANDLER_CLASS, you can change this directly and will
# likely not need this setting.
CHANNEL_COMMAND_CLASS = "evennia.comms.channelhandler.ChannelCommand"

######################################################################
# Typeclasses and other paths
######################################################################

# These are paths that will be prefixed to the paths given if the
# immediately entered path fail to find a typeclass. It allows for
# shorter input strings. They must either base off the game directory
# or start from the evennia library.
TYPECLASS_PATHS = [
    "typeclasses",
    "evennia",
    "evennia.contrib",
    "evennia.contrib.tutorial_examples",
]

# Typeclass for account objects (linked to a character) (fallback)
BASE_ACCOUNT_TYPECLASS = "typeclasses.accounts.Account"
# Typeclass and base for all objects (fallback)
BASE_OBJECT_TYPECLASS = "typeclasses.objects.Object"
# Typeclass for character objects linked to an account (fallback)
BASE_CHARACTER_TYPECLASS = "typeclasses.characters.Character"
# Typeclass for rooms (fallback)
BASE_ROOM_TYPECLASS = "typeclasses.rooms.Room"
# Typeclass for Exit objects (fallback).
BASE_EXIT_TYPECLASS = "typeclasses.exits.Exit"
# Typeclass for Channel (fallback).
BASE_CHANNEL_TYPECLASS = "typeclasses.channels.Channel"
# Typeclass for Scripts (fallback). You usually don't need to change this
# but create custom variations of scripts on a per-case basis instead.
BASE_SCRIPT_TYPECLASS = "typeclasses.scripts.Script"
# The commands home location used for all objects. This is used as a
# fallback if an object's normal home location is deleted. Default
# is Limbo (#2).
DEFAULT_HOME = "#2"
# The start position for new characters. Default is Limbo (#2).
#  MULTISESSION_MODE = 0, 1 - used by commands unloggedin create command
#  MULTISESSION_MODE = 2, 3 - used by commands character_create command
START_LOCATION = "#2"
# Lookups of Attributes, Tags, Nicks, Aliases can be aggressively
# cached to avoid repeated database hits. This often gives noticeable
# performance gains since they are called so often. Drawback is that
# if you are accessing the database from multiple processes (such as
# from a website -not- running Evennia's own webserver) data may go
# out of sync between the processes. Keep on unless you face such
# issues.
TYPECLASS_AGGRESSIVE_CACHE = True

######################################################################
# Options and validators
######################################################################

# Options available on Accounts. Each such option is described by a
# class available from evennia.OPTION_CLASSES, in turn making use
# of validators from evennia.VALIDATOR_FUNCS to validate input when
# the user changes an option. The options are accessed through the
# `Account.options` handler.

# ("Description", 'Option Class name in evennia.OPTION_CLASS_MODULES', 'Default Value')

OPTIONS_ACCOUNT_DEFAULT = {
    "border_color": ("Headers, footers, table borders, etc.", "Color", "n"),
    "header_star_color": ("* inside Header lines.", "Color", "n"),
    "header_text_color": ("Text inside Header lines.", "Color", "w"),
    "header_fill": ("Fill for Header lines.", "Text", "="),
    "separator_star_color": ("* inside Separator lines.", "Color", "n"),
    "separator_text_color": ("Text inside Separator lines.", "Color", "w"),
    "separator_fill": ("Fill for Separator Lines.", "Text", "-"),
    "footer_star_color": ("* inside Footer lines.", "Color", "n"),
    "footer_text_color": ("Text inside Footer Lines.", "Color", "n"),
    "footer_fill": ("Fill for Footer Lines.", "Text", "="),
    "column_names_color": ("Table column header text.", "Color", "w"),
    "help_category_color": ("Help category names.", "Color", "n"),
    "help_entry_color": ("Help entry names.", "Color", "n"),
    "timezone": ("Timezone for dates. @tz for a list.", "Timezone", "UTC"),
}
# Modules holding Option classes, responsible for serializing the option and
# calling validator functions on it. Same-named functions in modules added
# later in this list will override those added earlier.
OPTION_CLASS_MODULES = ["evennia.utils.optionclasses"]
# Module holding validator functions. These are used as a resource for
# validating options, but can also be used as input validators in general.
# Same-named functions in modules added later in this list will override those
# added earlier.
VALIDATOR_FUNC_MODULES = ["evennia.utils.validatorfuncs"]

######################################################################
# Batch processors
######################################################################

# Python path to a directory to be searched for batch scripts
# for the batch processors (.ev and/or .py files).
BASE_BATCHPROCESS_PATHS = [
    "world",
    "evennia.contrib",
    "evennia.contrib.tutorial_examples",
]

######################################################################
# Game Time setup
######################################################################

# You don't actually have to use this, but it affects the routines in
# evennia.utils.gametime.py and allows for a convenient measure to
# determine the current in-game time. You can of course interpret
# "week", "month" etc as your own in-game time units as desired.

# The time factor dictates if the game world runs faster (timefactor>1)
# or slower (timefactor<1) than the real world.
TIME_FACTOR = 2.0
# The starting point of your game time (the epoch), in seconds.
# In Python a value of 0 means Jan 1 1970 (use negatives for earlier
# start date). This will affect the returns from the utils.gametime
# module. If None, the server's first start-time is used as the epoch.
TIME_GAME_EPOCH = None
# Normally, game time will only increase when the server runs. If this is True,
# game time will not pause when the server reloads or goes offline. This setting
# together with a time factor of 1 should keep the game in sync with
# the real time (add a different epoch to shift time)
TIME_IGNORE_DOWNTIMES = False

######################################################################
# Inlinefunc, PrototypeFuncs
######################################################################
# Evennia supports inline function preprocessing. This allows users
# to supply inline calls on the form $func(arg, arg, ...) to do
# session-aware text formatting and manipulation on the fly. If
# disabled, such inline functions will not be parsed.
INLINEFUNC_ENABLED = False
# Only functions defined globally (and not starting with '_') in
# these modules will be considered valid inlinefuncs. The list
# is loaded from left-to-right, same-named functions will overload
INLINEFUNC_MODULES = ["evennia.utils.inlinefuncs", "server.conf.inlinefuncs"]
# Module holding handlers for OLCFuncs. These allow for embedding
# functional code in prototypes
PROTOTYPEFUNC_MODULES = ["evennia.utils.prototypefuncs", "server.conf.prototypefuncs"]

######################################################################
# Global Scripts
######################################################################

# Global scripts started here will be available through
# 'evennia.GLOBAL_SCRIPTS.key'. The scripts will survive a reload and be
# recreated automatically if deleted. Each entry must have the script keys,
# whereas all other fields in the specification are optional. If 'typeclass' is
# not given, BASE_SCRIPT_TYPECLASS will be assumed.  Note that if you change
# typeclass for the same key, a new Script will replace the old one on
# `evennia.GLOBAL_SCRIPTS`.
GLOBAL_SCRIPTS = {
    # 'key': {'typeclass': 'typeclass.path.here',
    #         'repeats': -1, 'interval': 50, 'desc': 'Example script'},
}

######################################################################
# Default Account setup and access
######################################################################

# Different Multisession modes allow a player (=account) to connect to the
# game simultaneously with multiple clients (=sessions). In modes 0,1 there is
# only one character created to the same name as the account at first login.
# In modes 2,3 no commands character will be created and the MAX_NR_CHARACTERS
# value (below) defines how many characters the commands char_create command
# allow per account.
#  0 - single session, one account, one character, when a new session is
#      connected, the old one is disconnected
#  1 - multiple sessions, one account, one character, each session getting
#      the same data
#  2 - multiple sessions, one account, many characters, one session per
#      character (disconnects multiplets)
#  3 - like mode 2, except multiple sessions can puppet one character, each
#      session getting the same data.
MULTISESSION_MODE = 0
# The maximum number of characters allowed by the commands ooc char-creation command
MAX_NR_CHARACTERS = 1
# The access hierarchy, in climbing order. A higher permission in the
# hierarchy includes access of all levels below it. Used by the perm()/pperm()
# lock functions, which accepts both plural and singular (Admin & Admins)
PERMISSION_HIERARCHY = [
    "Guest",  # note-only used if GUEST_ENABLED=True
    "Player",
    "Helper",
    "Builder",
    "Admin",
    "Developer",
]
# The commands permission given to all new accounts
PERMISSION_ACCOUNT_DEFAULT = "Player"
# Default sizes for client window (in number of characters), if client
# is not supplying this on its own
CLIENT_DEFAULT_WIDTH = 78
# telnet standard height is 24; does anyone use such low-res displays anymore?
CLIENT_DEFAULT_HEIGHT = 45
# Help output from CmdHelp are wrapped in an EvMore call
# (excluding webclient with separate help popups). If continuous scroll
# is preferred, change 'HELP_MORE' to False. EvMORE uses CLIENT_DEFAULT_HEIGHT
HELP_MORE = True
# Set rate limits per-IP on account creations and login attempts
CREATION_THROTTLE_LIMIT = 2
CREATION_THROTTLE_TIMEOUT = 10 * 60
LOGIN_THROTTLE_LIMIT = 5
LOGIN_THROTTLE_TIMEOUT = 5 * 60


######################################################################
# Guest accounts
######################################################################

# This enables guest logins, by commands via "connect guest". Note that
# you need to edit your login screen to inform about this possibility.
GUEST_ENABLED = False
# Typeclass for guest account objects (linked to a character)
BASE_GUEST_TYPECLASS = "typeclasses.accounts.Guest"
# The permission given to guests
PERMISSION_GUEST_DEFAULT = "Guests"
# The commands home location used for guests.
GUEST_HOME = DEFAULT_HOME
# The start position used for guest characters.
GUEST_START_LOCATION = START_LOCATION
# The naming convention used for creating new guest
# accounts/characters. The size of this list also determines how many
# guests may be on the game at once. The commands is a maximum of nine
# guests, named Guest1 through Guest9.
GUEST_LIST = ["Guest" + str(s + 1) for s in range(9)]

######################################################################
# In-game Channels created from server start
######################################################################

# The mudinfo channel must always exist; it is used by Evennia itself to
# relay status messages, connection info etc to staff. The superuser will be
# automatically subscribed to this channel and it will be recreated on a
# reload if deleted. This is a dict specifying the kwargs needed to create
# the channel .
CHANNEL_MUDINFO = {
    "key": "MudInfo",
    "aliases": "",
    "desc": "Connection log",
    "locks": "control:perm(Developer);listen:perm(Admin);send:false()",
}
# These are additional channels to offer. Usually, at least 'public'
# should exist. The superuser will automatically be subscribed to all channels
# in this list. New entries will be created on the next reload. But
# removing or updating a same-key channel from this list will NOT automatically
# change/remove it in the game, that needs to be done manually.
DEFAULT_CHANNELS = [
    # public channel
    {
        "key": "Public",
        "aliases": ("pub"),
        "desc": "Public discussion",
        "locks": "control:perm(Admin);listen:all();send:all()",
    }
]
# Optional channel info (same form as CHANNEL_MUDINFO) for the channel to
# receive connection messages ("<account> has (dis)connected").  While the
# MudInfo channel will also receieve this info, this channel is meant for
# non-staffers.
CHANNEL_CONNECTINFO = None

######################################################################
# External Connections
######################################################################

# Note: You do *not* have to make your MUD open to
# the public to use the external connections, they
# operate as long as you have an internet connection,
# just like stand-alone chat clients.

# The Evennia Game Index is a dynamic listing of Evennia games. You can add your game
# to this list also if it is in closed pre-alpha development.
GAME_INDEX_ENABLED = False
# This dict
GAME_INDEX_LISTING = {
    "game_name": SERVERNAME,
    "game_status": "pre-alpha",  # pre-alpha, alpha, beta or launched
    "short_description": GAME_SLOGAN,
    "long_description": "",
    "listing_contact": "",  # email
    "telnet_hostname": "",  # mygame.com
    "telnet_port": "",  # 1234
    "game_website": "",  # http://mygame.com
    "web_client_url": "",  # http://mygame.com/webclient
}
# Evennia can connect to external IRC channels and
# echo what is said on the channel to IRC and vice
# versa. Obs - make sure the IRC network allows bots.
# When enabled, command @irc2chan will be available in-game
# IRC requires that you have twisted.words installed.
IRC_ENABLED = False
# RSS allows to connect RSS feeds (from forum updates, blogs etc) to
# an in-game channel. The channel will be updated when the rss feed
# updates. Use @rss2chan in game to connect if this setting is
# active. OBS: RSS support requires the python-feedparser package to
# be installed (through package manager or from the website
# http://code.google.com/p/feedparser/)
RSS_ENABLED = False
RSS_UPDATE_INTERVAL = 60 * 10  # 10 minutes
# Grapevine (grapevine.haus) is a network for listing MUDs as well as allow
# users of said MUDs to communicate with each other on shared channels. To use,
# your game must first be registered by logging in and creating a game entry at
# https://grapevine.haus. Evennia links grapevine channels to in-game channels
# with the @grapevine2chan command, available once this flag is set
# Grapevine requires installing the pyopenssl library (pip install pyopenssl)
GRAPEVINE_ENABLED = False
# Grapevine channels to allow connection to. See https://grapevine.haus/chat
# for the available channels. Only channels in this list can be linked to in-game
# channels later.
GRAPEVINE_CHANNELS = ["gossip", "testing"]
# Grapevine authentication. Register your game at https://grapevine.haus to get
# them. These are secret and should thus be overridden in secret_settings file
GRAPEVINE_CLIENT_ID = ""
GRAPEVINE_CLIENT_SECRET = ""

######################################################################
# Django web features
######################################################################

# While DEBUG is False, show a regular server error page on the web
# stuff, email the traceback to the people in the ADMINS tuple
# below. If True, show a detailed traceback for the web
# browser to display. Note however that this will leak memory when
# active, so make sure to turn it off for a production server!
DEBUG = False
# Emails are sent to these people if the above DEBUG value is False. If you'd
# rather prefer nobody receives emails, leave this commented out or empty.
ADMINS = ()  # 'Your Name', 'your_email@domain.com'),)
# These guys get broken link notifications when SEND_BROKEN_LINK_EMAILS is True.
MANAGERS = ADMINS
# This is a public point of contact for players or the public to contact
# a staff member or administrator of the site. It is publicly posted.
STAFF_CONTACT_EMAIL = None
# Absolute path to the directory that holds file uploads from web apps.
# Example: "/home/media/media.lawrence.com"
MEDIA_ROOT = os.path.join(GAME_DIR, "web", "media")
# If using Sites/Pages from the web admin, this value must be set to the
# database-id of the Site (domain) we want to use with this game's Pages.
SITE_ID = 1
# The age for sessions.
# Default: 1209600 (2 weeks, in seconds)
SESSION_COOKIE_AGE = 1209600
# Session cookie domain
# Default: None
SESSION_COOKIE_DOMAIN = None
# The name of the cookie to use for sessions.
# Default: 'sessionid'
SESSION_COOKIE_NAME = "sessionid"
# Should the session expire when the browser closes?
# Default: False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
# Where to find locales (no need to change this, most likely)
LOCALE_PATHS = [os.path.join(EVENNIA_DIR, "locale/")]
# This should be turned off unless you want to do tests with Django's
# development webserver (normally Evennia runs its own server)
SERVE_MEDIA = False
# The master urlconf file that contains all of the sub-branches to the
# applications. Change this to add your own URLs to the website.
ROOT_URLCONF = "web.urls"
# Where users are redirected after logging in via contrib.auth.login.
LOGIN_REDIRECT_URL = "/"
# Where to redirect users when using the @login_required decorator.
LOGIN_URL = reverse_lazy("login")
# Where to redirect users who wish to logout.
LOGOUT_URL = reverse_lazy("logout")
# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = "/media/"
# URL prefix for admin media -- CSS, JavaScript and images. Make sure
# to use a trailing slash. Django1.4+ will look for admin files under
# STATIC_URL/admin.
STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(GAME_DIR, "web", "static")

# Location of static data to overload the defaults from
# evennia/web/webclient and evennia/web/website's static/ dirs.
STATICFILES_DIRS = [os.path.join(GAME_DIR, "web", "static_overrides")]
# Patterns of files in the static directories. Used here to make sure that
# its readme file is preserved but unused.
STATICFILES_IGNORE_PATTERNS = ["README.md"]
# The name of the currently selected web template. This corresponds to the
# directory names shown in the templates directory.
WEBSITE_TEMPLATE = "website"
WEBCLIENT_TEMPLATE = "webclient"
# The commands options used by the webclient
WEBCLIENT_OPTIONS = {
    "gagprompt": True,  # Gags prompt from the output window and keep them
    # together with the input bar
    "helppopup": False,  # Shows help files in a new popup window
    "notification_popup": False,  # Shows notifications of new messages as
    # popup windows
    "notification_sound": False  # Plays a sound for notifications of new
    # messages
}

# We setup the location of the website template as well as the admin site.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(GAME_DIR, "web", "template_overrides", WEBSITE_TEMPLATE),
            os.path.join(GAME_DIR, "web", "template_overrides", WEBCLIENT_TEMPLATE),
            os.path.join(GAME_DIR, "web", "template_overrides"),
            os.path.join(EVENNIA_DIR, "web", "website", "templates", WEBSITE_TEMPLATE),
            os.path.join(EVENNIA_DIR, "web", "website", "templates"),
            os.path.join(EVENNIA_DIR, "web", "webclient", "templates", WEBCLIENT_TEMPLATE),
            os.path.join(EVENNIA_DIR, "web", "webclient", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.media",
                "django.template.context_processors.debug",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
                "evennia.web.utils.general_context.general_context",
            ],
            # While true, show "pretty" error messages for template syntax errors.
            "debug": DEBUG,
        },
    }
]

# MiddleWare are semi-transparent extensions to Django's functionality.
# see http://www.djangoproject.com/documentation/middleware/ for a more detailed
# explanation.
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",  # 1.4?
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "evennia.web.utils.middleware.SharedLoginMiddleware",
]

######################################################################
# Evennia components
######################################################################

# Global and Evennia-specific apps. This ties everything together so we can
# refer to app models and perform DB syncs.
INSTALLED_APPS += [
    "evennia.muxlib.accounts",
    "evennia.muxlib.objects",
    "evennia.muxlib.comms",
    "evennia.muxlib.help",
    "evennia.muxlib.scripts",
]

# The user profile extends the User object with more functionality;
# This should usually not be changed.
AUTH_USER_MODEL = "accounts.AccountDB"

# Password validation plugins
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "evennia.server.validators.EvenniaPasswordValidator"},
]

# Username validation plugins
AUTH_USERNAME_VALIDATORS = [
    {"NAME": "django.contrib.auth.validators.ASCIIUsernameValidator"},
    {"NAME": "django.core.validators.MinLengthValidator", "OPTIONS": {"limit_value": 3},},
    {"NAME": "django.core.validators.MaxLengthValidator", "OPTIONS": {"limit_value": 30},},
    {"NAME": "evennia.server.validators.EvenniaUsernameAvailabilityValidator"},
]

# Use a custom test runner that just tests Evennia-specific apps.
TEST_RUNNER = "evennia.server.tests.testrunner.EvenniaTestSuiteRunner"

# Messages and Bootstrap don't classify events the same way; this setting maps
# messages.error() to Bootstrap 'danger' classes.
MESSAGE_TAGS = {messages.ERROR: "danger"}

# Django REST Framework settings
REST_FRAMEWORK = {
    # django_filters allows you to specify search fields for models in an API View
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    # whether to paginate results and how many per page
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 25,
    # require logged in users to call API so that access checks can work on them
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated",],
    # These are the different ways people can authenticate for API requests - via
    # session or with user/password. Other ways are possible, such as via tokens
    # or oauth, but require additional dependencies.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # commands permission checks used by the EvenniaPermission class
    "DEFAULT_CREATE_PERMISSION": "builder",
    "DEFAULT_LIST_PERMISSION": "builder",
    "DEFAULT_VIEW_LOCKS": ["examine"],
    "DEFAULT_DESTROY_LOCKS": ["delete"],
    "DEFAULT_UPDATE_LOCKS": ["control", "edit"],
    # No throttle class set by commands. Setting one also requires a cache backend to be specified.
}

# To enable the REST api, turn this to True
REST_API_ENABLED = False

######################################################################
# Networking Replaceables
######################################################################
# This allows for replacing the very core of the infrastructure holding Evennia
# together with your own variations. You should usually never have to touch
# this, and if so, you really need to know what you are doing.

# The Base Session Class is used as a parent class for all Protocols such as
# Telnet and SSH.) Changing this could be really dangerous. It will cascade
# to tons of classes. You generally shouldn't need to touch protocols.
BASE_SESSION_CLASS = "evennia.server.session.Session"

# Telnet Protocol inherits from whatever above BASE_SESSION_CLASS is specified.
# It is used for all telnet connections, and is also inherited by the SSL Protocol
# (which is just TLS + Telnet).
TELNET_PROTOCOL_CLASS = "evennia.portal.telnet.TelnetProtocol"
SSL_PROTOCOL_CLASS = "evennia.portal.ssl.SSLProtocol"

# Websocket Client Protocol. This inherits from BASE_SESSION_CLASS. It is used
# for all webclient connections.
WEBSOCKET_PROTOCOL_CLASS = "evennia.portal.webclient.WebSocketClient"

# Protocol for the SSH interface. This inherits from BASE_SESSION_CLASS.
SSH_PROTOCOL_CLASS = "evennia.portal.ssh.SshProtocol"

# Server-side session class used. This will inherit from BASE_SESSION_CLASS.
# This one isn't as dangerous to replace.
SERVER_SESSION_CLASS = "evennia.server.serversession.ServerSession"

# The Server SessionHandler manages all ServerSessions, handling logins,
# ensuring the login process happens smoothly, handling expected and
# unexpected disconnects. You shouldn't need to touch it, but you can.
# Replace it to implement altered game logic.
SERVER_SESSION_HANDLER_CLASS = "evennia.server.sessionhandler.ServerSessionHandler"

# The Portal SessionHandler manages all incoming connections regardless of
# the protocol in use. It is responsible for keeping them going and informing
# the Server Session Handler of the connections and synchronizing them across the
# AMP connection. You shouldn't ever need to change this. But you can.
PORTAL_SESSION_HANDLER_CLASS = "evennia.portal.portalsessionhandler.PortalSessionHandler"


# These are members / properties / attributes kept on both Server and
# Portal Sessions. They are sync'd at various points, such as logins and
# reloads. If you add to this, you may need to adjust the class __init__
# so the additions have somewhere to go. These must be simple things that
# can be pickled - stuff you could serialize to JSON is best.
SESSION_SYNC_ATTRS = (
    "protocol_key",
    "address",
    "suid",
    "sessid",
    "uid",
    "csessid",
    "uname",
    "logged_in",
    "puid",
    "conn_time",
    "cmd_last",
    "cmd_last_visible",
    "cmd_total",
    "protocol_flags",
    "server_data",
    "cmdset_storage_string",
)

# The following are used for the communications between the Portal and Server.
# Very dragons territory.
AMP_SERVER_PROTOCOL_CLASS = "evennia.portal.amp_server.AMPServerProtocol"
AMP_CLIENT_PROTOCOL_CLASS = "evennia.server.amp_client.AMPServerClientProtocol"


######################################################################
# Django extensions
######################################################################

# Django extesions are useful third-party tools that are not
# always included in the commands django distro.
try:
    import django_extensions  # noqa

    INSTALLED_APPS = INSTALLED_APPS.append("django_extensions")
except ImportError:
    # Django extensions are not installed in all distros.
    pass

#######################################################################
# SECRET_KEY
#######################################################################
# This is the signing key for the cookies generated by Evennia's
# web interface.
#
# It is a fallback for the SECRET_KEY setting in settings.py, which
# is randomly seeded when settings.py is first created. If copying
# from here, make sure to change it!
SECRET_KEY = "changeme!(*#&*($&*(#*(&SDFKJJKLS*(@#KJAS"
