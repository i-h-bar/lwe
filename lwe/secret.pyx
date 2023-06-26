import secrets
import struct

import numpy
cimport numpy
numpy.import_array()

from utils.const import INT, MAX_CHR

cdef int closest_multiple(int num, int target):
    return (target * round(num / target)) / target


class Secret:
    def __init__(self, vector: numpy.array, mod):
        self.mod = mod
        self.vector = vector
        self.addition = self.mod // MAX_CHR

    @classmethod
    def generate(cls, dim: int = 100):
        return cls(
            numpy.array(tuple(secrets.randbelow(65534) for _ in range(dim)), dtype=INT),
            secrets.choice(range(111206400, 1112064000))
        )

    def _decrypt_char(self, character):
        message_vector = numpy.frombuffer(character, dtype=INT)
        encoded_answer = message_vector[-1]
        encoded_vector = message_vector[:-1]
        vector_multiple = self.vector * encoded_vector
        my_answer = vector_multiple.sum() % self.mod

        answer = (encoded_answer - my_answer) % self.mod
        multiple = closest_multiple(answer, self.addition)
        return chr(multiple)

    def decrypt(self, secret: bytes):
        message_length = struct.unpack("!I", secret[:4])[0]
        vectors = struct.unpack(f"{(len(self.vector) + 1) * 8}s" * message_length, secret[4:])
        return "".join(self._decrypt_char(vector) for vector in vectors)
