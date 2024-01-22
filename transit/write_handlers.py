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

X_wHandler =1
X_wHandler_tag_len_1 =1
#X_wHandler_tag_as_subscr =0 ??-not-called-enough #a[b] is faster than a.method(b)
#X_singledispatch =0     #no, much slower
X_wdict = 1
X_wHandler_as_dictAttr =0  #slower

import uuid
import datetime
import struct
from transit.class_hash import ClassDict
from transit.transit_types import (
    Keyword,
    Symbol,
    URI,
    frozendict,
    TaggedValue,
    Link,
    Boolean,
)
from decimal import Decimal
from dateutil import tz
from math import isnan

MAX_INT = pow(2, 63) - 1
MIN_INT = -pow(2, 63)

## This file contains Write Handlers - all the top-level objects used when
## writing Transit data.  These object must all be immutable and pickleable.


class TaggedMap(object):
    def __init__(self, tag, rep, str):
        self._tag = tag
        self._rep = rep
        self._str = str

    def tag(self):
        return self._tag

    def rep(self):
        return self._rep

    def string_rep(self):
        return self._str


class NoneHandler(object):
    @staticmethod
    def tag(_):
        return "_"

    @staticmethod
    def rep(_):
        return None

    @staticmethod
    def string_rep(n):
        return None


class IntHandler(object):
    @staticmethod
    def tag(i):
        return "i"

    @staticmethod
    def rep(i):
        return i

    @staticmethod
    def string_rep(i):
        return str(i)


class BigIntHandler(object):
    @staticmethod
    def tag(_):
        return "n"

    @staticmethod
    def rep(n):
        return str(n)

    @staticmethod
    def string_rep(n):
        return str(n)


class Python3IntHandler(object):
    @staticmethod
    def tag(n):
        if n < MAX_INT and n > MIN_INT:
            return "i"
        return "n"

    @staticmethod
    def rep(n):
        return n

    @staticmethod
    def string_rep(n):
        return str(n)


class BigDecimalHandler(object):
    @staticmethod
    def tag(_):
        return "f"

    @staticmethod
    def rep(n):
        return str(n)

    @staticmethod
    def string_rep(n):
        return str(n)


class FloatHandler(object):
    @staticmethod
    def tag(f):
        return "z" if isnan(f) or f in (float("Inf"), float("-Inf")) else "d"

    @staticmethod
    def rep(f):
        if isnan(f):
            return "NaN"
        if f == float("Inf"):
            return "INF"
        if f == float("-Inf"):
            return "-INF"
        return f

    @staticmethod
    def string_rep(f):
        return str(f)


class StringHandler(object):
    @staticmethod
    def tag(s):
        return "s"

    @staticmethod
    def rep(s):
        return s

    @staticmethod
    def string_rep(s):
        return s


class BooleanHandler(object):
    @staticmethod
    def tag(_):
        return "?"

    @staticmethod
    def rep(b):
        return bool(b)

    @staticmethod
    def string_rep(b):
        return "t" if b else "f"


class ArrayHandler(object):
    @staticmethod
    def tag(a):
        return "array"

    @staticmethod
    def rep(a):
        return a

    @staticmethod
    def string_rep(a):
        return None


class MapHandler(object):
    @staticmethod
    def tag(m):
        return "map"

    @staticmethod
    def rep(m):
        return m

    @staticmethod
    def string_rep(m):
        return None


class KeywordHandler(object):
    @staticmethod
    def tag(k):
        return ":"

    @staticmethod
    def rep(k):
        return str(k)

    @staticmethod
    def string_rep(k):
        return str(k)


class SymbolHandler(object):
    @staticmethod
    def tag(s):
        return "$"

    @staticmethod
    def rep(s):
        return str(s)

    @staticmethod
    def string_rep(s):
        return str(s)


class UuidHandler(object):
    @staticmethod
    def tag(_):
        return "u"

    @staticmethod
    def rep(u):
        return struct.unpack(">qq", u.bytes)

    @staticmethod
    def string_rep(u):
        return str(u)


class UriHandler(object):
    @staticmethod
    def tag(_):
        return "r"

    @staticmethod
    def rep(u):
        return u.rep

    @staticmethod
    def string_rep(u):
        return u.rep


class DateTimeHandler(object):
    epoch = datetime.datetime(1970, 1, 1).replace(tzinfo=tz.tzutc())

    @staticmethod
    def tag(_):
        return "m"

    @staticmethod
    def rep(d):
        td = d - DateTimeHandler.epoch
        return int((td.microseconds + (td.seconds + td.days * 24 * 3600) * pow(10, 6)) / 1e3)

    @staticmethod
    def verbose_handler():
        return VerboseDateTimeHandler

    @staticmethod
    def string_rep(d):
        return str(DateTimeHandler.rep(d))


class VerboseDateTimeHandler(object):
    @staticmethod
    def tag(_):
        return "t"

    @staticmethod
    def rep(d):
        return d.isoformat()

    @staticmethod
    def string_rep(d):
        return d.isoformat()


class SetHandler(object):
    @staticmethod
    def tag(_):
        return "set"

    @staticmethod
    def rep(s):
        return TaggedMap("array", tuple(s), None)

    @staticmethod
    def string_rep(_):
        return None


