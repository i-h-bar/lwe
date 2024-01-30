import pickle
import struct

import numpy
import numba

from ..utils.rng import rng
from ..utils.const import INT, MAX_CHR

from .. import Secret


class Public:
    def __init__(self, mod: int, public_matrix: numpy.array):
        self.mod = mod
        self.public_matrix = public_matrix
        self.dimension = self.public_matrix.shape[1]
        self.addition = self.mod // MAX_CHR
        self.error_max = self._error_max(self.mod)
        self.max_encode_vectors = (self.addition // (self.error_max * 2))

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
        public_key = cls(secret_key.mod, public_matrix)

        public_key.__compile(secret_key)

        return public_key

    def to_pickle_file(self):
        with open("pub.pkl", "wb") as out_pkl:
            pickle.dump(self, out_pkl)

    @classmethod
    def from_pickle_file(cls):
        with open("pub.pkl", "rb") as in_pkl:
            return pickle.load(in_pkl)

    def encrypt(self, message):
        num_of_matrices = rng.integers(2, self.max_encode_vectors, size=len(message))
        vector_to_use = rng.integers(0, self.public_matrix.shape[0] - 1, size=len(message) * self.max_encode_vectors)
        encryption_matrix = create_encryption_matrix(
            self.dimension, self.public_matrix, len(message), num_of_matrices, vector_to_use
        )
        message_vector = numpy.array([self.addition * ord(bit) for bit in message], dtype=INT)

        encode_message(encryption_matrix, message_vector, self.mod)

        return struct.pack(
                "!I" + f"{self.dimension * 4 * len(message)}s",
                len(message),
                encryption_matrix.tobytes()
            )

    @staticmethod
    def _error_max(mod):
        return round((mod // MAX_CHR) * 0.1)

    def __compile(self, secret_key: Secret):
        encrypted = self.encrypt("xyz")
        secret_key.decrypt(encrypted)


@numba.jit(target_backend="cuda", nopython=True, parallel=True)
def solve_public_matrix(public_matrix: numpy.array, secret_key, errors: numpy.array):
    for i in numba.prange(len(public_matrix)):
        public_matrix[i, -1] = numpy.sum(public_matrix[i, :-1] * secret_key)
        public_matrix[i, -1] = public_matrix[i, -1] + errors[i]


@numba.jit(target_backend="cuda", nopython=True, parallel=True)
def encode_message(encoding_matrix, message_vector, mod):
    for i in numba.prange(len(message_vector)):
        encoding_matrix[i, -1] = (encoding_matrix[i, -1] + message_vector[i]) % mod


@numba.jit(target_backend="cuda", nopython=True, parallel=True)
def add_encoding_vector(encoding_matrix, vector, index):
    for x in numba.prange(vector.shape[0]):
        encoding_matrix[index, x] = (encoding_matrix[index, x] + vector[x])


@numba.jit(target_backend="cuda", nopython=True, parallel=True)
def create_encryption_matrix(dimension, encoding_vectors, message_length, num_of_matrices, vector_to_use):
    encoding_matrix = numpy.zeros((message_length, dimension), dtype=INT)
    for i in numba.prange(message_length):
        for x in numba.prange(num_of_matrices[i]):
            add_encoding_vector(
                encoding_matrix, encoding_vectors[vector_to_use[i * x]], i
            )

    return encoding_matrix
