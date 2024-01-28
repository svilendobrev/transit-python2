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

from transit.constants import SUB, ESC, RES, MAP_AS_ARR, QUOTE

#from transit.write_handlers import X_wHandler_tag_len_1, X_wHandler_tag_str, WriteHandler
import uuid, datetime, struct, decimal
from transit.class_hash import ClassDict
from transit.transit_types import Keyword, Symbol, URI, frozendict, TaggedValue, Link, Boolean
from math import isnan
MAX_INT = pow(2, 63) - 1
MIN_INT = -pow(2, 63)

class TaggedMap:
    def __init__(self, tag, rep, str):
        self._tag = tag
        self._rep = rep
        self._str = str
    def tag(self): return self._tag
    def rep(self): return self._rep
    def string_rep(self): return self._str

class DateTimeHandler:
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC)
    @staticmethod
    def tag(_): return "m"
    @staticmethod
    def rep(d):
        td = d - DateTimeHandler.epoch
        return int((td.microseconds + (td.seconds + td.days * 24 * 3600) * pow(10, 6)) / 1e3)
    @classmethod
    def string_rep(d): return str(DateTimeHandler.rep(d))

float_infp= float("Inf")
float_infn= float("-Inf")
class FloatHandler:
    tag_len_1 = True
    tag_str = None
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

wh_all = {}
class wHandler:
    __slots__ = 'tag rep string_rep tag_len_1 tag_str'.split()
    def __init__( me, *types, tag, rep, str, tag_len_1 =False):
        me.tag = tag if callable( tag) else lambda x: tag
        me.rep = rep
        me.string_rep = str
        #tag_len_1: precalc, True or False or None; None meaning do check .tag() dynamically
        #if X_wHandler_tag_len_1:
        me.tag_len_1 = tag_len_1 or (len(tag)==1 if not callable( tag) else None)
        #if X_wHandler_tag_str:
        me.tag_str = tag if not callable( tag) else None
        for t in types: wh_all[ t ] = me
    @classmethod
    def copy( me, o, *, tag =None, rep =None, str =None):
        return me( tag= tag or o.tag, rep= rep or o.rep, str= str or o.string_rep)

def rep_x(x): return x
def rep_None(x): return None
NoneHandler         = wHandler( type(None), tag= '_'  , rep= rep_None , str= rep_None)
#IntHandler          = wHandler( int,        tag= 'i'  , rep= rep_x    , str= str )
#BigIntHandler       = wHandler( int,        tag= 'n'  , rep= str      , str= str )
Python3IntHandler   = wHandler( int,        tag= lambda x: 'i' if MIN_INT < x < MAX_INT else 'n', rep= rep_x, str= str, tag_len_1 =True)
BigDecimalHandler   = wHandler( decimal.Decimal, tag= 'f'  , rep= str      , str= str)
StringHandler       = wHandler( str,            tag= 's'    , rep= rep_x    , str= rep_x )
BooleanHandler      = wHandler( bool, Boolean,  tag= '?'    , rep= bool     , str= lambda x: "t" if x else "f")
ArrayHandler        = wHandler( list, tuple,    tag= 'array', rep= rep_x    , str= rep_None)
MapHandler          = wHandler( dict, frozendict, tag= 'map', rep= rep_x    , str= rep_None)
KeywordHandler      = wHandler( Keyword,    tag= ':'    , rep= str      , str= str)
SymbolHandler       = wHandler( Symbol,     tag= '$'    , rep= str      , str= str)
UuidHandler         = wHandler( uuid.UUID,  tag= 'u'    , rep= lambda x: struct.unpack(">qq", x.bytes), str= str)
UriHandler          = wHandler( URI,        tag= 'r'    , rep= lambda x: x.rep,     str= lambda x: x.rep)
#too complex ? DateTimeHandler(object):
DateTimeHandler.tag_len_1 = True
DateTimeHandler.tag_str = DateTimeHandler.tag(1)
#no types, will not go in wh_all
VerboseDateTimeHandler = wHandler(              tag= 't'    , rep= lambda x: x.isoformat()  , str= lambda x: x.isoformat())
SetHandler          = wHandler( set, frozenset, tag= 'set'  , rep= lambda x: TaggedMap("array", tuple(x), None),    str= rep_None)
TaggedValueHandler  = wHandler( TaggedValue,    tag= lambda x: x.tag, rep= lambda x: x.rep  , str= rep_None)
LinkHandler         = wHandler( Link,           tag= 'link' , rep= lambda x: x.as_map       , str= rep_None)
klasi = {
    float: FloatHandler,
    datetime.datetime: DateTimeHandler,
    TaggedMap: TaggedMap,
    }
