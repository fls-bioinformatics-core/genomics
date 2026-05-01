#######################################################################
# Tests for utils/path.py module
#######################################################################


import unittest
from bcftbx.utils.parser import parse_named_lanes
from bcftbx.utils.parser import parse_lanes


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