from lwe import Public
from lwe import Secret
from lwe.keys._gpu.public import CUDAPublic

secret = Secret.generate()
public = Public.create(secret)


def test_public_bytes_conversion():
    public_bytes = bytes(public)

    assert isinstance(public_bytes, bytes), "Did not convert to bytes"

    public_from_bytes = public.from_bytes(public_bytes)
    assert public_from_bytes == public, "public key created from bytes does not equal original public key"


def test_public_bytes_conversion_gpu():
    public_bytes = bytes(public)

    assert isinstance(public_bytes, bytes), "Did not convert to bytes"

    public_from_bytes = public.from_bytes(public_bytes, device="cuda")
    assert public_from_bytes == public, "public key created from bytes does not equal original public key"
    assert isinstance(public_from_bytes, CUDAPublic), "Did not create CUDAPublic object"


def test_gpu_pub_create_classmethod():
    pub = Public.create(secret, device="cuda")
    assert isinstance(pub, CUDAPublic), "Did not create CUDAPublic object"


def test_gpu_pub_init():
    pub = Public(public.mod, public.public_matrix, device="cuda")
    assert isinstance(pub, CUDAPublic), "Did not create CUDAPublic object"
