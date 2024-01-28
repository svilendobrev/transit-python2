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

#from transit.rolling_cache import RollingCache     #original was broken..
## see transit-java-code/impl/ReadCache.java + transit-java-code/impl/WriteCache.java
# usage in writer.emit_string and Decoder.decode_string

FIRST_ORD = 48
CACHE_CODE_DIGITS = 44
CACHE_SIZE = CACHE_CODE_DIGITS * CACHE_CODE_DIGITS
MIN_SIZE_CACHEABLE = 4
#XXX if above MIN_SIZE_CACHEABLE does not match the other side... TROUBLE

from tt.constants import SUB, MAP_AS_ARR
# ReadCache.cacheCode
def is_cache_key(name):     #the func maybe never used
    return name and (name[0] == SUB and name != MAP_AS_ARR)
# WriteCache.isCacheable
#def is_cacheable(string, as_map_key=False):    #embedded inside RollingCache.encache*
#    return len(string) >= MIN_SIZE_CACHEABLE and (as_map_key or (string[0]=='~' and string[1] in "#$:"))

# WriteCache.indexToCode
def encode_key(i):
    lo = i % CACHE_CODE_DIGITS
    hi = i // CACHE_CODE_DIGITS
    if hi == 0: return "^" + chr(lo + FIRST_ORD)
    return "^" + chr(hi + FIRST_ORD) + chr(lo + FIRST_ORD)

# ReadCache.codeToIndex
#def decode_key(s):
#    sz = len(s)
#    if sz == 2: return ord(s[1]) - FIRST_ORD
#    return (ord(s[2]) - FIRST_ORD) + (CACHE_CODE_DIGITS * (ord(s[1]) - FIRST_ORD))

#X_encode_key_map =1
encode_i2key_map = dict( (i,encode_key(i)) for i in range( CACHE_SIZE))

class RollingCache( dict):    #https://github.com/cognitect/transit-format
    #encode at ..emit_string ; decode at Decoder.decode_string
    #encache as of #~as of java:WriteCache.cacheWrite + ReadCache.cacheRead
    X_is_cacheable_inside_encache = 1
    def encache( self, name, key2name =False, as_map_key =False, name4is_cacheable =None):
        string = name4is_cacheable or name
        #if is_cacheable
        if len(string) >= MIN_SIZE_CACHEABLE and (as_map_key or (string[0]=='~' and string[1] in "#$:")) :
            l = len( self)
            if l >= CACHE_SIZE:
                self.clear()
                l = 0
            key = encode_i2key_map[ l ]
            if key2name:
                self[ key ] = name
            else:
                self[ name ] = key

    X_encache_split =1
    if X_encache_split:
      #encache = None
      def encache_decode_k2v( self, name, as_map_key, name4is_cacheable):  #decode
        #if is_cacheable
        if len(name4is_cacheable) >= MIN_SIZE_CACHEABLE and (as_map_key or (name4is_cacheable[0]=='~' and name4is_cacheable[1] in "#$:")) :
            l = len( self)
            if l >= CACHE_SIZE:
                self.clear()
                l = 0
            #key = encode_i2key_map[ l ]
            #self[ key ] = name
            self[ encode_i2key_map[ l ]] = name
        return name
      def encache_encode_v2k( self, name, as_map_key):     #encode
        #if is_cacheable
        if len(name) >= MIN_SIZE_CACHEABLE and (as_map_key or (name[0]=='~' and name[1] in "#$:")) :
            l = len( self)
            if l >= CACHE_SIZE:
                self.clear()
                l = 0
            #key = encode_i2key_map[ l ]
            #self[ name ] = key
            self[ name ] = encode_i2key_map[ l ]
        return name
      def encode( self, name, as_map_key):     #encode
        if name in self: return self[ name]
        #if is_cacheable
        if len(name) >= MIN_SIZE_CACHEABLE and (as_map_key or (name[0]=='~' and name[1] in "#$:")) :
            l = len( self)
            if l >= CACHE_SIZE:
                self.clear()
                l = 0
            #key = encode_i2key_map[ l ]
            #self[ name ] = key
            self[ name ] = encode_i2key_map[ l ]
        return name

# vim:ts=4:sw=4:expandtab
