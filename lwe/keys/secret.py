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
        solved_vector = solve(secret[4:], message_length, self.vector, self.addition, self.mod)

        return lwe.decode(solved_vector, solved_vector.max())


@numba.jit(target_backend="cuda", nopython=True, parallel=True)
def solve(secret, message_length, secret_key, addition, mod):
    message = numpy.frombuffer(secret, dtype=INT).reshape((message_length, len(secret_key) + 1))
    solved_vector = numpy.zeros(message.shape[0], dtype=INT)
    for i in numba.prange(message.shape[0]):
        for x in numba.prange(message.shape[1] - 1):
            solved_vector[i] += message[i, x] * secret_key[x]

        solved_vector[i] = (addition * round(((message[i, -1] - solved_vector[i]) % mod) / addition)) / addition

    return solved_vector
