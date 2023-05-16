import random
import re
import secrets
from collections.abc import Iterable
from time import perf_counter

from vector import Vector


class Secret:
    def __init__(self, vector, mod):
        self.mod = mod
        self.target = self.mod // 2
        self.vector = Vector(*vector)

    @classmethod
    def generate(cls, dim: int = 100):
        return cls((secrets.randbelow(65534) for _ in range(dim)), random.randint(500, 1000))  # Temp use of random

    def _decode_bit(self, bit):
        message_vector = Vector.from_bytes(bit)
        encoded_answer = message_vector[-1]
        my_answer = sum(self.vector * Vector(*message_vector[:-1])) % self.mod

        answer = (encoded_answer - my_answer) % self.mod

        return str(int(abs(self.target - answer) < abs(answer) and abs(self.target - answer) < abs(self.mod - answer)))

    def decode(self, secret: bytes):
        bits = "".join(self._decode_bit(bit) for bit in secret.split(b"--"))
        string_blocks = (bits[i:i + 8] for i in range(0, len(bits), 8))
        return ''.join(chr(int(char, 2)) for char in string_blocks)


class Public:
    def __init__(self, mod: int, vectors: Iterable[Vector]):
        self.mod = mod
        self.vectors = tuple(vectors)
        self.dimension = len(self.vectors[0]) - 1

        self.addition = self.mod // 2

    def __repr__(self):
        return f"{self.__class__.__name__}({self.mod}, Size({len(self.vectors)}))"

    def __bytes__(self):
        b_vectors = b",,".join((bytes(vector) for vector in self.vectors))
        return b"{{%i}}{{%b}}" % (self.mod, b_vectors)

    @classmethod
    def from_bytes(cls, octets: bytes):
        b_mod, b_vectors = re.findall(rb'(?s){{(.*?)}}', octets)
        mod = int(b_mod)
        vectors = (Vector.from_bytes(b_vector) for b_vector in b_vectors.split(b",,"))

        return cls(mod, vectors)

    @classmethod
    def create(cls, secret_key: Secret):
        dimension = len(secret_key.vector)

        vectors = []

        for _ in range(dimension // 2):
            equation = Vector.random(dimension)
            answer = (sum(equation * secret_key.vector) + random.randint(-5, 5)) % secret_key.mod  # Temp use of random
            vectors.append(Vector(*equation, answer))

        return cls(secret_key.mod, vectors)

    def _encode_bit(self, bit):
        encoders = random.choices(self.vectors, k=random.randint(1, round(0.2 * self.dimension)))  # Temp use of random

        encoded_vector = Vector(*(0 for _ in range(self.dimension + 1)))

        for vector in encoders:
            encoded_vector += vector

        encoded_vector[-1] = (encoded_vector[-1] + self.addition * int(bit)) % self.mod

        return bytes(encoded_vector)

    def encode(self, message):
        bits = "".join(bin(ord(x))[2:].zfill(8) for x in message)
        return b"--".join(
            self._encode_bit(bit) for bit in list(bits)
        )


if __name__ == "__main__":
    secret = Secret.generate(dim=20)
    public = Public.create(secret)

    t1_start = perf_counter()
    encoded_message = public.encode("This is a super secret message that needs to be hidden.")
    t1_stop = perf_counter()

    print(t1_stop - t1_start)

    t1_start = perf_counter()
    decoded_message = secret.decode(encoded_message)
    t1_stop = perf_counter()

    print(t1_stop - t1_start)

    print(decoded_message)
