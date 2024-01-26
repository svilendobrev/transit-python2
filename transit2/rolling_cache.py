#from transit.rolling_cache import RollingCache     #original was broken..
## see transit-java-code/impl/ReadCache.java + transit-java-code/impl/WriteCache.java
# usage in writer.emit_string and Decoder.decode_string

FIRST_ORD = 48
CACHE_CODE_DIGITS = 44
CACHE_SIZE = CACHE_CODE_DIGITS * CACHE_CODE_DIGITS
MIN_SIZE_CACHEABLE = 4

#ReadCache.cacheCode
#def is_cache_key(name):
#    return name and (name[0] == SUB and name != MAP_AS_ARR)

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

