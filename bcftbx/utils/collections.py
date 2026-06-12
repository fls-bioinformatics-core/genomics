#!/usr/bin/env python3
#
#     collections.py: specialized container datatypes
#     Copyright (C) University of Manchester 2026 Peter Briggs

"""
Provides specialized container datatypes:

* ``AttributeDictionary``: Dictionary-like object with keys also
  accessible as attributes
* ``OrderedDictionary``: augmented Dictionary which keeps keys in
  order
"""


import copy


class AttributeDictionary(dict):
    """
    Dictionary-like object with items accessible as attributes

    'AttributeDict' provides a Dictionary-like object where the value
    of items can also be accessed as attributes of the object.

    For example:

    >>> d = AttributeDict()
    >>> d['salutation'] = "hello"
    >>> d.salutation
    ... "hello"

    Attributes can only be assigned by using dictionary item assignment
    notation i.e. d['key'] = value. d.key = value doesn't work.

    If the attribute doesn't match a stored item then an
    AttributeError exception is raised.

    len(d) returns the number of stored items.

    The AttributeDict behaves like a dictionary for iterations, for
    example:

    >>> for attr in d:
    >>>    print("%s = %s" % (attr,d[attr]))
    """
    def __init__(self,**args):
        dict.__init__(self,**args)

    def __getattr__(self,attr):
        try:
            return dict.__getattr__(self,attr)
        except AttributeError:
            pass
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("'AttributeDictionary' has no "
                                 "attribute '%s'" % attr)


class OrderedDictionary:
    """
    Augumented Dictionary which keeps keys in order

    OrderedDictionary provides an augmented Python dictionary
    class which keeps the dictionary keys in the order they are
    added to the object.

    Items are added, modified and removed as with a standard
    dictionary e.g.:

    >>> d[key] = value
    >>> value = d[key]
    >>> del(d[key])

    The 'keys()' method returns the OrderedDictionary's keys in
    the correct order.
    """
    def __init__(self):
        self.__keys = []
        self.__dict = {}

    def __getitem__(self,key):
        if key not in self.__keys:
            raise KeyError
        return self.__dict[key]

    def __setitem__(self,key,value):
        if key not in self.__keys:
            self.__keys.append(key)
        self.__dict[key] = value

    def __delitem__(self,key):
        try:
            i = self.__keys.index(key)
            del(self.__keys[i])
            del(self.__dict[key])
        except ValueError:
            raise KeyError

    def __len__(self):
        return len(self.__keys)

    def __contains__(self,key):
        return key in self.__keys

    def __iter__(self):
        return iter(self.__keys)

    def keys(self):
        return copy.copy(self.__keys)

    def insert(self,i,key,value):
        if key not in self.__keys:
            self.__keys.insert(i,key)
            self.__dict[key] = value
        else:
            raise KeyError("Key '%s' already exists" % key)