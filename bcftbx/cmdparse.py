########################################################################
#
# cmdparse.py
#
#########################################################################

"""
Provides a CommandParser class for handling command lines of the form::

    PROG COMMAND OPTION ARGS

where different sets of options can be defined based on the initial
command.

The CommandParser can support arbitrary 'subparser backends' which are
created to parse the ARGS list for each defined COMMAND. The default
subparser is the 'optparse.OptionParser' class, but this can be swapped
for arbitrary subparser (for example, the 'argparse.ArgumentParser'
class) when the CommandParser is created.

In addition to the core CommandParser class, there are a number of
supporting functions that can be used with any optparse- or
argparse-based parser instance, to add the following 'standard'
options:

* --nprocessors
* --runner
* --no-save
* --dry-run
* --debug

"""

__version__ = "1.0.2"

#######################################################################
# Imports
#######################################################################

import os
import sys
import optparse
import argparse
from utils import OrderedDictionary

#######################################################################
# Classes
#######################################################################

# Command parser
class CommandParser(object):
    """Class defining multiple command line parsers

    This parser can process command lines of the form

    PROG CMD OPTIONS ARGS

    where different sets of options can be defined based on the major
    command ('CMD') supplied at the start of the line.

    Usage:

    Create a simple CommandParser which uses optparse.OptionParser as
    the default subparser backend using:

    >>> p = CommandParser()
    
    Alternatively, specify argparse.ArgumentParser as the subparser
    using:

    >>> p = CommandParser(subparser=argparser.ArgumentParser)

    Add a 'setup' command:

    >>> p.add_command('setup',usage='%prog setup OPTIONS ARGS')

    Add options to the 'setup' command using the appropriate methods
    of the subparser (e.g. 'add_argument' for an
    ArgumentParser instance).

    For example:

    >>> p.parser_for('info').add_argument('-f',...)

    To process a command line, use the 'parse_args' method, for
    example for an OptionParser-based subparser:

    >>> cmd,options,args = p.parse_args()

    Note that the exact form of the returned values depends on
    on the subparser instance; it will be the same as that
    returned by the 'parse_args' method of the subparser.

    """
    def __init__(self,description=None,version=None,subparser=None):
        """Create a command line parser
        with 'subparser' as the backend (default=OptionParser)
        This parser can process command lines of the form

        PROG CMD OPTIONS ARGS

        where different sets of options can be defined based
        on the major command supplied at the start.

        """
        self._name = os.path.basename(sys.argv[0])
        self._description = description
        self._version = version
        self._commands = OrderedDictionary()
        self._help = dict()
        if not subparser:
            subparser = optparse.OptionParser
        self._subparser = subparser

    def add_command(self,cmd,help=None,**args):
        """Add a major command to the CommandParser

        Adds a command, and creates and returns an initial
        subparser instance for it.

        Arguments:
          cmd: the command to be added
          help: (optional) help text for the command

        Other arguments are passed to the subparser instance
        when it is created i.e. 'usage', 'version',
        'description'.

        If 'version' isn't specified then the version
        supplied to the CommandParser object will be used.

        Returns:
          Subparser instance object for the command.

        """
        if cmd in self._commands:
            raise Exception("Command '%s' already defined" % cmd)
        if 'version' not in args:
            args['version'] = self._version
        p = self._subparser(**args)
        self._commands[cmd] = p
        self._help[cmd] = help
        return p

    def parser_for(self,cmd):
        """Return OptionParser for specified command

        Returns:
          The OptionParser object for the specified command.

        """
        return self._commands[cmd]

    def parse_args(self,argv=None):
        """Process a command line

        Parses a command line (either those supplied to the calling
        subprogram e.g. via the Python interpreter, or as a list).

        Once the command is identified from the first argument, the
        remainder of the arguments are passed to the 'parse_args'
        method of the appropriate subparser for that command.

        This method returns a tuple, with the first value being the
        command, and the rest of the values being those returned
        from the 'parse_args' method of the subparser.

        Arguments:
          argv: (optional) a list consisting of a command line.
            If not supplied then defaults to sys.argv[1:].

        Returns:
          A tuple of (cmd,...), where 'cmd' is the command, and '...'
          represents the values returned from the 'parse_args' method
          of the subparser. For example, using the default OptionParser
          backend returns (cmd,options,arguments), where 'options' and
          'arguments' are the options and arguments as returned by
          OptionParser.parse_args; using ArgumentParser as a backend
          returns (cmd,arguments).

        """
        # Collect arguments to process
        if argv is None:
            argv = sys.argv[1:]
        if not argv:
            self.error("Need to supply a command\n%s" %
                       self.print_available_commands())
        # Determine the major command and get the parser
        cmd = argv[0]
        self.handle_generic_commands(cmd)
        try:
            p = self.parser_for(cmd)
        except KeyError:
            # No parser
            self.error("Usage: %s COMMAND [options] [args...]\n\n"
                       "%s: error: no such command: %s" %
                       (self._name,self._name,cmd))
        # Parse the remaining arguments and return
        if isinstance(p,argparse.ArgumentParser):
            options = p.parse_args(argv[1:])
            return (cmd,options)
        # else:
        options,arguments = p.parse_args(argv[1:])
        return (cmd,options,arguments)

    def error(self,message):
        """Exit with error message

        """
        sys.stderr.write("%s\n" % message)
        sys.exit(1)

    def handle_generic_commands(self,cmd):
        """Process 'generic' commands e.g. 'help'

        """
        if cmd in ('-h','--help','help'):
            print("Usage: %s COMMAND [options] [args...]" % self._name)
            if self._description is not None:
                print("\n%s" % self._description)
            print("%s" % self.print_available_commands())
            sys.exit(0)
        if cmd in ('--version',):
            if self._version is not None:
                version_str = self._version
                print("%s" % version_str.replace('%prog',self._name))
            sys.exit(0)

    def list_commands(self):
        """Return the list of commands

        """
        return self._commands.keys()

    def print_available_commands(self):
        """Pretty-print available commands

        Returns a 'pretty-printed' string for all options and commands,
        with standard whitespace formatting.

        """
        lines = ["\nOptions:"]
        # Add generic commands
        if self._version is not None:
            lines.append(self.print_command("--version",
                                            "show program's version number and exit"))
            lines.append(self.print_command("-h, --help, help",
                                            "show this help message and exit"))
        # Add custom commands
        lines.append("\nAvailable commands:")
        for cmd in self.list_commands():
            lines.append(self.print_command(cmd,self._help[cmd]))
        lines.append("")
        return '\n'.join(lines)

    def print_command(self,cmd,message=None):
        """Print a line for a single command

        Returns a 'pretty-printed' line for the specified command
        and text, with standard whitespace formatting.

        """
        text = ['  ',cmd]
        width = 22
        if len(cmd) < width:
            text.append(' '*(width-len(cmd)))
        else:
            text.append('\n  '+' '*width)
        if message is not None:
            text.append(message)
        return ''.join(text)

