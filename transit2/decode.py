## svd@2024
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

#+X_FIX_ARRAY = 1
X_mapkeystr = 0     #treat map-keys separately from just Keyword .. no need if all Keywords are treated-same
_X_mapkeystr = 'mapkeystr' if X_mapkeystr else True
X_mapcompreh= 1         #as-of timing-probi.. dictcomp is a-bit-faster than {}+loop , listcomp is a-bit-faster than []+loop
#+X_tuple_via_listcomp =1    #minimal gain.. into X_FIX_ARRAY
X_decode_map =0         #slower
X_is_cache_key_eq_in_cache =1   #better this.. avoid is_cache_key() at all
#+X_parse_string = 1
#X_plain =1             #rhandler = plain func, not class+method
#X_decoders_direct =1    # remove klass.from_rep , direct funcs instead
X_tag_in_decoders =1    #??
X_escaped_first= 1
#+X_decode_tag = 1
X_decode_str_with_parse =1  #only done with X_tag_in_decoders, no X_mapkeystr
#+X_decode_bytes_last = 1
X_decode_no_bytes = 1


#from transit import transit_types
#from transit.helpers import pairs
def pairs(i):
    return zip(*[iter(i)] * 2)
from transit.transit_types import true, false
from transit.transit_types import Keyword, Symbol, URI, frozendict, TaggedValue, Link, Boolean

#read-handlers
from uuid import UUID
import decimal
from datetime import datetime, timezone
fromisoformat = datetime.fromisoformat
fromtimestamp = datetime.fromtimestamp
utc = timezone.utc

DefaultHandler = TaggedValue
def NoneHandler(): return None
KeywordHandler = Keyword
SymbolHandler  = Symbol
BigDecimalHandler = decimal.Decimal
def BooleanHandler(x):
    return true if x == "t" else false
IntHandler = int
FloatHandler = float
def UuidHandler(u):
    """Given a string, return a UUID object."""
    if isinstance(u, str): return UUID(u)
    # hack to remove signs
    a = ctypes.c_ulong(u[0])
    b = ctypes.c_ulong(u[1])
    combined = a.value << 64 | b.value
    return UUID(int=combined)
UriHandler = URI
def DateHandler(d):
    if isinstance( d, int): ms = d
    elif "T" in d:
        return fromisoformat( d)
        #return dateutil.parser.parse(d)
    else: ms = int(d)
    return fromtimestamp( ms / 1000.0, utc)
BigIntegerHandler = int
def _self(x): return x
def LinkHandler(l): return Link(**l)
ListHandler = _self
SetHandler = frozenset
def CmapHandler(cmap): return frozendict(pairs(cmap))
IdentityHandler = _self
_SpecialNumbers = {
    "NaN": float("Nan"),
    "INF": float("Inf"),
    "-INF": float("-Inf"),
    }
def SpecialNumbersHandler(z):
    if z in _SpecialNumbers: return _SpecialNumbers[z]
    raise ValueError(f"Don't know how to handle: {z} as 'z'")

# eo read-handlers

from collections import OrderedDict
from transit.constants import MAP_AS_ARR, ESC, SUB, RES
from tt.rolling_cache import RollingCache, is_cache_key

class Tag(object):
    def __init__(self, tag):
        self.tag = tag

default_options = {
    "decoders": {
        "_": NoneHandler,
        ":": KeywordHandler,
        "$": SymbolHandler,
        "?": BooleanHandler,
        "i": IntHandler,
        "d": FloatHandler,
        "f": BigDecimalHandler,
        "u": UuidHandler,
        "r": UriHandler,
        "t": DateHandler,
        "m": DateHandler,
        "n": BigIntegerHandler,
        "z": SpecialNumbersHandler,
        "link": LinkHandler,
        "list": ListHandler,
        "set":  SetHandler,
        "cmap": CmapHandler,
        "'": IdentityHandler,
    },
    "default_decoder": DefaultHandler,
}

