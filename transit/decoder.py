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

X_FIX_ARRAY = 1
X_mapkeystr = 0     #treat map-keys separately from just Keyword .. no need if all Keywords are treated-same
_X_mapkeystr = 'mapkeystr' if X_mapkeystr else True
X_mapcompreh= 0         #no gain ?
#X_tuple_via_list =1    #unclear gain.. into X_FIX_ARRAY
X_decode_map =0         #some gain, some loss..
#X_decode_as_subscr =0  #cannot, 3 args  #a[b] is faster than a.method(b)
#X_decode_self_cache =0 ?? less args= less noise but same speed probably or slower
X_is_cache_key_as_subscr =0     #no much gain..    #a[b] is faster than a.method(b)
X_is_cache_key_eq_in_cache =1   #better this.. avoid is_cache_key() at all
X_parse_string = 1
X_decoders_direct =1    # remove klass.from_rep , direct funcs instead
X_tag_in_decoders =1
X_decode_str_with_parse =1  #only done with RollingCache.X_rework, X_tag_in_decoders, no X_mapkeystr

from collections import OrderedDict

from transit import transit_types
from transit import read_handlers as rh
from transit.helpers import pairs
from transit.transit_types import true, false
from transit.constants import MAP_AS_ARR, ESC, SUB, RES
from transit.rolling_cache import RollingCache, is_cacheable, is_cache_key

if X_is_cache_key_as_subscr:
  class _is_cache_key:
    __getitem__ = staticmethod( is_cache_key)
  is_cache_key_as_subscr = _is_cache_key()    #singleton
  class _is_cacheable:
    @staticmethod
    def __getitem__( args ):
        return is_cacheable( *args)
  is_cacheable_as_subscr = _is_cacheable()    #singleton

assert getattr( rh, 'X_plain', 0) and X_decoders_direct

class Tag(object):
    def __init__(self, tag):
        self.tag = tag


default_options = {
    "decoders": {
        "_": rh.NoneHandler,
        ":": rh.KeywordHandler,
        "$": rh.SymbolHandler,
        "?": rh.BooleanHandler,
        "i": rh.IntHandler,
        "d": rh.FloatHandler,
        "f": rh.BigDecimalHandler,
        "u": rh.UuidHandler,
        "r": rh.UriHandler,
        "t": rh.DateHandler,
        "m": rh.DateHandler,
        "n": rh.BigIntegerHandler,
        "z": rh.SpecialNumbersHandler,
        "link": rh.LinkHandler,
        "list": rh.ListHandler,
        "set": rh.SetHandler,
        "cmap": rh.CmapHandler,
        "'": rh.IdentityHandler,
    },
    "default_decoder": rh.DefaultHandler,
}

ground_decoders = {
    "_": rh.NoneHandler,
    "?": rh.BooleanHandler,
    "i": rh.IntHandler,
    "'": rh.IdentityHandler,
}

if X_tag_in_decoders:
    assert X_decoders_direct
    ground_decoders[ "#" ] = Tag

