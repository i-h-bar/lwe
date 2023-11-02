from lwe.public import Public
from lwe.secret import Secret

secret = Secret.generate()
public = Public.create(secret)


def test_public_bytes_conversion():
    public_bytes = bytes(public)

    assert isinstance(public_bytes, bytes), "Did not convert to bytes"

    public_from_bytes = public.from_bytes(public_bytes)
    assert public_from_bytes == public, "public key created from bytes does not equal original public key"
