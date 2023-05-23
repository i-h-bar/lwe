import random
import struct
from typing import Iterable

from lwe.secret import Secret
from utils.vector import Vector


class Public:
    def __init__(self, mod: int, vectors: Iterable[Vector]):
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
        return cls(mod, (Vector.from_bytes(vector) for vector in vectors))

    @classmethod
    def create(cls, secret_key: Secret):
        dimension = len(secret_key.vector)
        error_max = cls.error_max(secret_key.mod)
        vectors = []

        for _ in range(dimension // 2):
            equation = Vector.random(dimension)
            answer = sum(equation * secret_key.vector) % secret_key.mod
            answer = (answer + random.randint(-error_max, error_max)) % secret_key.mod
            vectors.append(Vector(*equation, answer))

        return cls(secret_key.mod, vectors)

    def _encrypt_char(self, character):
        encoders = random.choices(self.vectors, k=random.randint(1, self.max_encode_vectors))
        encoded_vector = Vector(*(0 for _ in range(self.dimension + 1)))
        for vector in encoders:
            encoded_vector += vector

        encoded_vector[-1] = (encoded_vector[-1] + self.addition * ord(character)) % self.mod

        return bytes(encoded_vector)

    def encrypt(self, message):
        return struct.pack(
            "!I" + f"{self.dimension * 8}s" * len(message),
            len(message),
            *(self._encrypt_char(bit) for bit in message)
        )

    @staticmethod
    def error_max(mod):
        return round((mod // 1112064) * 0.05)