from pathlib import Path

from lwe.public import Public
from lwe.secret import Secret

from time import perf_counter

def line_profile():
    Secret._decrypt_char = profile(Secret._decrypt_char)
    # Secret.decrypt = profile(Secret.decrypt)

    secret = Secret.generate(dim=1000)
    public = Public.create(secret)

    message = Path(".gitignore").read_text()


    encrypted = public.encrypt(message)
    decrypted = secret.decrypt(encrypted)

def perf_time():
    secret = Secret.generate(dim=10)
    public = Public.create(secret)

    message = Path(".gitignore").read_text()
    print(len(message))

    t1 = perf_counter()
    encrypted = public.encrypt(message)
    print(perf_counter() - t1)

    t1 = perf_counter()
    decrypted = secret.decrypt(encrypted)
    print(perf_counter() - t1)


if __name__ == "__main__":
    perf_time()
    # line_profile()
