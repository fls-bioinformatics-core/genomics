#!/usr/bin/env python3
#
#     parser.py: command line parsing helpers
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Command line parsing helper classes and functions.

Provides a single class:

* CommandParser: provides an ArgumentParser interface with subparsers
  for subcommands

Also provides a number of general helper functions:

* add_arg: add an argument or option to a parser
* add_nprocessors_option: adds ``--nprocessors`` argument
* add_runner_option: adds ``--runner`` argument
* add_no_save_option: adds ``--no-save`` argument
* add_dry_run_option: adds ``--dry-run`` argument
* add_debug_option: adds ``--debug`` argument

Addition helper functions for post-parsing:

* parse_named_lanes: process "named lane expression" ('[<lanes>:]<name>')
* parse_lanes: process specifier with lists and/or ranges of lane numbers
"""


import os
import sys
from argparse import ArgumentParser
from .collections import OrderedDictionary


# Command parser
class CommandParser:
    """
    Class implementing parser supporting multiple subcommands

    The CommandParser class process command lines of the form:

    ::

        PROG CMD OPTIONS ARGS

    where different sets of options can be defined based on the
    subcommand ('CMD') supplied at the start of the line.

    Each subcommand has its own associated subparser which has
    its own set of arguments.

    **Currently only ArgumentParser subparsers are supported.**

    Example usage:

    Create an initial CommandParser instance:

    >>> p = CommandParser()

    Add a 'setup' command:

    >>> p.add_command('setup', usage='%prog setup OPTIONS ARGS')

    Add options to the 'setup' command using the appropriate methods
    of the subparser (i.e. 'add_argument' for an ArgumentParser
    subparser instance):

    >>> p.parser_for('info').add_argument('-f',...)

    To process a command line, use the 'parse_args' method:

    >>> cmd, args = p.parse_args()

    .. note::

        Note that the exact form of the returned values depends on
        on the subparser instance; it will be the same as that
        returned by the 'parse_args' method of the subparser.

    Arguments:
        description (str): description text for the
           top-level command
        version (str): version text for the --version
           argument
        subparser (object): class used to create subparsers
           (defaults to 'ArgumentParser')
    """
    def __init__(self, description=None, version=None, subparser=None):
        self._name = os.path.basename(sys.argv[0])
        self._description = description
        self._version = version
        self._commands = OrderedDictionary()
        self._help = dict()
        if subparser is None:
            subparser = ArgumentParser
        self._subparser = subparser

    def add_command(self, cmd, help=None, **args):
        """
        Add a subparser for subcommand

        Adds a subcommand, and creates and returns an initial
        subparser instance for it.

        Arguments:
          cmd (str): name of the subcommand
          help (str): (optional) help text for the command
          args (dict): (optional) additional arguments passed to the
            ArgumentParser subparser (e.g. 'usage', 'version',
            'description'...)

        Returns:
           Object: subparser instance for the subcommand.
        """
        if cmd in self._commands:
            raise Exception("Command '%s' already defined" % cmd)
        if 'prog' not in args:
            args['prog'] = f"{os.path.basename(sys.argv[0])} {cmd}"
        if 'version' not in args:
            args['version'] = self._version
        try:
            # Try to create parse including version
            p = self._subparser(**args)
        except TypeError:
            # Try again without the version argument
            version = args['version']
            del (args['version'])
            p = self._subparser(**args)
            # Add the --version argument manually
            add_arg(p, '--version', action='version', version=version)
        self._commands[cmd] = p
        self._help[cmd] = help
        return p

    def parser_for(self, cmd):
        """
        Return parser instance for specified subcommand

        Returns:
          Object: parser object for the specified command.
        """
        return self._commands[cmd]

    def parse_args(self, argv=None):
        """
        Parse a command line

        Parses a command line (either those supplied to the calling
        subprogram e.g. via the Python interpreter, or as a list).

        Once the command is identified from the first argument, the
        remainder of the arguments are passed to the 'parse_args'
        method of the appropriate subparser for that command.

        This method returns a tuple, with the first value being the
        command, and the rest of the values being those returned
        from the 'parse_args' method of the subparser.

        Arguments:
          argv (list): (optional) a list consisting of a command line.
            If not supplied then defaults to sys.argv[1:].

        Returns:
          Tuple: a tuple of (cmd, arguments), where 'cmd' is the subcommand,
            and 'arguments' are the arguments returned from the
            subparser after processing the remainder of the command line.
        """
        # Collect arguments to process
        if argv is None:
            argv = sys.argv[1:]
        if not argv:
            self.error("Need to supply a subcommand\n%s" %
                       self.print_available_commands())
        # Determine the major command and get the parser
        cmd = argv[0]
        self.handle_generic_commands(cmd)
        try:
            p = self.parser_for(cmd)
        except KeyError:
            # No parser
            self.error("Usage: %s COMMAND [options] [args...]\n\n"
                       "%s: error: no such subcommand: %s" %
                       (self._name, self._name, cmd))
        # Parse the remaining arguments and return
        if isinstance(p, ArgumentParser):
            options = p.parse_args(argv[1:])
            return (cmd, options)
        else:
            try:
                # Unofficial backwards-compatibility support for optparse
                options, arguments = p.parse_args(argv[1:])
                return (cmd,options,arguments)
            except Exception:
                raise NotImplementedError(f"parse_args: unsupported subparser")

    def error(self, message):
        """
        Exit with error message

        Arguments:
            message (str): error message
        """
        sys.stderr.write("%s\n" % message)
        sys.exit(1)

    def handle_generic_commands(self, cmd):
        """
        Process 'generic' commands e.g. 'help'

        Arguments:
            cmd (str): name of the subcommand
        """
        if cmd in ('-h', '--help', 'help'):
            print("Usage: %s COMMAND [options] [args...]" % self._name)
            if self._description is not None:
                print("\n%s" % self._description)
            print("%s" % self.print_available_commands())
            sys.exit(0)
        if cmd in ('--version',):
            if self._version is not None:
                version_str = self._version
                print("%s" % version_str.replace('%prog', self._name))
            sys.exit(0)

    def list_commands(self):
        """
        Return the list of subcommands
        """
        return self._commands.keys()

    def print_available_commands(self):
        """
        Pretty-print available subcommands

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
            lines.append(self.print_command(cmd, self._help[cmd]))
        lines.append("")
        return '\n'.join(lines)

    def print_command(self, cmd, message=None):
        """
        Print a line for a single command

        Returns a 'pretty-printed' line for the specified command
        and text, with standard whitespace formatting.

        Arguments:
            cmd (str): name of the subcommand
            message (str): optional message to include in the output
        """
        text = ['  ', cmd]
        width = 22
        if len(cmd) < width:
            text.append(' ' * (width - len(cmd)))
        else:
            text.append('\n  ' + ' ' * width)
        if message is not None:
            text.append(message)
        return ''.join(text)


