import struct
import secrets
from typing import Iterable

import numpy
cimport numpy

from utils.numpy_const import INT

numpy.import_array()

from lwe.secret import Secret


class Public:
    def __init__(self, mod: int, vectors: Iterable[numpy.array]):
        self.mod = mod
        self.vectors = tuple(vectors)
        self.dimension = len(self.vectors[0])
        self.addition = self.mod // 1112064
        self.error_max = self.error_max(self.mod)
        self.max_encode_vectors = (self.addition // self.error_max) - 2

    def __repr__(self):
        return f"{self.__class__.__name__}({self.mod}, Size({len(self.vectors)}))"

    def __bytes__(self):
        return struct.pack(
            '!QII' + f"{self.dimension*8}s"*len(self.vectors),
            self.mod,
            len(self.vectors),
            self.dimension,
            *(bytes(vector) for vector in self.vectors)
        )

    @classmethod
    def from_bytes(cls, b: bytes):
        mod, size, dim = struct.unpack("!QII", b[:16])
        vectors = struct.unpack(f"{dim*8}s"*size, b[16:])
        return cls(mod, (numpy.frombuffer(b, dtype=INT) for vector in vectors))

    @classmethod
    def create(cls, secret_key: Secret):
        dimension = len(secret_key.vector)
        error_max = cls.error_max(secret_key.mod)
        vectors = []

        for _ in range(dimension * 10):
            equation = numpy.array(tuple(secrets.randbelow(1112064000) for _ in range(dimension)), dtype=numpy.int64)
            answer = sum(equation * secret_key.vector) % secret_key.mod
            answer = (answer + secrets.choice(range(-error_max, error_max))) % secret_key.mod
            vectors.append(numpy.array([*equation, answer], dtype=INT))

        return cls(secret_key.mod, vectors)

    def _encrypt_char(self, character):
        encoded_vector = numpy.zeros(self.dimension, dtype=INT)
        for _ in range(secrets.choice(range(1, self.max_encode_vectors))):
            encoded_vector += self.vectors[secrets.randbelow(len(self.vectors))]

        encoded_vector[-1] = (encoded_vector[-1] + self.addition * ord(character)) % self.mod

        return encoded_vector.tobytes()

    def encrypt(self, message):
        return struct.pack(
            "!I" + f"{self.dimension * 8}s" * len(message),
            len(message),
            *(self._encrypt_char(bit) for bit in message)
        )

    @staticmethod
    def error_max(mod):
        return round((mod // 1112064) * 0.05)