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

import uuid
import ctypes
import datetime
import dateutil.tz
import dateutil.parser
from decimal import Decimal

from transit import transit_types
from transit.helpers import pairs

## Read handlers are used by the decoder when parsing/reading in Transit
## data and returning Python objects

#XXX these are almost never used.. so no much gain
#X_static =1
X_plain =1  #XXX rely on decoder not needing .from_rep i.e. decoder.X_decoders_direct

class DefaultHandler(object):
    @staticmethod
    def from_rep(t, v):
        return transit_types.TaggedValue(t, v)


class NoneHandler(object):
    @staticmethod
    def from_rep(_):
        return None


class KeywordHandler(object):
    @staticmethod
    def from_rep(v):
        return transit_types.Keyword(v)

class SymbolHandler(object):
    @staticmethod
    def from_rep(v):
        return transit_types.Symbol(v)


class BigDecimalHandler(object):
    @staticmethod
    def from_rep(v):
        return Decimal(v)


class BooleanHandler(object):
    @staticmethod
    def from_rep(x):
        return transit_types.true if x == "t" else transit_types.false


class IntHandler(object):
    @staticmethod
    def from_rep(v):
        return int(v)


class FloatHandler(object):
    @staticmethod
    def from_rep(v):
        return float(v)


class UuidHandler(object):
    @staticmethod
    def from_rep(u):
        """Given a string, return a UUID object."""
        if isinstance(u, str):
            return uuid.UUID(u)

        # hack to remove signs
        a = ctypes.c_ulong(u[0])
        b = ctypes.c_ulong(u[1])
        combined = a.value << 64 | b.value
        return uuid.UUID(int=combined)


class UriHandler(object):
    @staticmethod
    def from_rep(u):
        return transit_types.URI(u)


class DateHandler(object):
    @staticmethod
    def from_rep(d):
        if isinstance(d, int):
            return DateHandler._convert_timestamp(d)
        if "T" in d:
            return dateutil.parser.parse(d)
        return DateHandler._convert_timestamp(int(d))

    @staticmethod
    def _convert_timestamp(ms):
        """Given a timestamp in ms, return a DateTime object."""
        return datetime.datetime.fromtimestamp(ms / 1000.0, dateutil.tz.tzutc())


class BigIntegerHandler(object):
    @staticmethod
    def from_rep(d):
        return int(d)


class LinkHandler(object):
    @staticmethod
    def from_rep(l):
        return transit_types.Link(**l)


class ListHandler(object):
    @staticmethod
    def from_rep(l):
        return l


class SetHandler(object):
    @staticmethod
    def from_rep(s):
        return frozenset(s)


class CmapHandler(object):
    @staticmethod
    def from_rep(cmap):
        return transit_types.frozendict(pairs(cmap))


class IdentityHandler(object):
    @staticmethod
    def from_rep(i):
        return i


class SpecialNumbersHandler(object):
    @staticmethod
    def from_rep(z):
        if z == "NaN":
            return float("Nan")
        if z == "INF":
            return float("Inf")
        if z == "-INF":
            return float("-Inf")
        raise ValueError(f"Don't know how to handle: {z} as 'z'")


if X_plain:
    DefaultHandler = transit_types.TaggedValue
    def NoneHandler(): return None
    KeywordHandler = transit_types.Keyword
    SymbolHandler  = transit_types.Symbol
    BigDecimalHandler = Decimal
    def BooleanHandler(x):
        return transit_types.true if x == "t" else transit_types.false
    IntHandler = int
    FloatHandler = float
    def UuidHandler(u):
        """Given a string, return a UUID object."""
        if isinstance(u, str): return uuid.UUID(u)
        # hack to remove signs
        a = ctypes.c_ulong(u[0])
        b = ctypes.c_ulong(u[1])
        combined = a.value << 64 | b.value
        return uuid.UUID(int=combined)
    UriHandler = transit_types.URI
    def DateHandler(d):
        if isinstance( d, int): ms = d
        elif "T" in d:
            return dateutil.parser.parse(d)
        else: ms = int(d)
        return datetime.datetime.fromtimestamp( ms / 1000.0, dateutil.tz.tzutc())
    BigIntegerHandler = int
    def self(x): return x
    def LinkHandler(l):
        return transit_types.Link(**l)
    ListHandler = self
    SetHandler = frozenset
    def CmapHandler(cmap):
        return transit_types.frozendict(pairs(cmap))
    IdentityHandler = self
    _SpecialNumbers = {
        "NaN": float("Nan"),
        "INF": float("Inf"),
        "-INF": float("-Inf"),
        }
    def SpecialNumbersHandler(z):
        if z in _SpecialNumbers: return _SpecialNumbers[z]
        raise ValueError(f"Don't know how to handle: {z} as 'z'")
