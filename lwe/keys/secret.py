import secrets
import struct

import numba
import numpy

from .. import lwe

from lwe.utils.const import INT, MAX_CHR
from numba import types, cuda


class Secret:
    def __new__(cls, *args, **kwargs):
        if kwargs.get("device") == "cuda":
            if cuda.is_available():
                from ._gpu.secret import CUDASecret
                return CUDASecret(*args)
            else:
                raise cuda.CudaSupportError("cuda not available")

        else:
            return object.__new__(cls)

    def __init__(self, vector: numpy.array, mod: int, device: str = "cpu"):
        self.mod = mod
        self.vector = vector
        self.addition = self.mod // MAX_CHR
        self.dimension = types.int32(len(self.vector))
        self.device = device

        if self.vector.flags.writeable:
            self.vector.setflags(write=False)

    def __eq__(self, other):
        return (
                (isinstance(other, self.__class__) or issubclass(other.__class__, Secret)) and
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
    def from_bytes(cls, b: bytes, device: str = "cpu"):
        mod = struct.unpack("!Q", b[:8])[0]
        vector = numpy.frombuffer(b[8:], dtype=INT)
        return cls(vector, mod, device=device)

    @classmethod
    def generate(cls, dim: int = 10, device: str = "cpu"):
        secret = numpy.array([secrets.choice(range(-65534, 65534)) for _ in range(dim)], dtype=INT)
        return cls(secret, types.int32(secrets.choice(range(111206400, 1112064000))), device=device)

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
