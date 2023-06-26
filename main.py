from pathlib import Path

from lwe.public import Public
from lwe.secret import Secret

from time import perf_counter

def perf_time():
    secret = Secret.generate(dim=100)
    public = Public.create(secret)
    print(public.error_max)

    message = Path(".gitignore").read_text()
    print(len(message))

    t1 = perf_counter()
    encrypted = public.encrypt(message)
    print(perf_counter() - t1)
    print(len(encrypted) // 1000)

    t1 = perf_counter()
    decrypted = secret.decrypt(encrypted)
    print(perf_counter() - t1)
    # print(decrypted)


if __name__ == "__main__":
    perf_time()
    # line_profile()