#######################################################################
# Functions
#######################################################################

def add_nprocessors_option(parser,default_nprocessors,default_display=None):
    """Add a '--nprocessors' option to a parser

    Given a parser instance 'parser' (either OptionParser or
    ArgumentParser), add a '--nprocessors' option.

    The value of this option can be accessed via the 'nprocessors'
    attribute of the parser options.

    If 'default_display' is not None then this value will be shown
    in the help text, rather than the value supplied for the default.

    Returns the input parser object.

    """
    if default_display is None:
        default_display = default_nprocessors
    add_arg(parser,'--nprocessors',action='store',
            dest='nprocessors',default=default_nprocessors,
            help="explicitly specify number of processors/cores "
            "to use (default %s)" %default_display)
    return parser

def add_runner_option(parser):
    """Add a '--runner' option to a parser

    Given a parser instance 'parser' (either OptionParser or
    ArgumentParser), add a '--runner' option.

    The value of this option can be accessed via the 'runner'
    attribute of the parser options (use the 'fetch_runner'
    function to return a JobRunner object from the supplied
    value).

    Returns the input parser object.

    """
    add_arg(parser,'--runner',action='store',
            dest='runner',default=None,
            help="explicitly specify runner definition (e.g. "
            "'GEJobRunner(-j y)')")
    return parser

def add_no_save_option(parser):
    """Add a '--no-save' option to a parser

    Given a parser instance 'parser' (either OptionParser or
    ArgumentParser), add a '--no-save' option.

    The value of this option can be accessed via the 'no_save'
    attribute of the parser options.

    Returns the input parser object.

    """
    add_arg(parser,'--no-save',action='store_true',
            dest='no_save',default=False,
            help="Don't save parameter changes to "
            "the auto_process.info file")
    return parser

def add_dry_run_option(parser):
    """Add a '--dry-run' option to a parser

    Given a parser instance 'parser' (either OptionParser or
    ArgumentParser), add a '--dry-run' option.

    The value of this option can be accessed via the 'dry_run'
    attribute of the parser options.

    Returns the input parser object.

    """
    add_arg(parser,'--dry-run',action='store_true',
            dest='dry_run',default=False,
            help="Dry run i.e. report what would "
            "be done but don't perform any actions")
    return parser

def add_debug_option(parser):
    """Add a '--debug' option to a parser

    Given a parser instance 'parser' (either OptionParser or
    ArgumentParser), add a '--debug' option.

    The value of this option can be accessed via the 'debug'
    attribute of the parser options.

    Returns the input parser object.

    """
    add_arg(parser,'--debug',action='store_true',
            dest='debug',default=False,
            help="Turn on debugging output")
    return parser

def add_arg(p,*args,**kwds):
    """Add an argument or option to a parser

    Given an arbitrary parser instance, adds a new
    option or argument using the appropriate method
    call and passing the supplied arguments and
    keywords.

    For example, if the parser is an instance of
    argparse.ArgumentParser, then the 'add_argument'
    method will be invoked to add a new argument to
    the parser.

    Arguments:
      p (Object): parser instance; can be an instance
        of one of: optparse.OptionContainer (i.e.
        OptionParser or OptionGroup), or
        argparse.ArgumentParser
      args (List): list of argument values to pass
        directly to the argument-addition method
      kwds (mapping): keyword-value mapping to pass
        directly to the argument-addition method

    """
    for add_arg in ('add_argument','add_option',):
        try:
            return getattr(p,add_arg)(*args,**kwds)
        except AttributeError:
            pass
    raise Exception("Unrecognised subparser class")
