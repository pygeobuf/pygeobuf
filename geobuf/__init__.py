from encode import Encoder
from decode import Decoder

def encode(*args): return Encoder(*args).encode()
def decode(*args): return Decoder(*args).decode()
