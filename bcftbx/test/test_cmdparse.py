#######################################################################
# Tests for cmdparse.py module
#######################################################################

import unittest
from optparse import OptionParser
from optparse import OptionGroup
from argparse import ArgumentParser
from bcftbx.cmdparse import *

class TestCommandParserOptionParser(unittest.TestCase):
    """Tests for CommandParser using default OptionParser backend
    """
    def test_add_command(self):
        """CommandParser.add_command works for a single command using optparse
        """
        p = CommandParser()
        cmd = p.add_command('slow')
        self.assertTrue(isinstance(cmd,OptionParser))
        self.assertEqual(p.list_commands(),['slow'])
    def test_add_multiple_commands(self):
        """CommandParser.add_command works for multiple commands using optparse
        """
        p = CommandParser()
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        medium_cmd = p.add_command('medium')
        self.assertTrue(isinstance(slow_cmd,OptionParser))
        self.assertTrue(isinstance(fast_cmd,OptionParser))
        self.assertTrue(isinstance(medium_cmd,OptionParser))
        self.assertEqual(p.list_commands(),['slow','fast','medium'])
    def test_parser_for(self):
        """CommandParser.parser_for returns the correct OptionParser
        """
        p = CommandParser()
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        medium_cmd = p.add_command('medium')
        self.assertEqual(p.parser_for('slow'),slow_cmd)
        self.assertEqual(p.parser_for('fast'),fast_cmd)
        self.assertEqual(p.parser_for('medium'),medium_cmd)
    def test_parse_args(self):
        """CommandParser.parse_args works for simple cases using optparse
        """
        p = CommandParser()
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        slow_cmd.add_option('-a',action='store',dest='a_value')
        fast_cmd.add_option('-b',action='store',dest='b_value')
        cmd,options,args = p.parse_args(['slow','-a','unspeedy','input'])
        self.assertEqual(cmd,'slow')
        self.assertEqual(options.a_value,'unspeedy')
        self.assertEqual(args,['input'])
        try:
            options.b_value
            self.fail("Accessing 'b_value' for 'slow' command didn't raise AttributeError")
        except AttributeError:
            pass
        cmd,options,args = p.parse_args(['fast','-b','zippy','input2'])
        self.assertEqual(cmd,'fast')
        self.assertEqual(options.b_value,'zippy')
        self.assertEqual(args,['input2'])
        try:
            options.a_value
            self.fail("Accessing 'a_value' for 'fast' command didn't raise AttributeError")
        except AttributeError:
            pass

class TestCommandParserWithArgumentParser(unittest.TestCase):
    """Tests for CommandParser using explicit ArgumentParser backend
    """
    def test_add_command(self):
        """CommandParser.add_command works for a single command using argparse
        """
        p = CommandParser(subparser=ArgumentParser)
        cmd = p.add_command('slow')
        self.assertTrue(isinstance(cmd,ArgumentParser))
        self.assertEqual(p.list_commands(),['slow'])
    def test_add_multiple_commands(self):
        """CommandParser.add_command works for multiple commands using argparse
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
        """CommandParser.parser_for returns the correct ArgumentParser
        """
        p = CommandParser(subparser=ArgumentParser)
        slow_cmd = p.add_command('slow')
        fast_cmd = p.add_command('fast')
        medium_cmd = p.add_command('medium')
        self.assertEqual(p.parser_for('slow'),slow_cmd)
        self.assertEqual(p.parser_for('fast'),fast_cmd)
        self.assertEqual(p.parser_for('medium'),medium_cmd)
    def test_parse_args(self):
        """CommandParser.parse_args works for simple cases using argparse
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

class TestAddOptionFunctions(unittest.TestCase):
    """Tests for the various 'add_..._option' functions
    """
    def test_add_nprocessors_option(self):
        """add_nprocessors_option enables '--nprocessors'
        """
        p = OptionParser()
        add_nprocessors_option(p,1)
        options,args = p.parse_args(['--nprocessors','4'])
        self.assertEqual(options.nprocessors,'4')
    def test_add_nprocessors_option_with_argparse(self):
        """add_nprocessors_option enables '--nprocessors' with ArgumentParser
        """
        p = ArgumentParser()
        add_nprocessors_option(p,1)
        args = p.parse_args(['--nprocessors','4'])
        self.assertEqual(args.nprocessors,'4')
    def test_add_runner_option(self):
        """add_runner_option enables '--runner'
        """
        p = OptionParser()
        add_runner_option(p)
        options,args = p.parse_args(['--runner','SimpleJobRunner'])
        self.assertEqual(options.runner,'SimpleJobRunner')
    def test_add_runner_option_with_argparse(self):
        """add_runner_option enables '--runner' with ArgumentParser
        """
        p = ArgumentParser()
        add_runner_option(p)
        args = p.parse_args(['--runner','SimpleJobRunner'])
        self.assertEqual(args.runner,'SimpleJobRunner')
    def test_add_no_save_option(self):
        """add_no_save_option enables '--no-save'
        """
        p = OptionParser()
        add_no_save_option(p)
        options,args = p.parse_args(['--no-save'])
        self.assertTrue(options.no_save)
    def test_add_no_save_option_with_argparse(self):
        """add_no_save_option enables '--no-save' with ArgumentParser
        """
        p = ArgumentParser()
        add_no_save_option(p)
        args = p.parse_args(['--no-save'])
        self.assertTrue(args.no_save)
    def test_add_dry_run_option(self):
        """add_dry_run_option enables '--dry-run'
        """
        p = OptionParser()
        add_dry_run_option(p)
        options,args = p.parse_args(['--dry-run'])
        self.assertTrue(options.dry_run)
    def test_add_dry_run_option_with_argparse(self):
        """add_dry_run_option enables '--dry-run' with ArgumentParser
        """
        p = ArgumentParser()
        add_dry_run_option(p)
        args = p.parse_args(['--dry-run'])
        self.assertTrue(args.dry_run)
    def test_add_debug_option(self):
        """add_debug_option enables '--debug'
        """
        p = OptionParser()
        add_debug_option(p)
        options,args = p.parse_args(['--debug'])
        self.assertTrue(options.debug)
    def test_add_debug_option_with_argparse(self):
        """add_debug_option enables '--debug' with ArgumentParser
        """
        p = ArgumentParser()
        add_debug_option(p)
        args = p.parse_args(['--debug'])
        self.assertTrue(args.debug)
    def test_add_arg_with_optionparser(self):
        """add_arg works with OptionParser
        """
        p = OptionParser()
        add_arg(p,'-n',action='store',dest='n')
        options,args = p.parse_args(['-n','4'])
        self.assertEqual(options.n,'4')
    def test_add_arg_with_optiongroup(self):
        """add_arg works with OptionGroup
        """
        p = OptionParser()
        g = OptionGroup(p,'Suboptions')
        add_arg(g,'-n',action='store',dest='n')
        options,args = p.parse_args(['-n','4'])
        self.assertEqual(options.n,'4')
    def test_add_arg_with_argumentparser(self):
        """add_arg works with ArgumentParser
        """
        p = ArgumentParser()
        add_arg(p,'-n',action='store',dest='n')
        args = p.parse_args(['-n','4'])
        self.assertEqual(args.n,'4')
    def test_add_arg_with_argumentparser(self):
        """add_arg works with ArgumentParser argument group
        """
        p = ArgumentParser()
        g = p.add_argument_group('Suboptions')
        add_arg(g,'-n',action='store',dest='n')
        args = p.parse_args(['-n','4'])
        self.assertEqual(args.n,'4')
