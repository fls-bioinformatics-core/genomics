#######################################################################
# Tests for utils/users.py module
#######################################################################


import unittest
from bcftbx.utils.users import get_user_from_uid
from bcftbx.utils.users import get_group_from_gid
from bcftbx.utils.users import get_gid_from_group
from bcftbx.utils.users import get_uid_from_user


class TestUserAndGroupNameFunctions(unittest.TestCase):
    """
    Tests for the functions fetching user and group names and IDs
    """
    def test_get_user_from_uid(self):
        """
        utils.users.get_user_from_uid: gets 'root' from UID 0
        """
        self.assertEqual(get_user_from_uid(0),'root')

    def test_get_uid_from_user(self):
        """
        utils.users.get_uid_from_user: gets 0 from 'root'
        """
        self.assertEqual(get_uid_from_user('root'),0)

    def test_get_group_from_gid(self):
        """
        utils.users.get_group_from_gid: gets 'root' from UID 0
        """
        self.assertEqual(get_group_from_gid(0),'root')

    def test_get_gid_from_group(self):
        """
        utils.users.get_gid_from_group: gets 0 from 'root'
        """
        self.assertEqual(get_gid_from_group('root'),0)

    def test_user_and_group_functions_handle_string_ids(self):
        """
        utils.users.get_user_from_uid/get_group_from_gid: handle UID/GID supplied as strings
        """
        self.assertEqual(get_user_from_uid('0'),'root')
        self.assertEqual(get_group_from_gid('0'),'root')

    def test_user_and_group_functions_handle_nonexistent_users(self):
        """
        utils.users: user/group name functions handle nonexistent users
        """
        self.assertEqual(get_user_from_uid(-999),None)
        self.assertEqual(get_uid_from_user(''),None)
        self.assertEqual(get_group_from_gid(-999),None)
        self.assertEqual(get_gid_from_group(''),None)

    def test_user_and_group_functions_handle_bad_inputs(self):
        """
        utils.users: user/group name functions handle bad inputs
        """
        self.assertEqual(get_user_from_uid('root'),None)
        self.assertEqual(get_uid_from_user('0'),None)
        self.assertEqual(get_group_from_gid('root'),None)
        self.assertEqual(get_gid_from_group('0'),None)