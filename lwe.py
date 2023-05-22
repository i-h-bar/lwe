import random
import secrets
import struct
from collections.abc import Iterable
from pathlib import Path
from time import perf_counter
from vector import Vector


class Secret:
    def __init__(self, vector, mod):
        self.mod = mod
        self.vector = Vector(*vector)
        self.addition = self.mod // 1112064

    @classmethod
    def generate(cls, dim: int = 100):
        return cls((secrets.randbelow(6553400) for _ in range(dim)), secrets.randbelow(1112064000))

    def _decrypt_char(self, char):
        message_vector = Vector.from_bytes(char, len(self.vector) + 1)
        encoded_answer = message_vector[-1]
        my_answer = sum(self.vector * Vector(*message_vector[:-1])) % self.mod

        answer = (encoded_answer - my_answer) % self.mod
        multiple = int((self.addition * round(answer / self.addition)) / self.addition)
        return chr(multiple)

    def decrypt(self, secret: bytes):
        return "".join(self._decrypt_char(bit) for bit in secret.split(b"@~:/|`"))


class Public:
    def __init__(self, mod: int, vectors: Iterable[Vector]):
        self.mod = mod
        self.vectors = tuple(vectors)
        self.dimension = len(self.vectors[0])
        self.addition = self.mod // 1112064
        self.error_max = self.error_max(self.mod)
        self.max_encode_vectors = (self.addition // self.error_max) - 1

    def __repr__(self):
        return f"{self.__class__.__name__}({self.mod}, Size({len(self.vectors)}))"

    def __bytes__(self):
        b = struct.pack('>Q', self.mod)
        b += b"@~:/|`"
        b += b"@~:/|`".join(bytes(vector) for vector in self.vectors)

        return b

    @classmethod
    def from_bytes(cls, b: bytes):
        b_mod, *b_vectors = b.split(b"@~:/|`")
        mod = struct.unpack('>Q', b_mod)[0]
        return cls(mod, (Vector.from_bytes(vector) for vector in b_vectors))

    @classmethod
    def create(cls, secret_key: Secret):
        dimension = len(secret_key.vector)
        error_max = cls.error_max(secret_key.mod)
        vectors = []

        for _ in range(dimension // 2):
            equation = Vector.random(dimension)
            answer = sum(equation * secret_key.vector) % secret_key.mod
            answer = (answer + random.randint(-error_max, error_max)) % secret_key.mod
            vectors.append(Vector(*equation, answer))

        return cls(secret_key.mod, vectors)

    def _encrypt_char(self, char):
        encoders = random.choices(self.vectors, k=random.randint(1, self.max_encode_vectors))
        encoded_vector = Vector(*(0 for _ in range(self.dimension + 1)))
        for vector in encoders:
            encoded_vector += vector

        encoded_vector[-1] = (encoded_vector[-1] + self.addition * ord(char)) % self.mod

        return bytes(encoded_vector)

    def encrypt(self, message):
        return b"@~:/|`".join(
            self._encrypt_char(bit) for bit in list(message)
        )

    @staticmethod
    def error_max(mod):
        return round((mod // 1112064) * 0.1)


if __name__ == "__main__":
    secret = Secret.generate(dim=1000)
    public = Public.create(secret)

    message = Path(".gitignore").read_text()

    encoded_message = public.encrypt(message)
    decoded_message = secret.decrypt(encoded_message)

