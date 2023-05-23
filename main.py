from pathlib import Path

from lwe.public import Public
from lwe.secret import Secret
from time import perf_counter


secret = Secret.generate(dim=1000)
public = Public.create(secret)

message = Path(".gitignore").read_text()

t1 = perf_counter()
encrypted = public.encrypt(message)
print(perf_counter() - t1)

t1 = perf_counter()
decrypted = secret.decrypt(encrypted)
print(perf_counter() - t1)
print(decrypted == message)
