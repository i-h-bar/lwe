from lwe import Public
from lwe import Secret
from lwe.keys._gpu.public import CUDAPublic
from lwe.keys._gpu.secret import CUDASecret

secret = Secret.generate()
public = Public.create(secret)
gpu_secret = CUDASecret(secret.vector, secret.mod)
gpu_public = CUDAPublic(public.mod, public.public_matrix)

def test_encryption():
    message = "Hello World"

    for _ in range(10):
        encrypted = public.encrypt(message)

        assert isinstance(encrypted, bytes), "Encrypted type is not bytes"
        assert encrypted != message, "encrypted message is the same as the message"

        decrypted = secret.decrypt(encrypted)

        assert isinstance(decrypted, str), "Decrypted message is not a string"
        assert decrypted == message, "Message is not the same"


def test_utf8_char_encryption():
    message = "「こんにちは世界」"

    for _ in range(10):
        encrypted = public.encrypt(message)

        assert isinstance(encrypted, bytes), "Encrypted type is not bytes"
        assert encrypted != message, "encrypted message is the same as the message"

        decrypted = secret.decrypt(encrypted)

        assert isinstance(decrypted, str), "Decrypted message is not a string"
        assert decrypted == message, "Message is not the same"


def test_gpu_enc_cpu_dec():
    message = "Hello World" * 100000

    encrypted = gpu_public.encrypt(message)

    assert isinstance(encrypted, bytes), "Encrypted type is not bytes"
    assert encrypted != message, "encrypted message is the same as the message"

    decrypted = secret.decrypt(encrypted)

    assert isinstance(decrypted, str), "Decrypted message is not a string"
    assert decrypted == message, "Message is not the same"


def test_cpu_enc_gpu_dec():
    message = "Hello World" * 100000

    encrypted = public.encrypt(message)

    assert isinstance(encrypted, bytes), "Encrypted type is not bytes"
    assert encrypted != message, "encrypted message is the same as the message"

    decrypted = gpu_secret.decrypt(encrypted)

    assert isinstance(decrypted, str), "Decrypted message is not a string"
    assert decrypted == message, "Message is not the same"


def test_gpu_decryption():
    message = "Hello World" * 100000

    encrypted = gpu_public.encrypt(message)

    assert isinstance(encrypted, bytes), "Encrypted type is not bytes"
    assert encrypted != message, "encrypted message is the same as the message"

    decrypted = gpu_secret.decrypt(encrypted)

    assert isinstance(decrypted, str), "Decrypted message is not a string"
    assert decrypted == message, "Message is not the same"



def test_decryption_different_key():
    message = "Hello World"
    secret_2 = Secret.generate()

    encrypted = public.encrypt(message)

    assert isinstance(encrypted, bytes), "Encrypted type is not bytes"
    assert encrypted != message, "encrypted message is the same as the message"

    decrypted = secret_2.decrypt(encrypted)

    assert isinstance(decrypted, str), "Decrypted message is not a string"
    assert decrypted != message, "Message is the same"