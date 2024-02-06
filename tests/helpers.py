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

from transit3.transit_types import Keyword, frozendict

import itertools
def mapcat(f, i):
    return itertools.chain.from_iterable(map(f, i))
cycle = itertools.cycle
def take(n, i):
    return itertools.islice(i, 0, n)

def ints_centered_on(m, n=5):
    return tuple(range(m - n, m + n + 1))

def array_of_symbols(m, n=None):
    if n is None:
        n = m

    seeds = [ Keyword("key" + str(x).zfill(4)) for x in range(0, m) ]
    return take(n, cycle(seeds))

def hash_of_size(n):
    return frozendict(zip(array_of_symbols(n), range(0, n + 1)))
