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

X_rework =1
X_encode_key_map =1 # func-only: 40% less
X_is_cacheable =1   # func-only: 65% less
X_is_cache_key =1   # func-only: 15% less
X_is_cacheable_inside_encache =1

from transit.constants import SUB, MAP_AS_ARR

FIRST_ORD = 48
CACHE_CODE_DIGITS = 44
CACHE_SIZE = CACHE_CODE_DIGITS * CACHE_CODE_DIGITS
MIN_SIZE_CACHEABLE = 4

def is_cache_key(name):
    return len(name) and (name[0] == SUB and name != MAP_AS_ARR)
#ReadCache.cacheCode
if X_is_cache_key:
  def is_cache_key(name):
    return name and (name[0] == SUB and name != MAP_AS_ARR)


# WriteCache.indexToCode
def encode_key(i):
    lo = i % CACHE_CODE_DIGITS
    hi = i // CACHE_CODE_DIGITS
    if hi == 0:
        return "^" + chr(lo + FIRST_ORD)
    return "^" + chr(hi + FIRST_ORD) + chr(lo + FIRST_ORD)

# ReadCache.codeToIndex
def decode_key(s):
    sz = len(s)
    if sz == 2:
        return ord(s[1]) - FIRST_ORD
    return (ord(s[2]) - FIRST_ORD) + (CACHE_CODE_DIGITS * (ord(s[1]) - FIRST_ORD))

if X_encode_key_map:
    encode_i2key_map = dict( (i,encode_key(i)) for i in range( CACHE_SIZE))

def is_cacheable(string, as_map_key=False):
    return string and len(string) >= MIN_SIZE_CACHEABLE and (as_map_key or (string[:2] in ["~#", "~$", "~:"]))
#WriteCache.isCacheable
if X_is_cacheable:
  def is_cacheable(string, as_map_key=False):
    return len(string) >= MIN_SIZE_CACHEABLE and (as_map_key or (string[0]=='~' and string[1] in "#$:"))

class RollingCache(object):
    """This is the internal cache used by python-transit for cacheing and
    expanding map keys during writing and reading.  The cache enables transit
    to minimize the amount of duplicate data sent over the wire, effectively
    compressing down the overall payload size.  The cache is not intended to
    be used directly.
    """

    def __init__(self):
        self.key_to_value = {}
        self.value_to_key = {}

    # if index rolls over... (bug)
    def decode(self, name, as_map_key=False):
        """Always returns the name"""
        if is_cache_key(name) and (name in self.key_to_value):
            return self.key_to_value[name]
        return self.encache(name) if is_cacheable(name, as_map_key) else name

    def encode(self, name, as_map_key=False):
        """Returns the name the first time and the key after that"""
        if name in self.key_to_value:
            return self.key_to_value[name]
        return self.encache(name) if is_cacheable(name, as_map_key) else name

    def size(self):
        return len(self.key_to_value)

    def is_cache_full(self):
        return len(self.key_to_value) > CACHE_SIZE

    # cacheWrite
    def encache(self, name):
        if self.is_cache_full():
            self.clear()
        elif name in self.value_to_key:
            return self.value_to_key[name]

        key = encode_key(len(self.key_to_value))
        self.key_to_value[key] = name
        self.value_to_key[name] = key

        return name

    def clear(self):
        self.value_to_key = {}

if X_rework:
  #XXX this above is broken
  ## see transit-java-code/impl/ReadCache.java + transit-java-code/impl/WriteCache.java
  # usage in writer.emit_string and Decoder.decode_string

  class RollingCache( dict):    #https://github.com/cognitect/transit-format
    X_rework = X_rework
    def encode( self, name, as_map_key=False):     #as of java:WriteCache.cacheWrite
        #if not is_cacheable( name, as_map_key): return name
        if name in self: return self[ name]
        if is_cacheable( name, as_map_key):     #better here
            self.encache( name, False)
        return name
    #encode is at Writer.emit_string
    #decode is at Decoder.decode_string
    #encache as of #~as of java:WriteCache.cacheWrite + ReadCache.cacheRead
    def encache( self, name, key2name=False):
        l = len( self)
        if l >= CACHE_SIZE:
            self.clear()
            l = 0
        key = encode_key( l)
        if key2name:
            self[ key ] = name
        else:
            self[ name ] = key
        #return key,name
    if X_encode_key_map:
      def encache( self, name, key2name=False):
        l = len( self)
        if l >= CACHE_SIZE:
            self.clear()
            l = 0
        key = encode_i2key_map[ l ]
        if key2name:
            self[ key ] = name
        else:
            self[ name ] = key
        #return key,name

    if X_encode_key_map and X_is_cacheable_inside_encache:
      X_is_cacheable_inside_encache = X_is_cacheable_inside_encache
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
      def encode( self, name, as_map_key=False):     #as of java:WriteCache.cacheWrite
        if name in self: return self[ name]
        self.encache( name, False, as_map_key)
        return name

