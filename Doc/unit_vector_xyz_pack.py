import math
from ctypes import POINTER, pointer, c_int, cast, c_float

def get_packed_11_10_10_xyz(xyz, multiplier):
    """ """

    if multiplier <= 0:
        return (False, "Invalid multiplier", 0.0)

    bitstring_a = str(bin(math.floor((((xyz.x / multiplier) + 1) * 0.5) * (1<<10))))
    bitstring_a = bitstring_a[2:] # get rid of 0b
    bitstring_a = bitstring_a.zfill(11) # ensure it's 11 char long

    bitstring_b = str(bin(math.floor((((xyz.y / multiplier) + 1) * 0.5) * (1<<10))))
    bitstring_b = bitstring_b[2:] # get rid of 0b
    bitstring_b = bitstring_b.zfill(11) # ensure it's 11 char long

    bitstring_c = str(bin(math.floor((((xyz.z / multiplier) + 1) * 0.5) * (1<<9))))
    bitstring_c = bitstring_c[2:] # get rid of 0b
    bitstring_c = bitstring_c.zfill(10) # ensure it's 10 char long

    bits = int((bitstring_a + bitstring_b + bitstring_c), 2)

    cp = pointer(c_int(bits))
    fp = cast(cp, POINTER(c_float))
    return (True, "", fp.contents.value)