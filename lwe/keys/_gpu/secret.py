import struct

import cupy
import numpy
from numba import cuda, types

from lwe.utils.const import INT
from ..secret import Secret
from ... import lwe


class CUDASecret(Secret):
    def __init__(self, vector: numpy.array, mod, **_):
        super().__init__(vector, mod, "cuda")
        self.gpu_vector = cuda.to_device(self.vector)
        self.stream = cuda.stream()

    def decrypt(self, secret: bytes) -> str:
        message_length = struct.unpack("!I", secret[:4])[0]
        message = cupy.frombuffer(secret[4:], dtype=INT).reshape((message_length, self.dimension + 1))
        solved_vector = cupy.zeros(message_length, dtype=INT)

        threads = round((message_length*self.dimension)**0.66)
        blocks = round((message_length*self.dimension) / threads)

        gpu_solve[threads, blocks](message, self.gpu_vector, solved_vector, self.addition, self.mod)

        solved_vector = cupy.asnumpy(solved_vector)
        return lwe.decode(solved_vector, solved_vector.max())


@cuda.jit(
    types.void(
        types.Array(types.int32, 2, "C", readonly=True),
        types.Array(types.int32, 1, "C", readonly=True),
        types.Array(types.int32, 1, "C"),
        types.int32,
        types.int32
    )
)
def gpu_solve(message, secret_key, solved_vector, addition, mod):
    i = cuda.grid(1)
    if i < message.shape[0]:
        for j in range(len(secret_key)):
            solved_vector[i] += message[i, j] * secret_key[j]

        solved_vector[i] = (addition * round(((message[i, -1] - solved_vector[i]) % mod) / addition)) / addition
