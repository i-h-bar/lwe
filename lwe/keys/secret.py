import secrets
import struct

import numba
import numpy

from .. import lwe

from lwe.utils.const import INT, MAX_CHR
from numba import types


class Secret:
    def __new__(cls, *args, **kwargs):
        if kwargs.get("cuda"):
            from ._gpu.secret import GPUSecret
            kwargs.pop("cuda")
            return GPUSecret(*args)
        else:
            return object.__new__(cls)

    def __init__(self, vector: numpy.array, mod: int, cuda: bool = False):
        self.mod = mod
        self.vector = vector
        self.addition = self.mod // MAX_CHR
        self.dimension = types.int32(len(self.vector))

        if self.vector.flags.writeable:
            self.vector.setflags(write=False)

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
    def generate(cls, dim: int = 10, cuda: bool = False):
        secret = numpy.array([secrets.choice(range(-65534, 65534)) for _ in range(dim)], dtype=INT)
        return cls(secret, types.int32(secrets.choice(range(111206400, 1112064000))), cuda=cuda)

    def decrypt(self, secret):
        message_length = struct.unpack("!I", secret[:4])[0]
        message = numpy.frombuffer(secret[4:], dtype=INT).reshape((message_length, len(self.vector) + 1))
        solved_vector = solve(message, self.vector, self.addition, self.mod)

        return lwe.decode(solved_vector, solved_vector.max())


@numba.njit(
    types.Array(types.int32, 1, "C")(
        types.Array(types.int32, 2, "C", readonly=True),
        types.Array(types.int32, 1, "C", readonly=True),
        types.int32,
        types.int32
    ),
    parallel=True, fastmath=True
)
def solve(message, secret_key, addition, mod):
    solved_vector = numpy.zeros(message.shape[0], dtype=INT)
    for i in numba.prange(message.shape[0]):
        for x in numba.prange(message.shape[1] - 1):
            solved_vector[i] += message[i, x] * secret_key[x]

        solved_vector[i] = (addition * round(((message[i, -1] - solved_vector[i]) % mod) / addition)) / addition

    return solved_vector