for klas in klasi.values():
    if not hasattr( klas, 'tag_len_1'): klas.tag_len_1 = None
    if not hasattr( klas, 'tag_str'):   klas.tag_str = None
wh_all.update( klasi)

def WriteHandler():
    'dispatcher for encoding/writing Python data into Transit data, based on its type, and inheritance'
    return ClassDict( wh_all)

########### eo write_handlers

from tt.rolling_cache import RollingCache

JSON_MAX_INT = pow(2, 53) - 1
JSON_MIN_INT = -pow(2, 53) + 1

_escaped = SUB+ESC+RES
def escape(s):
    if s is MAP_AS_ARR: return MAP_AS_ARR
    if s and s[0] in _escaped: return ESC + s
    return s
def flatten_map(m):
    """Expand a dictionary's items into a flat list"""
    return [item for t in m.items() for item in t]



X_marshal_str_shortcut = 10     #faster than emit_string2+X_emit_string2_embeds
X_emit_string2_embeds = 0       #does not matter if X_marshal_str_shortcut =1
X_encache_split = 10 and RollingCache.X_encache_split
X_encode_in_cache = 0 and RollingCache.X_encache_split
X_encode_instead_of_emit_str = 0 and RollingCache.X_encache_split
X_marshal_embeds_emit_string_no_encode =10 and RollingCache.X_encache_split
X_encoded_embeds_emit_string_no_encode =10 and RollingCache.X_encache_split
X_handler_rep_x =1
X_emit_xx_args_instead_of_kargs_ignored =1     # lambda rep, as_map_key, cache, obj, tag: ..

assert RollingCache.X_is_cacheable_inside_encache
assert X_emit_xx_args_instead_of_kargs_ignored
def emit_string( rep, as_map_key, cache, _obj, _tag):
    if rep in cache: return cache[ rep]
    cache.encache( rep, False, as_map_key)
    return rep
def emit_string2( rep, as_map_key, cache, _obj, _tag):
    return emit_string( escape(rep), as_map_key, cache, 0,0)
if X_encache_split:
  def emit_string( rep, as_map_key, cache, _obj, _tag):
    if rep in cache: return cache[ rep]
    return cache.encache_encode_v2k( rep, as_map_key)
  if X_emit_string2_embeds:
    def emit_string2( rep, as_map_key, cache, _obj, _tag):
        rep = escape( rep)
        if rep in cache: return cache[ rep]
        return cache.encache_encode_v2k( rep, as_map_key)
if X_encode_in_cache:
  def emit_string( rep, as_map_key, cache, _obj, _tag):
    return cache.encode( rep, as_map_key)
  if X_emit_string2_embeds:
    def emit_string2( rep, as_map_key, cache, _obj, _tag):
        return cache.encode( escape( rep), as_map_key)

if X_marshal_str_shortcut:
    emit_string2 = 0

''' comparing these is tricky.. diffs are minimal:
1.default (RollingCache.X_is_cacheable_inside_encache)
- call emit_string: check if name in cache, ret else call cache.encache with if-switch inside
2.RollingCache.X_encache_split
- call emit_string: check if name in cache, ret else call cache.encache_encode_v2k
3.X_encode_in_cache
- call emit_string: call cache.encode: check if name in cache, ret else ..doit
4.X_encode_instead_of_emit_str
- call cache.encode: check if name in cache else ..encache

in happy path - name in cache :
    1 - global+call, dict-check, ret  << fastest
    2 - global+call, dict-check, ret  << same=fastest
    4 - local+getattr+call, dict-check, ret
    3 - global+call, local+getattr+call, dict-check, ret
in unhappy path - not in cache
    4 - local+ getattr+ call + dict-check , doit  << fastest
    2 - global,call, dict-check, local+getattr+call, doit
    3 - global,call, local+getattr+call, dict-check, doit
    1 - global,call, dict-check, local+getattr+call , if-switch, doit

sooo: embedding 2 might be best:
5 X_marshal_str_shortcut + X_marshal_embeds_emit_string2_emit_string (escape():always)
- check if (escaped) name in cache, else call cache.encache_encode_v2k
  happy: dict-check, ret
  unhappy: dict-check, local+getattr+call, doit

'''

# emit_string in these matter if as_map_key.. rarely
def emit_nil( rep, as_map_key, cache, _obj, _tag):
    return emit_string( ESC+ "_", True, cache, 0,0) if as_map_key else None
