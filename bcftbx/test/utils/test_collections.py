#######################################################################
# Tests for utils/collections.py module
#######################################################################


import unittest
import pickle
from bcftbx.utils.collections import AttributeDictionary
from bcftbx.utils.collections import OrderedDictionary


class TestAttributeDictionary(unittest.TestCase):
    """Tests for the AttributeDictionary class
    """

    def test_set_get_items(self):
        """AttributeDictionary 'set' and 'get' using dictionary notation
        """
        d = AttributeDictionary()
        self.assertEqual(len(d),0)
        d['salutation'] = 'hello'
        self.assertEqual(len(d),1)
        self.assertEqual(d["salutation"],"hello")

    def test_get_attrs(self):
        """AttributeDictionary 'get' using attribute notation
        """
        d = AttributeDictionary()
        self.assertEqual(len(d),0)
        d['salutation'] = 'hello'
        self.assertEqual(len(d),1)
        self.assertEqual(d.salutation,"hello")

    def test_init(self):
        """AttributeDictionary initialised like a standard dictionary
        """
        d = AttributeDictionary(salutation='hello',valediction='goodbye')
        self.assertEqual(len(d),2)
        self.assertEqual(d.salutation,"hello")
        self.assertEqual(d.valediction,"goodbye")

    def test_iter(self):
        """AttributeDictionary iteration over items
        """
        d = AttributeDictionary()
        self.assertEqual(len(d),0)
        d['salutation'] = 'hello'
        d['valediction'] = 'goodbye'
        self.assertEqual(len(d),2)
        self.assertEqual(d.salutation,"hello")
        self.assertEqual(d.valediction,"goodbye")
        for key in d:
            self.assertTrue(key in ('salutation','valediction'),
                            "%s not in list" % key)

    def test_can_pickle_attributedictionary(self):
        """AttributeDictionary can be pickled
        """
        d = AttributeDictionary(hello="world")
        self.assertEqual(d['hello'],"world")
        pickled = pickle.dumps(d)
        unpickled = pickle.loads(pickled)
        self.assertTrue(isinstance(unpickled,AttributeDictionary))
        self.assertEqual(unpickled['hello'],"world")
        self.assertEqual(unpickled.hello,"world")

class TestOrderedDictionary(unittest.TestCase):
    """Unit tests for the OrderedDictionary class
    """

    def test_get_and_set(self):
        """OrderedDictionary add and retrieve data
        """
        d = OrderedDictionary()
        self.assertEqual(len(d),0)
        d['hello'] = 'goodbye'
        self.assertEqual(d['hello'],'goodbye')

    def test_insert(self):
        """OrderedDictionary insert items
        """
        d = OrderedDictionary()
        d['hello'] = 'goodbye'
        self.assertEqual(d.keys(),['hello'])
        self.assertEqual(len(d),1)
        # Insert at start of list
        d.insert(0,'stanley','fetcher')
        self.assertEqual(d.keys(),['stanley','hello'])
        self.assertEqual(len(d),2)
        self.assertEqual(d['stanley'],'fetcher')
        self.assertEqual(d['hello'],'goodbye')
        # Insert in middle
        d.insert(1,'monty','python')
        self.assertEqual(d.keys(),['stanley','monty','hello'])
        self.assertEqual(len(d),3)
        self.assertEqual(d['stanley'],'fetcher')
        self.assertEqual(d['monty'],'python')
        self.assertEqual(d['hello'],'goodbye')

    def test_keeps_things_in_order(self):
        """OrderedDictionary returns items in same order as added
        """
        d = OrderedDictionary()
        d['hello'] = 'goodbye'
        d['stanley'] = 'fletcher'
        d['monty'] = 'python'
        self.assertEqual(d.keys(),['hello','stanley','monty'])

    def test_iteration_over_keys(self):
        """OrderedDictionary iterating over keys
        """
        d = OrderedDictionary()
        d['hello'] = 'goodbye'
        d['stanley'] = 'fletcher'
        d['monty'] = 'python'
        try:
            for i in d:
                pass
        except KeyError:
            self.fail("Iteration over OrderedDictionary failed")