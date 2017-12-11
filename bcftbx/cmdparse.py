########################################################################
#
# cmdparse.py
#
#########################################################################

"""
Provides a CommandParser class built on top of the 'argparse.ArgumentParser'
class, that can be used for handling command lines of the form::

    PROG COMMAND OPTION ARGS

where different sets of options can be defined based on the initial
command.

The argparse.ArgumentParser may be specified to be used in place of optparse.OptionParser.

In addition to the core CommandParser class, there are a number of
supporting functions that can be used with any argparse-based object to
add 'standard' options:

* --nprocessors
* --runner
* --no-save
* --dry-run
* --debug

"""

__version__ = "1.0.1"

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

    Create a simple CommandParser
    with OptionParser as the default backend using:

    >>> p = CommandParser()
    
    or with ArgumentParser as the backend using:

    >>> p = CommandParser(subparser=argparser.ArgumentParser)

    Add a 'setup' command:

    >>> p.add_command('setup',usage='%prog setup OPTIONS ARGS')

    Add options to the 'setup' command using normal OptionParser/ ArgumentParser methods,
    e.g.

    >>> p.parser_for('info').add_option('-f',...)

    To process a command line use the 'parse_args' method e.g.:

    >>> cmd,options,args = p.parse_args()

    The options and arguments can be accessed using the normal
    methods from optparse.

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

        Adds a command and creates an initial ArgumentParser
        for it.

        Arguments:
          cmd: the command to be added
          help: (optional) help text for the command

        Other arguments are passed to the ArgumentParser object
        when it is created i.e. 'usage', 'version',
        'description'.

        If 'version' isn't specified then the version
        supplied to the CommandParser object will be used.

        Returns:
          ArgumentParser object for the command.

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

        Arguments:
          argv: (optional) a list consisting of a command line.
            If not supplied then defaults to sys.argv[1:].

        Returns:
          A tuple of (cmd,options,arguments) if OptionParser (default)
          backend is used where 'cmd' is the
          command, and 'options' and 'arguments' are the options and
          arguments as returned by OptionParser.parse_args.
          A tuple of (cmd,options) if ArgumentParser is used as backend
          where 'cmd' is the command and 'options' is as returned by
          ArgumentParser.parse_args

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
            print "Usage: %s COMMAND [options] [args...]" % self._name
            if self._description is not None:
                print "\n%s" % self._description
            print "%s" % self.print_available_commands()
            sys.exit(0)
        if cmd in ('--version',):
            if self._version is not None:
                version_str = self._version
                print "%s" % version_str.replace('%prog',self._name)
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

    Given an OptionParser 'parser', add a '--nprocessors' option.

    The value of this option can be accessed via the 'nprocessors'
    attribute of the parser options.

    If 'default_display' is not None then this value will be shown
    in the help text, rather than the value supplied for the default.

    Returns the input ArgumentParser object.

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

    Given an OptionParser 'parser', add a '--runner' option.

    The value of this option can be accessed via the 'runner'
    attribute of the parser options (use the 'fetch_runner'
    function to return a JobRunner object from the supplied
    value).

    Returns the input ArgumentParser object.

    """
    add_arg(parser,'--runner',action='store',
            dest='runner',default=None,
            help="explicitly specify runner definition (e.g. "
            "'GEJobRunner(-j y)')")
    return parser

def add_no_save_option(parser):
    """Add a '--no-save' option to a parser

    Given an OptionParser 'parser', add a '--no-save' option.

    The value of this option can be accessed via the 'no_save'
    attribute of the parser options.

    Returns the input ArgumentParser object.

    """
    add_arg(parser,'--no-save',action='store_true',
            dest='no_save',default=False,
            help="Don't save parameter changes to "
            "the auto_process.info file")
    return parser

def add_dry_run_option(parser):
    """Add a '--dry-run' option to a parser

    Given an OptionParser 'parser', add a '--dry-run' option.

    The value of this option can be accessed via the 'dry_run'
    attribute of the parser options.

    Returns the input OptionParser object.

    """
    add_arg(parser,'--dry-run',action='store_true',
            dest='dry_run',default=False,
            help="Dry run i.e. report what would "
            "be done but don't perform any actions")
    return parser

def add_debug_option(parser):
    """Add a '--debug' option to a parser

    Given an OptionParser 'parser', add a '--debug' option.

    The value of this option can be accessed via the 'debug'
    attribute of the parser options.

    Returns the input ArgumentParser object.

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
    method will be invoked to add a new

    Arguments:
      p (Object): parser instance; can be an instance
        of one of: optparse.OptionParser or
        argparse.ArgumentParser
      args (List): list of argument values to pass
        directly to the argument-addition method
      kwds (mapping): keyword-value mapping to pass
        directly to the argument-addition method

    """
    if isinstance(p,argparse.ArgumentParser):
        add_arg = p.add_argument
    elif isinstance(p,optparse.OptionParser):
        add_arg = p.add_option
    else:
        raise Exception("Unrecognised subparser class")
    return add_arg(*args,**kwds)
