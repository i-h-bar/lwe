import struct
from typing import Generator


def unpack_bytes(b: bytes) -> Generator[int, None, None]:
    for i in range(0, len(b), 8):
        yield struct.unpack('!Q', b[i:i + 8])[0]


