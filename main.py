from pathlib import Path

from line_profiler import LineProfiler

from lwe.keys.public import Public
from lwe.keys.secret import Secret


def main():
    secret = Secret.generate()
    public = Public.create(secret)

    message = Path(".gitignore").read_text() * 200
    encrypted = public.encrypt(message)

    profiler = LineProfiler()
    wrapped = profiler(secret.decrypt)
    wrapped(encrypted)
    profiler.print_stats()


if __name__ == "__main__":
    main()
