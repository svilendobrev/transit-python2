## svd@2024
'''
Fixed (caching) and faster heir of transit-python2
- decoder is py-to-py, so only python-optimized - about 2x faster
- encoder is now py-to-py too (was py-to-json-direct), removed json-ing, can use any json-encoder lib - about 2x faster
- btw assumption: if something looks-like cache-key, it will be in the cache

from tt.decode import Decoder
rdr = Decoder()     #can be static/global
#rdr.register( fancytag, fancyHandler_func_or_class_having_from_rep)
py_result = rdr.decode( input_py_data_out_of_json)

from tt.encode import Prejson
wrt = ttencode.Prejson()    #can be static/global
#wrt.register( fancytype, fancyWHandler)
py_data_for_json = wrt.encode( py_input)
json_result = json.dumps( py_data_for_json)
'''

TODO = '''
* try subscr[a:b:c] instead of 2-3 arg func_call(a,b,c)
* try encode-gzip-unzip-decode with and without that rolling-cache
* + keep for-loop map_factory for pre-3.8 compat
* try diff. MIN_SIZE_CACHEABLE
* +0.5% try split cache.encache into encache_k2v and encache_v2k
* ~0.5% try embed emit_string
* +     combinations of above
* +0.5% try check if handler.rep is rep_x
* +? emit..(args) instead of emit..(kargs,**ignored)
'''

