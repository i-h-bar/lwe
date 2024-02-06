import secrets
import struct

import numba
import numpy
from .. import lwe

from lwe.utils.const import INT, MAX_CHR


def closest_multiple(num: int, target: int):
    return (target * round(num / target)) / target


class Secret:
    def __init__(self, vector: numpy.array, mod):
        self.mod = mod
        self.vector = vector
        self.addition = self.mod // MAX_CHR

    def __eq__(self, other):
        return (
                isinstance(other, self.__class__) and
                self.mod == other.mod and
                numpy.array_equal(self.vector, other.vector)
        )

    def __bytes__(self):
        return struct.pack(
            "!Q" + f"{len(self.vector) * 4}s",
            self.mod,
            self.vector.tobytes()
        )

    @classmethod
    def from_bytes(cls, b: bytes):
        mod = struct.unpack("!Q", b[:8])[0]
        vector = numpy.frombuffer(b[8:], dtype=INT)
        return cls(vector, mod)

    @classmethod
    def generate(cls, dim: int = 10):
        return cls(
            numpy.array([secrets.choice(range(-65534, 65534)) for _ in range(dim)], dtype=INT),
            secrets.choice(range(111206400, 1112064000))
        )

    def decrypt(self, secret):
        message_length = struct.unpack("!I", secret[:4])[0]
        message = numpy.frombuffer(secret[4:], dtype=INT).reshape((message_length, len(self.vector) + 1))

        solved_matrix = numpy.zeros(message.shape, dtype=INT)
        encodings = message[:, :-1]
        encrypted_message = message[:, -1]

        solve_encodings(encodings, self.vector, solved_matrix)
        solved_vector = solved_matrix[:, -1]
        extract_char(solved_vector, encrypted_message, self.mod, self.addition)

        return lwe.decode(solved_vector, solved_vector.max())


@numba.jit(target_backend="cuda", nopython=True)
def solve_encodings(encodings, secret_key, solved_matrix):
    for i in numba.prange(encodings.shape[0]):
        for x in numba.prange(encodings.shape[1]):
            solved_matrix[i, x] = (encodings[i, x] * secret_key[x])

    for i in numba.prange(solved_matrix.shape[0]):
        solved_matrix[i, -1] = numpy.sum(solved_matrix[i, :-1])


@numba.jit(target_backend="cuda", nopython=True)
def extract_char(solved_vector, encrypted_message, mod, addition):
    for i in numba.prange(solved_vector.shape[0]):
        solved_vector[i] = (addition * round(((encrypted_message[i] - solved_vector[i]) % mod) / addition)) / addition
