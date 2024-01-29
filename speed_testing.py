from pathlib import Path
from time import perf_counter

from lwe.keys.public import Public
from lwe.keys.secret import Secret


def main():
    secret = Secret.generate()
    public = Public.create(secret)

    message = Path(".gitignore").read_text() * 200
    size_before = len(message.encode()) / 1000000

    t1 = perf_counter()
    encrypted = public.encrypt(message)
    time_taken = perf_counter() - t1
    print("Message Size    = ", size_before, "MB")
    print("Encryption Time = ", f"{time_taken:.3f}", "s")
    print("Encryption Rate = ", f"{size_before / time_taken:.3f}", "MB/s")
    size_after = len(encrypted) / 1000000

    t1 = perf_counter()
    decrypted = secret.decrypt(encrypted)
    time_taken = perf_counter() - t1
    print("Encrypted Size  = ", size_after, "MB")
    print("Decryption Time = ", f"{time_taken:.3f}", "s")
    print("Decryption Rate = ", f"{size_before / time_taken:.3f}", "MB/s")


if __name__ == "__main__":
    main()