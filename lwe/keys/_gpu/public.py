import struct
from random import randint

import cupy
import numpy
from ...utils.rng import rng
from numba import cuda, types
from numba.cuda import random

from ..public import Public
from ... import lwe
from ...utils.const import INT


class CUDAPublic(Public):
    def __init__(self, mod: int, public_matrix: numpy.array, **_):
        super().__init__(mod, public_matrix, device="cuda")
        self.gpu_public = cuda.to_device(public_matrix)

    def encrypt(self, message: str):
        message_length = len(message)
        message_vector = lwe.encode(message, self.addition, message_length)
        message_vector = cuda.to_device(message_vector)

        encryption_matrix = cupy.zeros((message_length, self.dimension), dtype=INT)

        threads = round((message_length*self.dimension)**0.66)
        blocks = round((message_length*self.dimension) / threads)
        vector_to_use = rng.integers(0, self.public_matrix.shape[0], message_length*3)
        vector_to_use = cuda.to_device(vector_to_use)

        encrypt[threads, blocks](encryption_matrix, message_vector, self.gpu_public, 3, self.mod, vector_to_use)

        encryption_matrix = cupy.asnumpy(encryption_matrix)

        return struct.pack(
            "!I" + f"{self.dimension * 4 * message_length}s",
            message_length,
            encryption_matrix.tobytes()
        )


@cuda.jit(
    types.void(
        types.Array(types.int32, 2, "C"),
        types.Array(types.int32, 1, "C"),
        types.Array(types.int32, 2, "C"),
        types.int32,
        types.int32,
        types.Array(types.int32, 1, "C"),
    )
)
def encrypt(encryption_matrix, message_vector, public_matrix, max_vectors, mod, vector_to_use):
    i = cuda.grid(1)
    if i < encryption_matrix.shape[0]:
        for k in range(max_vectors):
            public_vector = public_matrix[vector_to_use[i * k]]
            for j in range(len(public_vector)):
                encryption_matrix[i, j] += public_vector[j]

        encryption_matrix[i, -1] = (encryption_matrix[i, -1] + message_vector[i]) % mod
