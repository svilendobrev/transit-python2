#!/usr/bin/env python
# -*- coding: utf-8 -*-

#e.g.
# $ PYTHONPATH=. python benchmark/bench-transit.py transit-format/examples/0.8/example.json

from transit3 import encode, decode
print( *( f'{k}={v}\n' for k,v in [
    *encode.Encoder.__dict__.items(),
    *encode.__dict__.items(),
    *decode.Decoder.__dict__.items(),
    *decode.__dict__.items(),
    ] if k[:2]=='X_' or k[:2]=='Y_' ))

json_cfg = dict(
    ensure_ascii= False,      #nonascii -> utf8, not \u430
    separators= (',', ':'),  #no whitespaces
    )

ttenc = encode.Encoder()
def dump_py2ttpy( x):
    return ttenc.encode( x)
def dump_py2ttpy2json( x):
    ttpy = dump_py2ttpy( x)
    return json.dumps( ttpy, **json_cfg)
ttdec = decode.Decoder()     #for small data, this Decoder() is slower than the .decode :/
def load_ttpy2py( ttpy):
    return ttdec.decode( ttpy)
def load_json2ttpy2py( jstr):
    #x = x.decode( 'utf8')      #hope it's utf8 XXX ??
    ttpy = json.loads( jstr)
    return load_ttpy2py( ttpy)

try:
    from transit import write_handlers, writer, reader, decoder
    ORG = 1
except ImportError:
    print( '!warning, a "transit" module not found, not comparing')
    ORG = 0
else:
    from io import StringIO
    wrt = hasattr( writer.JsonMarshaler, 'reset') and writer.JsonMarshaler( None)
    rdr = reader.Reader( protocol= 'json')
    dec = decoder.Decoder()

    def dump_py2json_org( x):
        buf = StringIO()
        if not wrt:
            w = writer.Writer( buf, 'json' )
            regwrt( w)
            w.write( x )
        else:
            wrt.reset( buf)
            wrt.marshal_top( x)
        value = buf.getvalue()
        #valuebytes = value.encode( 'utf8')
        return value #bytes
    def load_json2ttpy2py_org( jstr):
        #rdr.register( dt_tag, DateHandler)
        #rdr.register( txkey_handler._tag, txkey_handler)
        return rdr.read( StringIO( jstr))
    def load_ttpy2py_org( ttpy):
        #dec.register( dt_tag, DateHandler)
        #dec.register( txkey_handler._tag, txkey_handler)
        return dec.decode( ttpy)
    #cross-lib
    decode.Keyword.__eq__            = lambda me, o: isinstance( o, decode.Keyword) and str.__eq__( me,o) or isinstance( o, write_handlers.Keyword) and str.__eq__( me, o.str)
    write_handlers.Keyword.__eq__    = lambda me, o: isinstance( o, decode.Keyword) and str.__eq__( me.str, o) or isinstance( o, write_handlers.Keyword) and str.__eq__( me.str,o.str)
    decode.frozendict.__eq__         = lambda me, o: isinstance( o, decode.frozendict) and dict.__eq__( me,o) or isinstance( o, write_handlers.frozendict) and dict.__eq__( me, o._dict)
    write_handlers.frozendict.__eq__ = lambda me, o: isinstance( o, decode.frozendict) and dict.__eq__( me._dict,o) or isinstance( o, write_handlers.frozendict) and me._dict == o._dict

#if 0:
    dt_tag = 'time/instant'
    if not getattr( write_handlers, 'X_wHandler', 0):
     class wMapHandler_auto_keywordize( write_handlers.MapHandler):
        @staticmethod
        def rep(m): return {
                        (write_handlers.Keyword( k) if k.__class__ is not write_handlers.Keyword else k):v
                        for k,v in m.items() }
     class wDatetimeHandler( write_handlers.VerboseDateTimeHandler):
        @staticmethod
        def tag(_): return dt_tag

     class wListHandler:
        @staticmethod
        def tag(_): return 'list'
        rep = list
    else:
        wHandler = write_handlers.wHandler
        wMapHandler_auto_keywordize = wHandler.copy( write_handlers.MapHandler,
            rep= lambda m: {
                        (write_handlers.Keyword( k) if k.__class__ is not write_handlers.Keyword else k):v
                        for k,v in m.items() }
            )
        wDatetimeHandler = wHandler.copy( write_handlers.VerboseDateTimeHandler,
            tag= dt_tag
            )
        wListHandler = wHandler( tag= 'list',
            rep= list,
            str= write_handlers.rep_None
            )
    import datetime
    def regwrt( wrt):
        wrt.register( dict, wMapHandler_auto_keywordize)
        #wrt.register( datetime.datetime, wDatetimeHandler)
        #wrt.register( List, wListHandler)     #tuple==list==array/vector
        #wrt.register( tuple, wListHandler)     #tuple -> xtdb/list i.e. sequence ; list -> vector
        wrt.register( decode.Keyword, write_handlers.KeywordHandler)    #cross-lib
    if wrt: regwrt( wrt)