class Decoder(object):
    """The Decoder is the lowest level entry point for parsing, decoding, and
    fully converting Transit data into Python objects.

    During the creation of a Decoder object, you can specify custom options
    in a dictionary.  One such option is 'decoders'.  Note that while you
    can specify your own decoders and override many of the built in decoders,
    some decoders are silently enforced and cannot be overriden.  These are
    known as Ground Decoders, and are needed to maintain bottom-tier
    compatibility.
    """
    map_factory = transit_types.frozendict

    def __init__(self, options={}):
        self.options = default_options.copy()
        self.options.update(options)

        self.decoders = self.options["decoders"]
        # Always ensure we control the ground decoders
        self.decoders.update(ground_decoders)
        if X_decode_map:
            self.make_decode_map()
        if X_decoders_direct:
            def from_repper(x): return getattr( x, 'from_rep', x)
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

    def _decode(self, node, cache, as_map_key):
        #tp = type(node)
        tp = node.__class__
        if tp is str:
            return self.decode_string(node, cache, as_map_key)
        elif tp is bytes:
            return self.decode_string(node.decode("utf-8"), cache, as_map_key)
        elif tp is dict or tp is OrderedDict:
            return self.decode_hash(node, cache, as_map_key)
        elif tp is list:
            return self.decode_list(node, cache, as_map_key)
        elif tp is bool:
            return true if node else false
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
        """Special case decodes map-as-array.
        Otherwise lists are treated as Python lists.

        Arguments follow the same convention as the top-level 'decode'
        function.
        """
        self_decode = self._decode
        if node:
            if node[0] == MAP_AS_ARR:
                # key must be decoded before value for caching to work.
                if X_mapcompreh:
                    # ... doc/python3/html/reference/expressions.html#dictionary-displays - Starting with 3.8, the key is evaluated before the value
                    return self.map_factory( {  #pff slower than below..
                        self_decode(k, cache, _X_mapkeystr) : self_decode(v, cache, as_map_key)
                        for k,v in pairs(node[1:])
                        })
                returned_dict = {}
                for k, v in pairs(node[1:]):
                    key = self_decode(k, cache, _X_mapkeystr)
                    val = self_decode(v, cache, as_map_key)
                    returned_dict[key] = val
                return self.map_factory(returned_dict)

            decoded = self_decode(node[0], cache, as_map_key)
            if isinstance(decoded, Tag):
                return self.decode_tag(decoded.tag, self_decode(node[1], cache, as_map_key))
            if X_FIX_ARRAY:
                # XXX fallthrough???     hahah will repeate parseing node[0] ..broken cache
                return (decoded, *[self_decode(x, cache, as_map_key) for x in node[1:]])
        return tuple(self_decode(x, cache, as_map_key) for x in node)

    def decode_string(self, string, cache, as_map_key):
        """Decode a string - arguments follow the same convention as the
        top-level 'decode' function.
        """
        if is_cache_key(string):
            return self.parse_string(cache.decode(string, as_map_key), cache, as_map_key)
        if is_cacheable(string, as_map_key):
            cache.encode(string, as_map_key)
        return self.parse_string(string, cache, as_map_key)

    if getattr( RollingCache, 'X_rework', 0):
      def decode_string(self, string, cache, as_map_key):
        if is_cache_key(string):
            return cache[ string ]
        pstring = self.parse_string(string, None, as_map_key)   #java:ReadCache.cacheRead does this inside
        if is_cacheable(string, as_map_key):
            cache.encache(pstring, True)
        return pstring

    def decode_tag(self, tag, rep):
        decoder = self.decoders.get(tag, None)
        if decoder:
            return decoder(rep)
        else:
            return self.options["default_decoder"](tag, rep)

    def decode_hash(self, hash, cache, as_map_key):
        self_decode = self._decode
        if len(hash) != 1:
            if X_mapcompreh:
                    # ... doc/python3/html/reference/expressions.html#dictionary-displays - Starting with 3.8, the key is evaluated before the value
                    return self.map_factory( {  #pff slower than below..
                        self_decode(k, cache, _X_mapkeystr) : self_decode(v, cache, False)
                        for k,v in hash.items()
                        })
            h = {}
            for k, v in hash.items():
                # crude/verbose implementation, but this is only version that
                # plays nice w/cache for both msgpack and json thus far.
                # -- e.g., we have to specify encode/decode order for key/val
                # -- explicitly, all implicit ordering has broken in corner
                # -- cases, thus these extraneous seeming assignments
                key = self_decode(k, cache, _X_mapkeystr)
                val = self_decode(v, cache, False)
                h[key] = val
            return self.map_factory(h)
        else:
            key = list(hash)[0]
            value = hash[key]
            key = self_decode(key, cache, True)
            if isinstance(key, Tag):
                return self.decode_tag(key.tag, self_decode(value, cache, as_map_key))
        return self.map_factory({key: self_decode(value, cache, False)})

    def parse_string(self, string, cache, as_map_key):
        if string.startswith(ESC):
            m = string[1]

            if X_mapkeystr:
              if m==':' and as_map_key==_X_mapkeystr and as_map_key in self.decoders: #not assumed
                return self.decoders[ as_map_key ](string[2:])
            if m in self.decoders:
                return self.decoders[m](string[2:])
            elif m == ESC or m == SUB or m == RES:
                return string[1:]
            elif m == "#":
                return Tag(string[2:])
            else:
                return self.options["default_decoder"](string[1], string[2:])
        return string

    _escaped = SUB+ESC+RES
    if X_parse_string and X_mapkeystr:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m==':' and as_map_key==_X_mapkeystr and as_map_key in decoders: #not assumed
                return decoders[ as_map_key ](string[2:])
            if m in decoders:
                return decoders[m](string[2:])
            elif m in self._escaped:
                return string[1:]
            elif m == "#":
                return Tag(string[2:])
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if X_parse_string and not X_mapkeystr:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                return decoders[m](string[2:])
            elif m in self._escaped:
                return string[1:]
            elif m == "#":
                return Tag(string[2:])
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if X_parse_string and not X_mapkeystr and X_tag_in_decoders:
      def parse_string(self, string, cache, as_map_key):
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                return decoders[m](string[2:])
            elif m in self._escaped:
                return string[1:]
            else:
                return self.options["default_decoder"]( m, string[2:])
        return string
    if all([ X_decode_str_with_parse , X_is_cache_key_eq_in_cache ,
        getattr( RollingCache, 'X_rework', 0) ,
        not X_mapkeystr , X_tag_in_decoders ,
        ]):
       def decode_string(self, string, cache, as_map_key):
        #if is_cache_key(string):
        if string in cache:
            return cache[ string ]

        #pstring = self.parse_string(string.. #java:ReadCache.cacheRead does this inside
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                pstring = decoders[m](string[2:])
            elif m in self._escaped:
                pstring = string[1:]
            else:
                pstring = self.options["default_decoder"]( m, string[2:])
        else: pstring = string

        if is_cacheable(string, as_map_key):
            cache.encache(pstring, True)
        return pstring
    if all([ X_decode_str_with_parse , X_is_cache_key_eq_in_cache ,
        getattr( RollingCache, 'X_rework', 0) ,
        not X_mapkeystr , X_tag_in_decoders ,
        getattr( RollingCache, 'X_is_cacheable_inside_encache', 0)
        ]):
       def decode_string(self, string, cache, as_map_key):
        #if is_cache_key(string):
        if string in cache: return cache[ string ]

        #pstring = self.parse_string(string.. #java:ReadCache.cacheRead does this inside
        if string and string[0] == ESC:
            m = string[1]
            decoders = self.decoders
            if m in decoders:
                pstring = decoders[m](string[2:])
            elif m in self._escaped:
                pstring = string[1:]
            else:
                pstring = self.options["default_decoder"]( m, string[2:])
        else: pstring = string

        #is_cacheable( string.. is inside
        cache.encache( pstring, True, as_map_key, string)
        return pstring


    def register(self, key_or_tag, obj):
        """Register a custom Transit tag and new parsing function with the
        decoder.  Also, you can optionally set the 'default_decoder' with
        this function.  Your new tag and parse/decode function will be added
        to the interal dictionary of decoders for this Decoder object.
        """
        if X_decoders_direct: obj = getattr( obj, 'from_rep', obj)
        if key_or_tag == "default_decoder":
            self.options["default_decoder"] = obj
        else:
            self.decoders[key_or_tag] = obj

