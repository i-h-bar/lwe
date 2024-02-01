from lwe import Secret

secret = Secret.generate()


def test_secret_bytes_conversion():
    secret_bytes = bytes(secret)

    assert isinstance(secret_bytes, bytes), "Did not convert to bytes"

    secret_from_bytes = Secret.from_bytes(secret_bytes)
    assert secret_from_bytes == secret, "Secret key created from bytes does not equal original secret key"
