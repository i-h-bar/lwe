import secrets
import struct

from utils.vector import Vector


class Secret:
    def __init__(self, vector, mod):
        self.mod = mod
        self.vector = Vector(*vector)
        self.addition = self.mod // 1112064

    @classmethod
    def generate(cls, dim: int = 100):
        return cls((secrets.randbelow(6553400) for _ in range(dim)), secrets.randbelow(1112064000))

    def _decrypt_char(self, character):
        message_vector = Vector.from_bytes(character, len(self.vector) + 1)
        encoded_answer = message_vector[-1]
        my_answer = sum(self.vector * Vector(*message_vector[:-1])) % self.mod

        answer = (encoded_answer - my_answer) % self.mod
        multiple = int((self.addition * round(answer / self.addition)) / self.addition)
        return chr(multiple)

    def decrypt(self, secret: bytes):
        message_length = struct.unpack("!I", secret[:4])[0]
        vectors = struct.unpack(f"{(len(self.vector) + 1) * 8}s" * message_length, secret[4:])
        return "".join(self._decrypt_char(vector) for vector in vectors)
