import math
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
        message = cupy.frombuffer(secret[4:], dtype=INT)
        solved_vector = cupy.zeros(message_length, dtype=INT)

        total_len = message_length * self.dimension

        threads = math.ceil(total_len / 512)
        blocks = 512

        gpu_solve[threads, blocks](message, self.gpu_vector, solved_vector, self.addition, self.mod, message_length, self.dimension + 1)

        solved_vector = cupy.asnumpy(solved_vector)
        return lwe.decode(solved_vector, solved_vector.max())


@cuda.jit(
    types.void(
        types.Array(types.int32, 1, "C", readonly=True),
        types.Array(types.int32, 1, "C", readonly=True),
        types.Array(types.int32, 1, "C"),
        types.int32,
        types.int32,
        types.int32,
        types.int32
    )
)
def gpu_solve(message, secret_key, solved_vector, addition, mod, message_length, dim):
    i = cuda.grid(1)
    if i < message_length:
        for j in range(len(secret_key)):
            solved_vector[i] += message[i * dim + j] * secret_key[j]

        solved_vector[i] = (addition * round(((message[i * dim + dim - 1] - solved_vector[i]) % mod) / addition)) / addition
