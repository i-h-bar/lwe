import struct

import numpy
from numba import cuda, types

from lwe.utils.const import MAX_CHR, INT


class GPUSecret:
    def __init__(self, vector: numpy.array, mod):
        self.mod = types.int32(mod)
        self.vector = vector
        self.addition = types.int32(self.mod // MAX_CHR)

        cuda.to_device(self.mod)
        cuda.to_device(self.vector)
        cuda.to_device(self.addition)

    def decrypt(self, secret):
        message_length = struct.unpack("!I", secret[:4])[0]
        message = numpy.frombuffer(secret[4:], dtype=INT).reshape((message_length, len(self.vector) + 1))