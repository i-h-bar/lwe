import pickle
import random
import struct

import numpy
import numba
from numba import types, cuda

from ..utils.rng import rng
from ..utils.const import INT, MAX_CHR

from .. import Secret
from .. import lwe


class Public:
    def __new__(cls, *args, **kwargs):
        if kwargs.get("device") == "cuda":
            if cuda.is_available():
                from ._gpu.public import CUDAPublic
                return CUDAPublic(*args)
            else:
                raise cuda.CudaSupportError("cuda not available")

        else:
            return object.__new__(cls)

    def __init__(self, mod: int, public_matrix: numpy.array, dimension: tuple[int, int], device: str = "cpu"):
        self.mod = types.int32(mod)
        self.public_matrix = public_matrix
        self.dimension = dimension
        self.addition = types.int32(self.mod // MAX_CHR)
        self.error_max = self._error_max(self.mod)
        self.max_encode_vectors = types.int32(self.addition // (self.error_max * 2))

        self.device = device

    def __repr__(self):
        return f"{self.__class__.__name__}({self.mod}, Dim({self.dimension}))"

    def __eq__(self, other):
        return (
                (isinstance(other, self.__class__) or issubclass(other.__class__, Public)) and
                self.mod == other.mod and
                numpy.array_equal(self.public_matrix, other.public_matrix)
        )

    def __bytes__(self):
        return struct.pack(
            '!QII' + f"{self.dimension[1] * 4 * self.dimension[0]}s",
            self.mod,
            self.dimension[0],
            self.dimension[1],
            self.public_matrix.tobytes()
        )

    @classmethod
    def from_bytes(cls, b: bytes, device: str = "cpu"):
        mod, size, dim = struct.unpack("!QII", b[:16])
        public_matrix = numpy.frombuffer(b[16:], dtype=INT)
        return cls(mod, public_matrix, (size, dim), device=device)

    @classmethod
    def create(cls, secret_key: Secret, device: str = "cpu"):
        secret_dimension = len(secret_key.vector)
        dims = (secret_dimension * 10, secret_dimension + 1)
        error_max = cls._error_max(secret_key.mod)
        public_matrix = rng.integers(-65534, 65534, dims[0] * dims[1], dtype=INT)
        errors = rng.integers(-error_max, error_max, size=dims[0], dtype=INT)
        solve_public_matrix(public_matrix, secret_key.vector, errors, dims[0], dims[1])
        public_matrix.setflags(write=False)
        public_key = cls(secret_key.mod, public_matrix, dims, device=device)

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
            message_vector, self.public_matrix, self.mod, self.max_encode_vectors, length, self.dimension[0], self.dimension[1]
        )

        return struct.pack(
            "!I" + f"{self.dimension[1] * 4 * length}s",
            length,
            encryption_matrix.tobytes()
        )

    @staticmethod
    def _error_max(mod):
        return round((mod // MAX_CHR) * 0.1)


@numba.njit(
    types.Array(types.int32, 1, "C")(
        types.Array(types.int32, 1, "C"),
        types.Array(types.int32, 1, "C", readonly=True),
        types.int32,
        types.int32,
        types.int32,
        types.int32,
        types.int32
    ),
    parallel=True, fastmath=True
)
def encrypt_message(message_vector, public_matrix, mod, max_vectors, message_len, pub_x, dim):
    encrypted_message = numpy.zeros(message_len * dim, dtype=INT)
    end = dim - 1
    for i in numba.prange(message_len):
        start = i * dim
        for _ in numba.prange(random.randint(2, max_vectors)):  # Find new random that works in njit func
            x = random.randint(0, pub_x - 1)
            pub_start = x * dim
            encrypted_message[start: start + dim] += public_matrix[pub_start: pub_start + dim]

        encrypted_message[start + end] = (encrypted_message[start + end] + message_vector[i]) % mod

    return encrypted_message


@numba.njit(
    types.void(
        types.Array(types.int32, 1, "C"),
        types.Array(types.int32, 1, "C", readonly=True),
        types.Array(types.int32, 1, "C"),
        types.int32,
        types.int32
    ),
    parallel=True, fastmath=True
)
def solve_public_matrix(public_matrix: numpy.array, secret_key, errors: numpy.array, x, y):
    for i in numba.prange(x):
        public_matrix[i * y + y - 1] = numpy.sum(public_matrix[i * y: i * y + y - 1] * secret_key)
        public_matrix[i * y + y - 1] = public_matrix[i * y + y - 1] + errors[i]