def add_arg(p, *args, **kwds):
    """
    Add an argument or option to a parser

    Given an arbitrary parser instance, adds a new
    option or argument using the appropriate method
    call and passing the supplied arguments and
    keywords.

    For example, if the parser is an instance of
    argparse.ArgumentParser, then the 'add_argument'
    method will be invoked to add a new argument to
    the parser.

    Arguments:
      p (Object): parser instance
      args (List): list of argument values to pass
        directly to the argument-addition method
      kwds (mapping): keyword-value mapping to pass
        directly to the argument-addition method

    """
    for add_arg in ('add_argument', 'add_option',):
        try:
            return getattr(p, add_arg)(*args, **kwds)
        except AttributeError:
            pass
    raise Exception("Unrecognised subparser class")


def add_nprocessors_option(parser, default_nprocessors, default_display=None):
    """
    Add a '--nprocessors' option to a parser

    The value of this option can be accessed via the 'nprocessors'
    attribute of the parser options.

    If 'default_display' is not None then this value will be shown
    in the help text, rather than the value supplied for the default.

    Returns the input parser object.
    """
    if default_display is None:
        default_display = default_nprocessors
    add_arg(parser, '--nprocessors', action='store',
            dest='nprocessors', default=default_nprocessors,
            help="explicitly specify number of processors/cores "
                 "to use (default %s)" % default_display)
    return parser


