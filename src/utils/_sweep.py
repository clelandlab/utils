"""Internal configuration sweeps and reproducible permutation helpers.

Copyright (c) 2024 Cleland Lab. Licensed under the MIT License; see LICENSE.
"""

import copy

import numpy as np
from tqdm.auto import tqdm

__all__ = ["Sweep", "feistel_network", "nested_get"]


def feistel_network(i, N, seed): # generate pseudo-random permutation
    half_bits = (N - 1).bit_length() // 2 + (N - 1).bit_length() % 2
    limit = 1 << half_bits
    mask = limit - 1
    def round_function(val, round_idx): # a variation of a 32-bit MurmurHash-style mixer.
        x = (val ^ seed ^ round_idx) * 0x45d9f3b
        x = ((x >> 16) ^ x) * 0x45d9f3b
        x = (x >> 16) ^ x
        return x & mask
    def permute(val):
        left = val >> half_bits
        right = val & mask
        for r in range(5):
            left, right = right, left ^ round_function(right, r)
        return (left << half_bits) | right
    curr = permute(i % N)
    while curr >= N:
        curr = permute(curr)
    return curr

def nested_get(d, key): # key is a list
    for k in key:
        d = d[k]
    return d

class Sweep:
    def __init__(self, config, sweepConfig, random=False, progressBar=True):
        self.config = copy.deepcopy(config) # Copy config, avoid changing the original
        self.sweep = [] # [{ "key", "list", "len" }]
        self.progressBar = progressBar
        self.random = random
        self.total = 1
        self.index = 0 # iteration index, increase in order
        self.seed = np.random.randint(2147483647)
        def parse_sweep(key, d): # key is a list
            for k, v in d.items():
                if isinstance(v, dict):
                    parse_sweep(key + [k], v)
                    continue
                if np.iterable(v) and not isinstance(v, str):
                    self.sweep.append({ "key": key + [k], "list": list(v), "len": len(v) })
                    self.total *= len(v)
                    continue
                nested_get(self.config, key)[k] = v
        try:
            parse_sweep([], sweepConfig)
            self.sweep.reverse()
            if self.total == 0:
                raise("Empty Sweep")
        except:
            raise("Invalid Sweep Config")
    def __iter__(self): # initialze all iterator
        if self.progressBar:
            self.progress = tqdm(total=self.total, mininterval=0, miniters=1, desc='utils.Sweep')
        self.index = 0
        return self
    def __next__(self):
        if self.index > 0 and self.progressBar:
            self.progress.update()
        if self.index == self.total:
            if self.progressBar:
                self.progress.close()
            raise StopIteration
        i = feistel_network(self.index, self.total, self.seed) if self.random else self.index
        for s in self.sweep:
            nested_get(self.config, s["key"][:-1])[s["key"][-1]] = s["list"][i % s["len"]]
            i = i // s["len"]
        self.index += 1
        return self.config
