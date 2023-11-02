from pathlib import Path
from time import perf_counter

from lwe.public import Public
from lwe.secret import Secret


def main():
    secret = Secret.generate()
    public = Public.create(secret)

    message = Path(".gitignore").read_text() * 200
    print(len(message))

    t1 = perf_counter()
    encrypted = public.encrypt(message)
    print(perf_counter() - t1)
    print(len(encrypted) // 1000, "KB")

    t1 = perf_counter()
    decrypted = secret.decrypt(encrypted)
    print(perf_counter() - t1)


if __name__ == "__main__":
    main()
