## svd@2024
'''
Fixed (caching) and faster variant of transit-python2
- decoder is py-to-py, so only python-optimized - about 2x faster
- encoder is now py-to-py too (was py-to-json-direct), removed json-ing, can use any json-encoder lib - about 2x faster
- btw assumption: on decode, if something looks-like cache-key, it has to be in the cache (so broken data will break things further)

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
* try encode-gzip-gunzip-decode with and without that rolling-cache
* + keep for-loop map_factory for pre-3.8 compat
* try diff. MIN_SIZE_CACHEABLE - breaks everything
* +0.5% try split cache.encache into encache_k2v and encache_v2k
* ~0.5% try embed emit_string
* +     combinations of above
* +0.5% try check if handler.rep is rep_x
* +3% emit..(args) instead of emit..(kargs,**ignored)
* decode with rep_x ?
* try return cache[name] except?
'''
SUGGESTIONS = '''
* get rid of keywords. :tablename? Pff. Identifiers (=symbols) are maybe okay, with rules of what is allowed..
  as one can send any crap and you have to deal with it - error or whatever.
* "transit" represents a static readonly snapshot of programmer's intent to execute on server. Server response is also readonly. So:
  * only tuples exist. Readonly. All lists are tuples. No point making diff. sequence vs vector
  * maps vs cmaps.. keep only one. Seems cmap is more general
* errors are incomprehensible.. esp. the combined clojure + java stacks. "Does not match grammar" without saying which is the culprit, is not helpful.
'''