def add_runner_option(parser):
    """
    Add a '--runner' option to a parser

    The value of this option can be accessed via the 'runner'
    attribute of the parser options (use the 'fetch_runner'
    function to return a JobRunner object from the supplied
    value).

    Returns the input parser object.
    """
    add_arg(parser, '--runner', action='store',
            dest='runner', default=None,
            help="explicitly specify runner definition (e.g. "
                 "'LocalRunner')")
    return parser


def add_no_save_option(parser):
    """
    Add a '--no-save' option to a parser

    The value of this option can be accessed via the 'no_save'
    attribute of the parser options.

    Returns the input parser object.
    """
    add_arg(parser, '--no-save', action='store_true',
            dest='no_save', default=False,
            help="Don't save parameter changes to "
                 "the auto_process.info file")
    return parser


def add_dry_run_option(parser):
    """
    Add a '--dry-run' option to a parser

    The value of this option can be accessed via the 'dry_run'
    attribute of the parser options.

    Returns the input parser object.
    """
    add_arg(parser, '--dry-run', action='store_true',
            dest='dry_run', default=False,
            help="Dry run i.e. report what would "
                 "be done but don't perform any actions")
    return parser


def add_debug_option(parser):
    """
    Add a '--debug' option to a parser

    The value of this option can be accessed via the 'debug'
    attribute of the parser options.

    Returns the input parser object.
    """
    add_arg(parser, '--debug', action='store_true',
            dest='debug', default=False,
            help="Turn on debugging output")
    return parser


def parse_named_lanes(name_expr):
    """Break up 'named lane expression' into lane numbers and name

    A 'named lane expression' takes the form '[<lanes>:]<name>',
    where lanes can be absent or consist of any of:

    - a single integer (e.g. 1), or
    - a list of comma-separated integers (e.g. 1,2,3), or
    - a range (e.g. 1-4), or
    - a combination of lists and ranges (e.g. 1,3,5-8).

    Arguments:
      name_expr (str): a named lane expression

    Returns:
      Tuple: a tuple of the form (lanes,name), where lanes is a
        Python list of integers representing lanes (or None, if no
        lanes were specified), and name is a string with the
        associated name.
    """
    # Name expressions are of the form 'expr:name'
    try:
        # Extract components
        i = str(name_expr).index(':')
        name = str(name_expr)[i+1:]
        # Extract lane numbers from leading expression
        lanes = parse_lanes(str(name_expr)[:i])
    except ValueError:
        # No lanes specified
        name = str(name_expr)
        lanes = None
    # Return tuple
    return (lanes,name)


def parse_lanes(lane_expr):
    """
    Break up a 'lane expression' into a list of lane numbers

    A 'lane expression' is a string consisting of:

    - a single integer (e.g. 1), or
    - a list of comma-separated integers (e.g. 1,2,3), or
    - a range (e.g. 1-4), or
    - a combination of lists and ranges (e.g. 1,3,5-8).

    Arguments:
      lane_expr (str): a lane expression

    Returns:
      List: list of integers representing lane numbers.
    """
    # Extract lane numbers
    fields = lane_expr.split(',')
    lanes = []
    for field in fields:
        # Check for ranges i.e. 1-3
        try:
            i = field.index('-')
            l1 = int(field[:i])
            l2 = int(field[i+1:])
            for i in range(l1,l2+1): lanes.append(i)
        except ValueError:
            # Not a range
            lanes.append(int(field))
    # Sort into order
    lanes.sort()
    return lanes