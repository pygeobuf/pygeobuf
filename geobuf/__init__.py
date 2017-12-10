from .encode import Encoder
from .decode import Decoder

__version__ = '2.0.0'


def encode(*args):
    return Encoder().encode(*args)


def decode(*args):
    return Decoder().decode(*args)
