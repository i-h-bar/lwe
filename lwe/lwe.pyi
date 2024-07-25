import numpy

from .utils.const import INT


def encode(message: str, addition: int, length: int) -> numpy.ndarray[INT]: ...

def decode(array: numpy.ndarray[INT], max_value: int) -> str: ...