def emit_boolean( rep, as_map_key, cache, _obj, _tag):
    return emit_string( ESC+ "?"+ rep, True, cache, 0,0) if as_map_key else rep
def emit_int( rep, as_map_key, cache, obj, tag):
    if isinstance(rep, int) and JSON_MIN_INT <= obj <= JSON_MAX_INT:
        return obj
    return emit_string( ESC+ tag+ str(rep), as_map_key, cache, 0,0)
def emit_double( rep, as_map_key, cache, _obj, _tag):
    return emit_string( ESC+ "d"+ rep, True, cache, 0,0) if as_map_key else rep


class Prejson: #( Marshaler):
    #X_map_with_extend=0            # no, r.append x2 is faster than r_append x2 than extend(tuple)
    X_map_embeds_marshal =0
    X_arr_embeds_marshal =0

    def __init__(self, opts={}):
        self.opts = opts
        self.handlers = WriteHandler()
        self.marshal_dispatch = {
            "_": emit_nil,
            "?": emit_boolean,
            "s": emit_string2,     #does escape()
            "i": emit_int,
            "n": emit_int,
            "d": emit_double,
            "'":     self.emit_tagged,
            "array": self.emit_array,
            "map":   self.dispatch_map,
            }
    #~straight copy from Marshaler
    def register(self, obj_type, handler_class):
        'Register custom converters for object types'
        self.handlers[obj_type] = handler_class
    #~straight copy from Marshaler
    def marshal_top(self, obj, cache=None):
        'passed whole input data, returns transit-data. No local state is kept'
        if not cache:
            cache = RollingCache()
        handler = self.handlers[obj]
        tag = handler.tag(obj)
        assert tag, f"Handler must provide a non-nil tag: {handler}"
        if len(tag) == 1:
            return self.marshal(TaggedValue(QUOTE, obj), False, cache)
        return self.marshal(obj, False, cache)
    encode = marshal_top
    #eo public stuff

    def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            return xmarshal_dispatch[ tag ](
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                as_map_key, cache, obj, tag #tag-for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)
    if X_handler_rep_x:
      def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            repper = handler.string_rep if as_map_key else handler.rep
            return xmarshal_dispatch[ tag ](
                obj if repper is rep_x else repper( obj),
                as_map_key, cache, obj, tag #obj+tag for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)

    if X_marshal_str_shortcut:
      def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        if tag == "s":  #X_marshal_str_shortcut and  :most frequent case
            return emit_string( escape(
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                ), as_map_key, cache, 0,0)

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            return xmarshal_dispatch[ tag ](
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                as_map_key, cache, obj, tag #obj+tag for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)
    if X_marshal_str_shortcut and X_handler_rep_x:
      def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        if tag == "s":  #X_marshal_str_shortcut and  :most frequent case
            repper = handler.string_rep if as_map_key else handler.rep
            return emit_string( escape(
                obj if repper is rep_x else repper( obj),
                ), as_map_key, cache, 0,0)

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            repper = handler.string_rep if as_map_key else handler.rep
            return xmarshal_dispatch[ tag ](
                obj if repper is rep_x else repper( obj),
                as_map_key, cache, obj, tag #obj+tag for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)
    if X_marshal_str_shortcut and X_encode_instead_of_emit_str:
      def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        if tag == "s":  #X_marshal_str_shortcut and  :most frequent case
            return cache.encode( escape(
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                ), as_map_key)

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            return xmarshal_dispatch[ tag ](
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                as_map_key, cache, obj, tag #obj+tag for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)
    if X_marshal_str_shortcut and X_marshal_embeds_emit_string_no_encode:
      def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        if tag == "s":  #X_marshal_str_shortcut and  :most frequent case
            rep = escape(
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                )
            if rep in cache: return cache[ rep]
            return cache.encache_encode_v2k( rep, as_map_key)

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            return xmarshal_dispatch[ tag ](
                handler.string_rep(obj) if as_map_key else handler.rep(obj),
                as_map_key, cache, obj, tag #obj+tag for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)
    if X_marshal_str_shortcut and X_marshal_embeds_emit_string_no_encode and X_handler_rep_x:
      def marshal(self, obj, as_map_key, cache):
        handler = self.handlers[obj]
        tag = handler.tag_str or handler.tag(obj)       #+gain X_wHandler_tag_str

        if tag == "s":  #X_marshal_str_shortcut and  :most frequent case
            repper = handler.string_rep if as_map_key else handler.rep
            rep = escape(
                obj if repper is rep_x else repper( obj),
                )
            if rep in cache: return cache[ rep]
            return cache.encache_encode_v2k( rep, as_map_key)

        xmarshal_dispatch = self.marshal_dispatch
        if tag in xmarshal_dispatch:
            repper = handler.string_rep if as_map_key else handler.rep
            return xmarshal_dispatch[ tag ](
                obj if repper is rep_x else repper( obj),
                as_map_key, cache, obj, tag #obj+tag for int
                )
        return self.emit_encoded(tag, handler, obj, as_map_key, cache)

    def emit_array(self, rep, as_map_key, cache, _obj, _tag):
        marshal = self.marshal
        return [ marshal( x, False, cache) for x in rep ]
    if X_arr_embeds_marshal:
      def emit_array(self, rep, as_map_key, cache, _obj, _tag):
        r = []
        #append = r.append      #r.append(x) is faster than r_append(x)
        handlers = self.handlers
        emit_encoded = self.emit_encoded
        as_map_key = False
        xmarshal_dispatch = self.marshal_dispatch
        for obj in rep:
            handler = handlers[obj]
            tag = handler.tag_str or handler.tag(obj)       #X_wHandler_tag_str
            if tag in xmarshal_dispatch:
                x = xmarshal_dispatch[ tag ](
                    tag, obj,
                    handler.string_rep(obj) if as_map_key else handler.rep(obj),
                    as_map_key, cache,
                    )
            else:
                x= emit_encoded(tag, handler, obj, as_map_key, cache)
            r.append( x)
        return r

    def emit_map(self, obj, as_map_key, cache):
        marshal = self.marshal
        r = [ MAP_AS_ARR ]
        for k,v in obj.items():
            r.append( marshal( k, True, cache))
            r.append( marshal( v, False, cache))
            #XXX r.append x2 is faster than r_append x2 is faster than r.extend(tuple)
        return r
    if X_map_embeds_marshal:
      def emit_map(self, obj, as_map_key, cache):
        r = [ MAP_AS_ARR ]
        #append = r.append      #r.append(x) is faster than r_append(x)
        handlers = self.handlers
        emit_encoded = self.emit_encoded
        map = obj
        xmarshal_dispatch = self.marshal_dispatch
        for k,v in map.items():
          for obj,as_map_key in ((k,True),(v,False)): #zip( kv,(True, False)):
            handler = handlers[obj]
            tag = handler.tag_str or handler.tag(obj)       #X_wHandler_tag_str
            if tag in xmarshal_dispatch:
                x = xmarshal_dispatch[ tag ](
                    tag, obj,
                    handler.string_rep(obj) if as_map_key else handler.rep(obj),
                    as_map_key, cache,
                    )
            else:
                x= emit_encoded(tag, handler, obj, as_map_key, cache)
            r.append( x)
        return r

    def emit_cmap(self, rep, _as_map_key, cache, _obj, _tag):
        return {
            emit_string( ESC+ "#cmap", True, cache, 0,0) :
            self.marshal(flatten_map(m), False, cache)      #cannot call directly self.emit_array.. handler[list] may be other
            }
    def emit_tagged(self, rep, _as_map_key, cache, _obj, tag):
        return [
            emit_string( ESC+ "#"+ tag, False, cache, 0,0),
            self.marshal(rep, False, cache),
            ]
    if X_encode_instead_of_emit_str:
      def emit_tagged(self, rep, _as_map_key, cache, _obj, tag):
        return [
            cache.encode( ESC+ "#"+ tag, False),
            self.marshal(rep, False, cache),
            ]

    def emit_encoded(self, tag, handler, obj, as_map_key, cache):
        rep = handler.rep(obj)
        if len(tag) == 1:
            if isinstance(rep, str):
                return emit_string( ESC+ tag+ rep, as_map_key, cache, 0,0)
            elif as_map_key or self.opts.get("prefer_strings"):
                rep = handler.string_rep(obj)
                assert isinstance(rep, str), f"Cannot be encoded as string: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
                return emit_string( ESC+ tag+ rep, as_map_key, cache, 0,0)
            #fallthrough
        else:
            assert not as_map_key, f"Cannot be used as a map key: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
        return self.emit_tagged( rep, 0, cache, 0, tag)
    if X_handler_rep_x:
      def emit_encoded(self, tag, handler, obj, as_map_key, cache):
        repper = handler.rep
        rep = obj if repper is rep_x else repper( obj)
        if len(tag) == 1:
            if isinstance(rep, str):
                return emit_string( ESC+ tag+ rep, as_map_key, cache, 0,0)
            elif as_map_key or self.opts.get("prefer_strings"):
                rep = handler.string_rep(obj)
                assert isinstance(rep, str), f"Cannot be encoded as string: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
                return emit_string( ESC+ tag+ rep, as_map_key, cache, 0,0)
            #fallthrough
        else:
            assert not as_map_key, f"Cannot be used as a map key: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
        return self.emit_tagged( rep, 0, cache, 0, tag)
    if X_encode_instead_of_emit_str:
      def emit_encoded(self, tag, handler, obj, as_map_key, cache):
        rep = handler.rep(obj)
        if len(tag) == 1:
            if isinstance(rep, str):
                return cache.encode( ESC+ tag+ rep, as_map_key)
            elif as_map_key or self.opts.get("prefer_strings"):
                rep = handler.string_rep(obj)
                assert isinstance(rep, str), f"Cannot be encoded as string: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
                return cache.encode( ESC+ tag+ rep, as_map_key)
            #fallthrough
        else:
            assert not as_map_key, f"Cannot be used as a map key: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
        return self.emit_tagged( rep, 0, cache, 0, tag)
    if X_encoded_embeds_emit_string_no_encode:
      def emit_encoded(self, tag, handler, obj, as_map_key, cache):
        rep = handler.rep(obj)
        if len(tag) == 1:
            if isinstance(rep, str):
                rep = ESC+ tag+ rep
                if rep in cache: return cache[ rep]
                return cache.encache_encode_v2k( rep, as_map_key)
            elif as_map_key or self.opts.get("prefer_strings"):
                rep = handler.string_rep(obj)
                assert isinstance(rep, str), f"Cannot be encoded as string: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
                rep = ESC+ tag+ rep
                if rep in cache: return cache[ rep]
                return cache.encache_encode_v2k( rep, as_map_key)
            #fallthrough
        else:
            assert not as_map_key, f"Cannot be used as a map key: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
        return self.emit_tagged( rep, 0, cache, 0, tag)
    if X_encoded_embeds_emit_string_no_encode and X_handler_rep_x:
      def emit_encoded(self, tag, handler, obj, as_map_key, cache):
        repper = handler.rep
        rep = obj if repper is rep_x else repper( obj)
        if len(tag) == 1:
            if isinstance(rep, str):
                rep = ESC+ tag+ rep
                if rep in cache: return cache[ rep]
                return cache.encache_encode_v2k( rep, as_map_key)
            elif as_map_key or self.opts.get("prefer_strings"):
                rep = handler.string_rep(obj)
                assert isinstance(rep, str), f"Cannot be encoded as string: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
                rep = ESC+ tag+ rep
                if rep in cache: return cache[ rep]
                return cache.encache_encode_v2k( rep, as_map_key)
            #fallthrough
        else:
            assert not as_map_key, f"Cannot be used as a map key: {str({'tag': tag, 'rep': rep, 'obj': obj})}"
        return self.emit_tagged( rep, 0, cache, 0, tag)

    def dispatch_map(self, rep, as_map_key, cache, _obj, _tag):
        'either simple map with string-keys, or complex map, with keys of compound types'
        #emit_map() if are_stringable_keys() else emit_cmap()
        #if X_wHandler_tag_len_1:
        handlers = self.handlers
        for x in rep:
            handler = handlers[x]
            tag_len_1 = handler.tag_len_1
            if tag_len_1: continue
            #special for dynamic tags.. TaggedMap and TaggedValueHandler will call .tag()
            if tag_len_1 is False or len(handler.tag(x)) != 1:
                #found non-stringable, bye
                return self.emit_cmap(rep, as_map_key, cache, 0,0)
        #not found non-stringable
        return self.emit_map(rep, as_map_key, cache)


if __name__ == '__main__':
    p = Prejson()
    print( p.marshal_top( [ 1, 'asdf',
        { 'aw': 23 } , { 'aw': 45 } ,
        { 'awqw': 13 } , { 'awqw': 15 } ,
        ] ) )
    import json
    j = json.load( open( 'transit-format/examples/0.8/example.json'))

    from transit.decoder import Decoder
    from io import StringIO
    d = Decoder().decode( j)
    #print(d)
    from transit.writer import JsonMarshaler
    wr = JsonMarshaler( None)
    buf = StringIO()
    wr.reset( buf)
    wr.marshal_top( d)
    txjs = buf.getvalue()
    tx = json.loads( txjs)
    #print( tx)
    ptx = p.marshal_top( d)
    #print( ptx)
    for a,b in zip(tx,ptx):
        assert a==b,(a,b)
    assert tx==ptx

# vim:ts=4:sw=4:expandtab
