from lwe import Secret
from lwe.keys._gpu.secret import CUDASecret

secret = Secret.generate()


def test_secret_bytes_conversion():
    secret_bytes = bytes(secret)

    assert isinstance(secret_bytes, bytes), "Did not convert to bytes"

    secret_from_bytes = Secret.from_bytes(secret_bytes)
    assert secret_from_bytes == secret, "Secret key created from bytes does not equal original secret key"


def test_secret_bytes_conversion_gpu():
    secret_bytes = bytes(secret)

    assert isinstance(secret_bytes, bytes), "Did not convert to bytes"

    secret_from_bytes = Secret.from_bytes(secret_bytes, device="cuda")
    assert secret_from_bytes == secret, "Secret key created from bytes does not equal original secret key"
    assert isinstance(secret_from_bytes, CUDASecret), "Did not create CUDAPublic object"


def test_gpu_pub_create_classmethod():
    sec = Secret.generate(device="cuda")
    assert isinstance(sec, CUDASecret), "Did not create CUDAPublic object"


def test_gpu_pub_init():
    sec = Secret(secret.vector, secret.mod, device="cuda")
    assert isinstance(sec, CUDASecret), "Did not create CUDAPublic object"
