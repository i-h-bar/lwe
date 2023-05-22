import functools
import math
import operator
import struct
import reprlib
import secrets
import re
import random

from byte_conversion import unpack_bytes


class Vector:
    def __init__(self, *components: int):
        self._components = list(components)

    def __iter__(self):
        return iter(self._components)

    def __repr__(self):
        return f"{self.__class__.__name__}{reprlib.repr(self._components)}"

    def __str__(self):
        return str(self._components)

    def __bytes__(self):
        b = struct.pack(f"!{len(self)}Q", *self._components)
        return b

    def __abs__(self):
        return math.hypot(*self)

    def __bool__(self):
        return bool(abs(self))

    def __len__(self):
        return len(self._components)

    def __getitem__(self, item):
        return self._components[item]

    def __setitem__(self, key, value):
        self._components[key] = value

    def __hash__(self):
        return functools.reduce(operator.xor, (hash(x) for x in self), 0)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._components == other._components

    def __mul__(self, other):
        return Vector(*(x * y for x, y in zip(self, other)))

    def __add__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self).__name__!r} cannot add with an instance of {type(other).__name__!r}")

        return Vector(*(x + y for x, y in zip(self, other)))

    def __iadd__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(f"{type(self).__name__!r} cannot iadd with an instance of {type(other).__name__!r}")

        self._components = [x + y for x, y in zip(self, other)]
        return self

    @classmethod
    def from_bytes(cls, b: bytes, dim: int = None):
        try:
            return cls(*struct.unpack(f'!{dim}Q', b))
        except struct.error:
            return cls(*unpack_bytes(b))

    @classmethod
    def random(cls, dim):
        return cls(*(secrets.randbelow(1112064000) for _ in range(dim)))

    def angle(self, n):
        r = math.hypot(*self[n:])
        a = math.atan2(r, self[n - 1])

        if (n == len(self) - 1) and (self[-1] < 0):
            return math.pi * 2 - a
        else:
            return a

    def angles(self):
        return (self.angle(n) for n in range(1, len(self)))
