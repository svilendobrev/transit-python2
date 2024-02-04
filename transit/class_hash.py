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

X_simplify =1
X_simplify_plain_dict =0    #slower

from collections.abc import MutableMapping


class ClassDict(MutableMapping):
    """A dictionary that looks up class/type keys with inheritance."""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        key = key if isinstance(key, type) else type(key)
        if key in self.store:
            return self.store[key]
        else:
            for t in key.__bases__:
                value = t in self.store and self.store[t]
                if value:
                    return value
            # only use mro if __bases__ doesn't work to
            # avoid its perf overhead.
            for t in key.mro():
                value = t in self.store and self.store[t]
                if value:
                    return value
            raise KeyError(f"No handler found for: {key}")

    if X_simplify:
      def __getitem__(self, key):
        store = self.store

        #if not isinstance(key, type): key = type(key)   #same as key.__class__
        typ = key.__class__
        if typ in store: return store[ typ ]        #most frequent case
        if not isinstance(key, type): key = typ

        try:
            return store[key]
        except KeyError:
            #~~never comes here ??
            for t in key.__bases__:
                if t in store: return store[t]
            # only use mro if __bases__ doesn't work to
            # avoid its perf overhead.
            for t in key.mro():
                if t in store: return store[t]
            raise KeyError(f"No handler found for: {key}")

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

if X_simplify_plain_dict:   #slower than above.. cant use self[x], hence call getitem/get
  class ClassDict(dict):
    def __getitem__(store, key):
        typ = key.__class__
        store_get = store.get #super().get
        p = store_get( typ)        #most frequent case
        if p: return p
        if not isinstance(key, type): key = typ
        p = store_get( key)
        if p: return p
        else:
            #~~never comes here ??
            for t in key.__bases__:
                p = store_get( t)
                if p: return p
            # only use mro if __bases__ doesn't work to
            # avoid its perf overhead.
            for t in key.mro():
                p = store_get( t)
                if p: return p
            raise KeyError(f"No handler found for: {key}")