ground_decoders = {
    "_": NoneHandler,
    "?": BooleanHandler,
    "i": IntHandler,
    "'": IdentityHandler,
}

if X_tag_in_decoders:
    #assert X_decoders_direct
    ground_decoders[ "#" ] = Tag

_escaped = SUB+ESC+RES

class Decoder(object):
    """fully convert Transit (python) data into Python objects. Options:
    * default_decoder: func(tag,x) ; called when no decoder matches
    * decoders: {kind:func(x)} ; add/override (one or more) decoders.
    Note: Some (ground_decoders) cannot be overriden,
    needed to maintain bottom-tier compatibility.
    """
    map_factory = frozendict

    def __init__(self, options={}):
        self.options = default_options.copy()
        self.options.update(options)

        self.decoders = self.options["decoders"].copy()
        # Always ensure we control the ground decoders
        self.decoders.update(ground_decoders)
        if X_decode_map:
            self.make_decode_map()
        #if X_decoders_direct:
        def from_repper(x): return getattr( x, 'from_rep', x)   #just in case some ReadHandler class comes
        self.decoders = { k:from_repper(v) for k,v in self.decoders.items() }
        self.options["default_decoder"] = from_repper( self.options["default_decoder"] )

    def decode(self, node, cache=None, as_map_key=False):
        """Given a node of data (any supported decodeable obj - string, dict,
        list), return the decoded object.  Optionally set the current decode
        cache [None].  If None, a new RollingCache is instantiated and used.
        You may also hit to the decoder that this node is to be treated as a
        map key [False].  This is used internally.
        """
        if not cache:
            cache = RollingCache()
        #self.cache = cache
        return self._decode(node, cache, as_map_key)

    #+X_decode_bytes_last = 1
    def _decode(self, node, cache, as_map_key, *nodes):
        tp = node.__class__
        if tp is str:
            return self.decode_string(node, cache, as_map_key)
        elif tp is dict or tp is OrderedDict:
            return self.decode_hash(node, cache, as_map_key)
        elif tp is list:
            return self.decode_list(node, cache, as_map_key)
        elif tp is bool:
            return true if node else false
        elif tp is bytes:   #last.. is it needed?
            return self.decode_string(node.decode("utf-8"), cache, as_map_key)
        return node
    if X_decode_no_bytes:
      def _decode(self, node, cache, as_map_key, *nodes):
        tp = node.__class__
        if tp is str:
            return self.decode_string(node, cache, as_map_key)
        elif tp is dict or tp is OrderedDict:
            return self.decode_hash(node, cache, as_map_key)
        elif tp is list:
            return self.decode_list(node, cache, as_map_key)
        elif tp is bool:
            return true if node else false
        #elif tp is bytes:
        #    return self.decode_string(node.decode("utf-8"), cache, as_map_key)
        return node
    if X_decode_map:
      def make_decode_map( self):
        self._decode_map = {
            str: self.decode_string,
            bytes: lambda node, *a,**ka: self.decode_string( node.decode("utf-8"), *a,**ka),
            dict:  self.decode_hash,
            OrderedDict: self.decode_hash,
            list: self.decode_list,
            bool: lambda node, *a,**ka: true if node else false,
            }
      def _decode(self, node, cache, as_map_key):
        tp = node.__class__
        self_decode_map = self._decode_map
        if tp in self_decode_map:
            return self_decode_map[ tp ]( node, cache, as_map_key)
        return node

      def decode_list(self, node, cache, as_map_key):
        """Special case decodes map-as-array into map_factory.
        Otherwise lists are treated into tuples.
        """
        self_decode = self._decode
        if node:
            if node[0] == MAP_AS_ARR:
                # key must be decoded before value for caching to work.
                # ... doc/python3/html/reference/expressions.html#dictionary-displays - Starting with 3.8, the key is evaluated before the value
                returned_dict = {}
                for k,v in pairs(node[1:]):
                    returned_dict[ self_decode( k, cache, _X_mapkeystr) ] = self_decode( v, cache, as_map_key)
                return self.map_factory(returned_dict)
            decoded = self_decode(node[0], cache, as_map_key)
            if isinstance(decoded, Tag):
                return self.decode_tag(decoded.tag, self_decode(node[1], cache, as_map_key))
            #X_FIX_ARRAY: fallthrough used to repeat parseing node[0] ..broken cache
            return (decoded, *[self_decode(x, cache, as_map_key) for x in node[1:]])
        return ()
    if X_mapcompreh:    #for python >= 3.8
      def decode_list(self, node, cache, as_map_key):
        """Special case decodes map-as-array into map_factory.
        Otherwise lists are treated into tuples.
        """
        self_decode = self._decode
        if node:
            if node[0] == MAP_AS_ARR:
                # key must be decoded before value for caching to work.
                # ... doc/python3/html/reference/expressions.html#dictionary-displays - Starting with 3.8, the key is evaluated before the value
                return self.map_factory( {
                        self_decode(k, cache, _X_mapkeystr) : self_decode(v, cache, as_map_key)
                        for k,v in pairs(node[1:])
                        })
            decoded = self_decode(node[0], cache, as_map_key)
            if isinstance(decoded, Tag):
                return self.decode_tag(decoded.tag, self_decode(node[1], cache, as_map_key))
            return (decoded, *[self_decode(x, cache, as_map_key) for x in node[1:]])
        return ()

    assert RollingCache.X_is_cacheable_inside_encache
    def decode_string(self, string, cache, as_map_key):
        if is_cache_key(string): return cache[ string ]
        pstring = self.parse_string(string, None, as_map_key)   #java:ReadCache.cacheRead does this inside
        cache.encache( pstring, True, as_map_key, string)
        return pstring
    if X_is_cache_key_eq_in_cache:
      def decode_string(self, string, cache, as_map_key):
        if string in cache: return cache[ string ]
        pstring = self.parse_string(string, None, as_map_key)   #java:ReadCache.cacheRead does this inside
        cache.encache( pstring, True, as_map_key, string)
        return pstring
    if X_is_cache_key_eq_in_cache and RollingCache.X_encache_split:
      def decode_string(self, string, cache, as_map_key):
        if string in cache: return cache[ string ]
        pstring = self.parse_string(string, None, as_map_key)   #java:ReadCache.cacheRead does this inside
        cache.encache_decode_k2v( pstring, as_map_key, string)
        return pstring

    def decode_tag(self, tag, rep):
        self_decoders = self.decoders
        if tag in self_decoders:
            return self_decoders[ tag ](rep)
        return self.options["default_decoder"](tag, rep)

    def decode_hash(self, hash, cache, as_map_key):
        self_decode = self._decode
        if len(hash) != 1:
            if X_mapcompreh:
                    # ... doc/python3/html/reference/expressions.html#dictionary-displays - Starting with 3.8, the key is evaluated before the value
                return self.map_factory( {
                        self_decode(k, cache, _X_mapkeystr) : self_decode(v, cache, False)
                        for k,v in hash.items()
                        })
            #h = {}
            #for k, v in hash.items():
            #    # crude/verbose implementation, but this is only version that
            #    # plays nice w/cache for both msgpack and json thus far.
            #    # -- e.g., we have to specify encode/decode order for key/val
            #    # -- explicitly, all implicit ordering has broken in corner
            #    # -- cases, thus these extraneous seeming assignments
            #    key = self_decode(k, cache, _X_mapkeystr)
            #    val = self_decode(v, cache, False)
            #    h[key] = val
            #return self.map_factory(h)
        else:
            key = list(hash)[0]
            value = hash[key]
            key = self_decode(key, cache, True)
            if isinstance(key, Tag):
                return self.decode_tag(key.tag, self_decode(value, cache, as_map_key))
        return self.map_factory({key: self_decode(value, cache, False)})

    if X_mapkeystr:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m==':' and as_map_key==_X_mapkeystr and as_map_key in decoders: #not assumed
                return decoders[ as_map_key ](string[2:])
            if m in decoders:
                return decoders[m](string[2:])
            elif m in _escaped:
                return string[1:]
            elif m == "#":
                return Tag(string[2:])
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if X_mapkeystr and X_tag_in_decoders and X_escaped_first:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m==':' and as_map_key==_X_mapkeystr and as_map_key in decoders: #not assumed
                return decoders[ as_map_key ](string[2:])
            elif m in _escaped:
                return string[1:]
            if m in decoders:
                return decoders[m](string[2:])
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if not X_mapkeystr:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                return decoders[m](string[2:])
            elif m in _escaped:
                return string[1:]
            elif m == "#":
                return Tag(string[2:])
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if not X_mapkeystr and X_tag_in_decoders:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                return decoders[m](string[2:])
            elif m in _escaped:
                return string[1:]
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if not X_mapkeystr and X_tag_in_decoders and X_escaped_first:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            if m in _escaped:
                return string[1:]
            decoders = self.decoders
            if m in decoders:
                return decoders[m](string[2:])
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string

    # embed the best parse_string variant into decode_string
    if all([ X_decode_str_with_parse , X_is_cache_key_eq_in_cache ,
        not X_mapkeystr , X_tag_in_decoders ,
        ]):
      def decode_string(self, string, cache, as_map_key):
        if string in cache: return cache[ string ]

        #pstring = self.parse_string(string.. #java:ReadCache.cacheRead does this inside
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                pstring = decoders[m](string[2:])
            elif m in _escaped:
                pstring = string[1:]
            else:
                pstring = self.options["default_decoder"]( m, string[2:])
        else: pstring = string

        cache.encache( pstring, True, as_map_key, string)
        return pstring

    if all([ X_decode_str_with_parse , X_is_cache_key_eq_in_cache ,
        not X_mapkeystr , X_tag_in_decoders , X_escaped_first,
        ]):
      def decode_string(self, string, cache, as_map_key):
        if string in cache: return cache[ string ]

        #pstring = self.parse_string(string.. #java:ReadCache.cacheRead does this inside
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in _escaped:
                pstring = string[1:]
            elif m in decoders:
                pstring = decoders[m](string[2:])
            else:
                pstring = self.options["default_decoder"]( m, string[2:])
        else: pstring = string

        cache.encache( pstring, True, as_map_key, string)
        return pstring

    if all([ X_decode_str_with_parse , X_is_cache_key_eq_in_cache ,
        not X_mapkeystr , X_tag_in_decoders , X_escaped_first,
        RollingCache.X_encache_split
        ]):
      def decode_string(self, string, cache, as_map_key):
        if string in cache: return cache[ string ]

        #pstring = self.parse_string(string.. #java:ReadCache.cacheRead does this inside
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in _escaped:
                pstring = string[1:]
            elif m in decoders:
                pstring = decoders[m](string[2:])
            else:
                pstring = self.options["default_decoder"]( m, string[2:])
        else: pstring = string

        cache.encache_decode_k2v( pstring, as_map_key, string)
        return pstring

    def register(self, key_or_tag, obj):
        """Register a custom Transit tag and new parsing function with the
        decoder.  Also, you can optionally set the 'default_decoder' with
        this function.  Your new tag and parse/decode function will be added
        to the interal dictionary of decoders for this Decoder object.
        """
        #if X_decoders_direct:
        obj = getattr( obj, 'from_rep', obj)
        if key_or_tag == "default_decoder":
            self.options["default_decoder"] = obj
        else:
            self.decoders[key_or_tag] = obj

# vim:ts=4:sw=4:expandtab
