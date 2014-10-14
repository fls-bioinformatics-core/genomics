#######################################################################
# Tests for cmdparse.py module
#######################################################################

import unittest
from optparse import OptionParser
from bcftbx.cmdparse import *

class TestCommandParser(unittest.TestCase):
    """
    """
    def test_add_command(self):
        """CommandParser.add_command works for a single command
        """
        p = CommandParser()
        cmd = p.add_command('slow')
        self.assertTrue(isinstance(cmd,OptionParser))
        self.assertEqual(p.list_commands(),['slow'])
    def test_add_multiple_commands(self):
        """CommandParser.add_command works for multiple commands
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
        """CommandParser.parse_args works for simple cases
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
    def test_add_runner_option(self):
        """add_runner_option enables '--runner'
        """
        p = OptionParser()
        add_runner_option(p)
        options,args = p.parse_args(['--runner','SimpleJobRunner'])
        self.assertEqual(options.runner,'SimpleJobRunner')
    def test_add_no_save_option(self):
        """add_no_save_option enables '--no-save'
        """
        p = OptionParser()
        add_no_save_option(p)
        options,args = p.parse_args(['--no-save'])
        self.assertTrue(options.no_save)
    def test_add_dry_run_option(self):
        """add_dry_run_option enables '--dry-run'
        """
        p = OptionParser()
        add_dry_run_option(p)
        options,args = p.parse_args(['--dry-run'])
        self.assertTrue(options.dry_run)
    def test_add_debug_option(self):
        """add_debug_option enables '--debug'
        """
        p = OptionParser()
        add_debug_option(p)
        options,args = p.parse_args(['--debug'])
        self.assertTrue(options.debug)
