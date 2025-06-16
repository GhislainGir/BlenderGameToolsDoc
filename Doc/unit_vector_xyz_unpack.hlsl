const uint mask11b = 1 << 10;
const uint mask10b = 1 << 9;
const float invmask11b = 1 / float(mask11b);
const float invmask10b = 1 / float(mask10b);
const float multiplier = 2.0 * inMultiplier;

uint packed_int = asuint(inVectorFloat);

// XXXXXXXXXXXYYYYYYYYYYYZZZZZZZZZZ
// 11-bit X, 11-bit Y, 10-bit Z

// X
// shift 11 most left bits 21 bits to the right
uint packed_x = packed_int >> 21;
//   XXXXXXXXXXXYYYYYYYYYYYZZZZZZZZZZ
// > 000000000000000000000XXXXXXXXXXX

// bring back to [0:1] range and remap
x = (((float)packed_x * invmask11b) - 0.5) * multiplier;

// Y
// shift 22 most left bits 10 bits to the right
uint packed_y = packed_int >> 10;
//   XXXXXXXXXXXYYYYYYYYYYYZZZZZZZZZZ
// > 0000000000XXXXXXXXXXXYYYYYYYYYYY

// mask 
packed_y = packed_y & (1 << 11) - 1;
//   0000000000XXXXXXXXXXXYYYYYYYYYYY
// & 00000000000000000000011111111111
// = 000000000000000000000YYYYYYYYYYY

// bring back to [0:1] range and remap
y = ((float(packed_y) * invmask11b) - 0.5) * multiplier;

// Z
// mask 
uint packed_z = packed_int & (mask11b - 1);
//   XXXXXXXXXXXYYYYYYYYYYYZZZZZZZZZZ
// & 00000000000000000000001111111111
// = 0000000000000000000000ZZZZZZZZZZ

// bring back to [0:1] range and remap
z = ((float(packed_z) * invmask10b) - 0.5) * multiplier;

return 1.0;