class TaggedValueHandler(object):
    @staticmethod
    def tag(tv):
        return tv.tag

    @staticmethod
    def rep(tv):
        return tv.rep

    @staticmethod
    def string_rep(_):
        return None


class LinkHandler(object):
    @staticmethod
    def tag(_):
        return "link"

    @staticmethod
    def rep(l):
        return l.as_map

    @staticmethod
    def string_rep(_):
        return None

if X_wHandler:
    wdict = {}
    class wHandler:
        __slots__ = 'tag rep string_rep tag_len_1'.split()
        def __init__( me, *types, tag, rep, str):
            me.tag = tag if callable( tag) else lambda x: tag
            me.rep = rep
            me.string_rep = str
            me.tag_len_1 = False
            if X_wHandler_tag_len_1:
                me.tag_len_1 = not callable( tag) and len(tag)==1
            for t in types: wdict[ t ] = me
        @classmethod
        def copy( me, o, *, tag =None, rep =None, str =None):
            return me( tag= tag or o.tag, rep= rep or o.rep, str= str or o.string_rep)

    def rep_x(x): return x
    def rep_None(x): return None
    NoneHandler         = wHandler( type(None), tag= '_'  , rep= rep_None , str= rep_None)
    #IntHandler          = wHandler( int,        tag= 'i'  , rep= rep_x    , str= str )
    #BigIntHandler       = wHandler( int,        tag= 'n'  , rep= str      , str= str )
    Python3IntHandler   = wHandler( int,        tag= lambda x: 'i' if MIN_INT < x < MAX_INT else 'n', rep= rep_x, str= str)
    BigDecimalHandler   = wHandler( Decimal,    tag= 'f'  , rep= str      , str= str)
    float_infp= float("Inf")
    float_infn= float("-Inf")
    class FloatHandler:
        tag_len_1 = True
        @staticmethod
        def tag( f):
            return "z" if isnan(f) or f in (float_infp,float_infn) else "d"
        @staticmethod
        def rep(f):
            if isnan(f): return "NaN"
            if f == float_infp: return "INF"
            if f == float_infn: return "-INF"
            return f
        string_rep = str
    StringHandler       = wHandler( str,            tag= 's'    , rep= rep_x    , str= rep_x )
    BooleanHandler      = wHandler( bool, Boolean,  tag= '?'    , rep= bool     , str= lambda x: "t" if x else "f")
    ArrayHandler        = wHandler( list, tuple,    tag= 'array', rep= rep_x    , str= rep_None)
    MapHandler          = wHandler( dict, frozendict, tag= 'map'  , rep= rep_x    , str= rep_None)
    KeywordHandler      = wHandler( Keyword,    tag= ':'    , rep= str      , str= str)
    SymbolHandler       = wHandler( Symbol,     tag= '$'    , rep= str      , str= str)
    UuidHandler         = wHandler( uuid.UUID,  tag= 'u'    , rep= lambda x: struct.unpack(">qq", x.bytes), str= str)
    UriHandler          = wHandler( URI,        tag= 'r'    , rep= lambda x: x.rep,     str= lambda x: x.rep)
    #too complex ? DateTimeHandler(object):
    DateTimeHandler.tag_len_1 = True
    #no types, will not go in wdict
    VerboseDateTimeHandler = wHandler(              tag= 't'    , rep= lambda x: x.isoformat()  , str= lambda x: x.isoformat())
    SetHandler          = wHandler( set, frozenset, tag= 'set'  , rep= lambda x: TaggedMap("array", tuple(x), None),    str= rep_None)
    TaggedValueHandler  = wHandler( TaggedValue,    tag= lambda x: x.tag, rep= lambda x: x.rep  , str= rep_None)
    LinkHandler         = wHandler( Link,           tag= 'link' , rep= lambda x: x.as_map       , str= rep_None)
    wdict.update({
        float: FloatHandler,
        datetime.datetime: DateTimeHandler,
        TaggedMap: TaggedMap,
        })


class WriteHandler(ClassDict):
    """This is the master handler for encoding/writing Python data into
    Transit data, based on its type.
    The Handler itself is a dispatch map, that resolves on full type/object
    inheritance.

    These handlers can be overriden during the creation of a Transit Writer.
    """

    def __init__(self):
      if X_wdict:
        super().__init__( wdict)
      else:
        super(WriteHandler, self).__init__()
        self[type(None)] = NoneHandler
        self[bool] = BooleanHandler
        self[Boolean] = BooleanHandler
        self[str] = StringHandler
        self[list] = ArrayHandler
        self[tuple] = ArrayHandler
        self[dict] = MapHandler
        self[int] = Python3IntHandler
        self[float] = FloatHandler
        self[Keyword] = KeywordHandler
        self[Symbol] = SymbolHandler
        self[uuid.UUID] = UuidHandler
        self[URI] = UriHandler
        self[datetime.datetime] = DateTimeHandler
        self[set] = SetHandler
        self[frozenset] = SetHandler
        self[TaggedMap] = TaggedMap
        self[dict] = MapHandler
        self[frozendict] = MapHandler
        self[TaggedValue] = TaggedValueHandler
        self[Link] = LinkHandler
        self[Decimal] = BigDecimalHandler