import sys, json, pprint #, os.path
import timeit #.timeit .repeat
for f in sys.argv[1:]:
    if f =='-':
        fi = sys.stdin
        f = 'stdin'
    else:
        fi = open( f)

    indata = fi.read()
    loaded = json.loads( indata)
    parsed = load_ttpy2py( loaded)
    dumped = dump_py2ttpy( parsed)
    outdata= json.dumps( dumped, **json_cfg)
    if ORG:
        parsed_org  = load_ttpy2py_org( loaded)
        parsed_org2 = load_json2ttpy2py_org( indata)
        outdata_org = dump_py2json_org( parsed)
        dumpedx_org = json.loads( outdata_org)
    print( f,'..')
    def eqtest( **ka):
        (ka,a),(kb,b) = ka.items()
        sa = a.strip() if isinstance( a, str) else a
        sb = b.strip() if isinstance( b, str) else b
        if sa!=sb:
            print( f'XXXXXXXXXXX {ka} != {kb}:', )#sa, sb)
        return sa,sb

    eqtest( loaded = loaded , dumped= dumped)
    eqtest( outdata= outdata, indata= indata)
    stages = 'loaded parsed dumped outdata'.split()
    if ORG:
        eqtest( parsed= parsed, parsed_org= parsed_org)
        eqtest( parsed= parsed, parsed_org2=parsed_org2)
        eqtest( dumped= dumped, dumpedx_org= dumpedx_org)
        eqtest( outdata= outdata, outdata_org= outdata_org)
        stages += 'dumpedx_org parsed_org outdata_org'.split()
    if 0:
        from itertools import zip_longest
        for pos,(i,o) in enumerate( zip_longest( indata_strip, outdata_strip)):
            assert i==o, (pos,i,o)

    fname = f.split('/')[-1]
    for stage in stages:
        with open( fname + '.' + stage, 'w') as fo:
            data = locals()[ stage ]
            fo.write( str(type(data))+'\n')
            fo.write( data if isinstance( data, (str, bytes)) else pprint.pformat( data))

    def ptimeit( func, arg, n):
        import gc
        gc.collect()
        print( ' ', func.__name__, n,
            round( sorted( timeit.repeat( lambda: func( arg),
            #timeit.timeit( lambda: func( arg),
                setup= 'gc.enable();gc.collect()',   #do not disable it
                repeat=8,
                number= n))[0]
            , 3))


    Nload = 100
    Ndump1= 100
    Ndump2= 100
    MANY  = 20
    parsed_many = [ parsed ] * MANY
    loaded_many = loaded * MANY

    ptimeit( load_ttpy2py,      loaded, Nload)
    ptimeit( load_ttpy2py,      loaded_many, Nload//MANY)
    if ORG:
        ptimeit( load_ttpy2py_org,  loaded, Nload)
        ptimeit( load_ttpy2py_org,  loaded_many, Nload//MANY)
    ptimeit( load_json2ttpy2py,     indata, Nload)
    if ORG:
        ptimeit( load_json2ttpy2py_org, indata, Nload)

    ptimeit( dump_py2ttpy2json, parsed, Ndump2)
    ptimeit( dump_py2ttpy,      parsed, Ndump2)
    ptimeit( dump_py2ttpy,      parsed_many, Ndump2//MANY)
    if ORG:
        ptimeit( dump_py2json_org,  parsed, Ndump2)
        ptimeit( dump_py2json_org,  parsed_many, Ndump2//MANY)

if 0:
    import cProfile
    def loaddump100():
        #for i in range(Nload): load_ttpy2py( loaded)
        #for i in range(Ndump1): dumps_py2json( parsed)
        for i in range(Ndump2): dump_py2ttpy( parsed)
        #for i in range(Ndump3): dump_py2ttpy( parsed_many)
    cProfile.run( 'loaddump100()', fname+'.profile')
    import pstats, os
    cwd = os.getcwd()
    def func_strip_path(func_name):
        filename, line, name = func_name
        if filename.startswith( cwd): filename = './'+filename[ len(cwd):]
        #if options.rootstrip:
        #    filename = re.sub( options.rootstrip, '##', filename)
        #if options.strip:
        #    filename = re.sub( options.strip, '.#', filename)
        return filename, line, name
    pstats.func_strip_path = func_strip_path
    p = pstats.Stats( fname+'.profile')
    p.strip_dirs()
    p.sort_stats('time')
    p.print_stats( 25)

# vim:ts=4:sw=4:expandtab
