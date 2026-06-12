#######################################################################
# Tests for utils/path.py module
#######################################################################


import unittest
from argparse import ArgumentParser
from bcftbx.cmdparse import CommandParser
from bcftbx.cmdparse import add_nprocessors_option
from bcftbx.cmdparse import add_runner_option
from bcftbx.cmdparse import add_no_save_option
from bcftbx.cmdparse import add_dry_run_option
from bcftbx.cmdparse import add_debug_option
from bcftbx.cmdparse import add_arg
from bcftbx.utils.parser import parse_named_lanes
from bcftbx.utils.parser import parse_lanes


class TestCommandParserWithArgumentParser(unittest.TestCase):
    """
    Tests for CommandParser using explicit ArgumentParser backend
    """
    def test_add_command(self):
        """
        CommandParser.add_command: add single subcommand
        """
        p = CommandParser(subparser=ArgumentParser)
        cmd = p.add_command('slow')
        self.assertTrue(isinstance(cmd,ArgumentParser))
        self.assertEqual(p.list_commands(),['slow'])

    def test_add_multiple_commands(self):
        """
        CommandParser.add_command: add multiple subcommands
        """
        p = CommandParser(subparser=ArgumentParser)
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        medium_cmd = p.add_command('medium')
        self.assertTrue(isinstance(slow_cmd,ArgumentParser))
        self.assertTrue(isinstance(fast_cmd,ArgumentParser))
        self.assertTrue(isinstance(medium_cmd,ArgumentParser))
        self.assertEqual(p.list_commands(),['slow','fast','medium'])

    def test_parser_for(self):
        """
        CommandParser.parser_for: returns correct subparser
        """
        p = CommandParser(subparser=ArgumentParser)
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        medium_cmd = p.add_command('medium')
        self.assertEqual(p.parser_for('slow'),slow_cmd)
        self.assertEqual(p.parser_for('fast'),fast_cmd)
        self.assertEqual(p.parser_for('medium'),medium_cmd)

    def test_parse_args(self):
        """
        CommandParser.parse_args: process command line
        """
        p = CommandParser(subparser=ArgumentParser)
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        slow_cmd.add_argument('-a',action='store',dest='a_value')
        slow_cmd.add_argument('name')
        fast_cmd.add_argument('-b',action='store',dest='b_value')
        fast_cmd.add_argument('name')
        cmd,args = p.parse_args(['slow','-a','unspeedy','input'])
        self.assertEqual(cmd,'slow')
        self.assertEqual(args.a_value,'unspeedy')
        self.assertEqual(args.name,'input')
        try:
            args.b_value
            self.fail("Accessing 'b_value' for 'slow' command didn't raise AttributeError")
        except AttributeError:
            pass
        cmd,args = p.parse_args(['fast','-b','zippy','input2'])
        self.assertEqual(cmd,'fast')
        self.assertEqual(args.b_value,'zippy')
        self.assertEqual(args.name,'input2')
        try:
            args.a_value
            self.fail("Accessing 'a_value' for 'fast' command didn't raise AttributeError")
        except AttributeError:
            pass

    def test_handles_version(self):
        """
        CommandParser: handles version argument
        """
        p = CommandParser(subparser=ArgumentParser,version="0.1")
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')


class TestAddOptionFunctions(unittest.TestCase):
    """
    Tests for the various 'add_..._option' functions
    """
    def test_add_nprocessors_option(self):
        """
        add_nprocessors_option: enables '--nprocessors'
        """
        p = ArgumentParser()
        add_nprocessors_option(p,1)
        args = p.parse_args(['--nprocessors','4'])
        self.assertEqual(args.nprocessors,'4')

    def test_add_runner_option(self):
        """
        add_runner_option: enables '--runner'
        """
        p = ArgumentParser()
        add_runner_option(p)
        args = p.parse_args(['--runner','LocalRunner'])
        self.assertEqual(args.runner,'LocalRunner')

    def test_add_no_save_option(self):
        """
        add_no_save_option: enables '--no-save'
        """
        p = ArgumentParser()
        add_no_save_option(p)
        args = p.parse_args(['--no-save'])
        self.assertTrue(args.no_save)

    def test_add_dry_run_option(self):
        """
        add_dry_run_option: enables '--dry-run'
        """
        p = ArgumentParser()
        add_dry_run_option(p)
        args = p.parse_args(['--dry-run'])
        self.assertTrue(args.dry_run)

    def test_add_debug_option(self):
        """
        add_debug_option: enables '--debug'
        """
        p = ArgumentParser()
        add_debug_option(p)
        args = p.parse_args(['--debug'])
        self.assertTrue(args.debug)

    def test_add_arg_with_argumentparser(self):
        """
        add_arg: works with ArgumentParser
        """
        p = ArgumentParser()
        add_arg(p,'-n',action='store',dest='n')
        args = p.parse_args(['-n','4'])
        self.assertEqual(args.n,'4')

    def test_add_arg_with_argumentparser(self):
        """
        add_arg: works with ArgumentParser argument group
        """
        p = ArgumentParser()
        g = p.add_argument_group('Suboptions')
        add_arg(g,'-n',action='store',dest='n')
        args = p.parse_args(['-n','4'])
        self.assertEqual(args.n,'4')


class TestParseNamedLanesFunction(unittest.TestCase):
    """
    Unit tests for breaking up '[<lanes>:]<name>' expression
    """
    def test_name_no_lanes(self):
        """
        utils.parser.parse_named_lanes: name with no lanes
        """
        self.assertEqual(parse_named_lanes("PJB"),(None,"PJB"))

    def test_name_with_single_lane(self):
        """
        utils.parser.parse_named_lanes: name with a single lane
        """
        self.assertEqual(parse_named_lanes("1:PJB"),([1,],"PJB"))

    def test_name_with_range_of_lanes(self):
        """
        utils.parser.parse_named_lanes: name with a range of lanes
        """
        self.assertEqual(parse_named_lanes("2-4:PJB"),([2,3,4],"PJB"))

    def test_name_with_list_of_lanes(self):
        """
        utils.parser.parse_named_lanes: name with a list of lanes
        """
        self.assertEqual(parse_named_lanes("1,3,5:PJB"),([1,3,5],"PJB"))

    def test_name_with_mixture(self):
        """
        utils.parser.parse_named_lanes: name with both range and list of lanes
        """
        self.assertEqual(parse_named_lanes("1,3,5-8:PJB"),
                         ([1,3,5,6,7,8],"PJB"))


class TestParseLanesFunction(unittest.TestCase):
    """
    Unit tests for breaking up range-of-lanes expression
    """
    def test_single_integer(self):
        """
        utils.parser.parse_lanes: single lane e.g. '1'
        """
        self.assertEqual(parse_lanes("1"),[1,])

    def test_range(self):
        """
        utils.parser.parse_lanes: range of lanes e.g. '2-4'
        """
        self.assertEqual(parse_lanes("2-4"),[2,3,4,])

    def test_list(self):
        """
        utils.parser.parse_lanes: list of lanes e.g. '1,2,5'
        """
        self.assertEqual(parse_lanes("1,3,5"),[1,3,5,])

    def test_mixture(self):
        """
        utils.parser.parse_lanes: mixture of range and list of lanes
        """
        self.assertEqual(parse_lanes("1,3,5-8"),
                         [1,3,5,6,7,8])