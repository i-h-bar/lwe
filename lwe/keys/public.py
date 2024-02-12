import pickle
import random
import struct

import numpy
import numba
from numba import types

from ..utils.rng import rng
from ..utils.const import INT, MAX_CHR

from .. import Secret
from .. import lwe


class Public:
    def __init__(self, mod: int, public_matrix: numpy.array):
        self.mod = types.int32(mod)
        self.public_matrix = public_matrix
        self.dimension = types.int32(self.public_matrix.shape[1])
        self.addition = types.int32(self.mod // MAX_CHR)
        self.error_max = self._error_max(self.mod)
        self.max_encode_vectors = types.int32(self.addition // (self.error_max * 2))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.mod}, Dim({self.dimension}))"

    def __eq__(self, other):
        return (
                isinstance(other, self.__class__) and
                self.mod == other.mod and
                numpy.array_equal(self.public_matrix, other.public_matrix)
        )

    def __bytes__(self):
        return struct.pack(
            '!QII' + f"{self.dimension * 4 * len(self.public_matrix)}s",
            self.mod,
            len(self.public_matrix),
            self.dimension,
            self.public_matrix.tobytes()
        )

    @classmethod
    def from_bytes(cls, b: bytes):
        mod, size, dim = struct.unpack("!QII", b[:16])
        public_matrix = numpy.frombuffer(b[16:], dtype=INT).reshape((size, dim))
        return cls(mod, public_matrix)

    @classmethod
    def create(cls, secret_key: Secret):
        dimension = len(secret_key.vector)
        error_max = cls._error_max(secret_key.mod)
        public_matrix = rng.integers(-65534, 65534, (dimension * 10, dimension + 1), dtype=INT)
        errors = rng.integers(-error_max, error_max, size=len(public_matrix), dtype=INT)
        solve_public_matrix(public_matrix, secret_key.vector, errors)
        public_matrix.setflags(write=False)
        public_key = cls(secret_key.mod, public_matrix)

        return public_key

    def to_pickle_file(self):
        with open("pub.pkl", "wb") as out_pkl:
            pickle.dump(self, out_pkl)

    @classmethod
    def from_pickle_file(cls):
        with open("pub.pkl", "rb") as in_pkl:
            return pickle.load(in_pkl)

    def encrypt(self, message):
        length = len(message)
        message_vector = lwe.encode(message, self.addition, length)

        encryption_matrix = encrypt_message(
            message_vector, self.public_matrix, self.mod, self.max_encode_vectors, length, self.dimension
        )

        return struct.pack(
            "!I" + f"{self.dimension * 4 * length}s",
            length,
            encryption_matrix.tobytes()
        )

    @staticmethod
    def _error_max(mod):
        return round((mod // MAX_CHR) * 0.1)


@numba.njit(
    types.Array(types.int32, 2, "C")(
        types.Array(types.int32, 1, "C"),
        types.Array(types.int32, 2, "C", readonly=True),
        types.int32,
        types.int32,
        types.int32,
        types.int32,
    ),
    parallel=True, fastmath=True
)
def encrypt_message(message_vector, public_matrix, mod, max_vectors, message_len, dim):
    encrypted_message = numpy.zeros((message_len, dim), dtype=INT)
    for i in numba.prange(message_len):
        for _ in numba.prange(random.randint(2, max_vectors)):  # Find new random that works in njit func
            encrypted_message[i] += public_matrix[random.randint(0, public_matrix.shape[0] - 1)]

        encrypted_message[i, -1] = (encrypted_message[i, -1] + message_vector[i]) % mod

    return encrypted_message


@numba.njit(
    types.void(
        types.Array(types.int32, 2, "C"),
        types.Array(types.int32, 1, "C", readonly=True),
        types.Array(types.int32, 1, "C")
    ),
    parallel=True, fastmath=True
)
def solve_public_matrix(public_matrix: numpy.array, secret_key, errors: numpy.array):
    for i in numba.prange(len(public_matrix)):
        public_matrix[i, -1] = numpy.sum(public_matrix[i, :-1] * secret_key)
        public_matrix[i, -1] = public_matrix[i, -1] + errors[i]
