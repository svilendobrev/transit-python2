## Copyright 2014 Cognitect. All Rights Reserved.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS-IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

# This test suite verifies that issues corrected remain corrected.

import unittest
from decimal import Decimal

from transit3.decode import Decoder
from transit3 import decode
from transit3.encode import Encoder
from transit3.class_hash import ClassDict
from transit3.transit_types import Symbol, frozendict, true, false, Keyword, Named

if decode.Y_no_Boolean:
    TRUE, FALSE = True, False
else:
    TRUE, FALSE = true, false

class RegressionTest(unittest.TestCase):
    cases = [
        ("cache_consistency", ({"Problem?": TRUE}, Symbol("Here"), Symbol("Here"))),
        ("one_pair_frozendict", frozendict({"a": 1})),
        ("json_int_max", (pow(2, 53) + 100, pow(2, 63) + 100)),
        ("newline_in_string", "a\nb"),
        ("big_decimal", Decimal("190234710272.2394720347203642836434")),
        ("dict_in_set", frozenset(frozendict({"test": "case"}))),
        ]
    def test_roundtrip(self):
        for name,value in self.cases:
            with self.subTest( name):
                in_data = value
                io = Encoder().encode( in_data)
                out_data = Decoder().decode( io)
                self.assertEqual(in_data, out_data)

class JsonIntBoundaryTest( unittest.TestCase):
    cases = [
        (pow(2, 53) - 1, int),
        (pow(2, 53), str),
        (-pow(2, 53) + 1, int),
        (-pow(2, 53), str),
        ]
    def test_max_is_number(self):
        for value,expected_type in self.cases:
            with self.subTest( str(value)):
                io = Encoder().encode( [value])
                actual_type = type(io[0])
                self.assertEqual(expected_type, actual_type)

class BooleanTest(unittest.TestCase):
    """Even though we're roundtripping transit_types.true and
    transit_types.false now, make sure we can still write Python bools.

    Additionally, make sure we can still do basic logical evaluation on transit
    Boolean values.
    """

    #XXX see  decode.Y_no_Boolean = 0

    def test_write_bool(self):
        io = Encoder().encode((True, False))
        out_data = Decoder().decode( io)
        self.assertIs( out_data[0],TRUE)
        self.assertIs( out_data[1],FALSE)

    def test_basic_eval(self):
        self.assertTrue( true)
        self.assertTrue( not false)

    def test_or(self):
        self.assertTrue( true or false)
        self.assertTrue( not (false or false))
        self.assertTrue( true or true)
        self.assertTrue( false or true)

    def test_and(self):
        self.assertTrue( not (true and false))
        self.assertTrue( not (false and true))
        self.assertTrue( true and true)
        self.assertTrue( not (false and false))


# Helper classes for inheritance unit test.
class parent(object):
    pass
class child(parent):
    pass
class grandchild(child):
    pass

class ClassDictInheritanceTest(unittest.TestCase):
    """Fix from issue #18: class_hash should iterate over all ancestors
    in proper mro, not just over direct ancestor.
    """
    def test_inheritance(self):
        cd = ClassDict()
        cd[parent] = "test"
        self.assertTrue( grandchild in cd)

#XXX this will be slow, .name/.namespace kept only for compatibility
class NamedTests(unittest.TestCase):
    """Verify behavior for newly introduced built-in Named name/namespace
    parsing. Accomplished through transit_types.Named, a mixin for
    transit_types.Keyword and transit_types.Symbol.
    """
    def test_named(self):
        k = Keyword("blah")
        s = Symbol("blah")
        self.assertEqual( k.name, "blah")
        self.assertEqual( s.name, "blah")

    def test_namespaced(self):
        k = Keyword("ns/name")
        s = Symbol("ns/name")
        self.assertEqual( k.name, "name")
        self.assertEqual( s.name, "name")
        self.assertEqual( k.namespace, "ns")
        self.assertEqual( s.namespace, "ns")

    def test_slash(self):
        k = Keyword("/")
        s = Symbol("/")
        self.assertEqual( k.name, "/")
        self.assertEqual( s.name, "/")
        self.assertIs( k.namespace, None)
        self.assertIs( s.namespace, None)
