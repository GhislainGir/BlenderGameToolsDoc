uint packed_int = asuint(packed_float);

// SII AAAAAAAAAAAAAAA BBBBBBBBBBBBBB
// S = sign, II = index,  A = 15-bit a component, B = 14-bit b component

// SIGN

// shift most left bit 31 bits to the right
uint packed_sign = packed_int >> 31;
//   SIIAAAAAAAAAAAAAAABBBBBBBBBBBBBB
// > 0000000000000000000000000000000S

// MAX COMPONENT INDEX
// shift three most left bits 29 bits to the right
uint packed_max_index = packed_int >> 29;
//   SIIAAAAAAAAAAAAAAABBBBBBBBBBBBBB
// > 00000000000000000000000000000SII
// set all bits after the 2nd bit to 0
packed_max_index &= (1 << 2) - 1; // 3, or 011 in binary
//   00000000000000000000000000000SII
// & 00000000000000000000000000000011
// = 000000000000000000000000000000II

// A
// shift 18 most left bits 14 bits to the right
uint packed_a = packed_int >> 14;
//   SIIAAAAAAAAAAAAAAABBBBBBBBBBBBBB
// > 00000000000000SIIAAAAAAAAAAAAAAA
// set all bits after the 14th bit to 0
packed_a &= (1 << 15) - 1;
//   00000000000000SIIAAAAAAAAAAAAAAA
// & 00000000000000000111111111111111
// = 00000000000000000AAAAAAAAAAAAAAA
// interpret bits as integer and remap to float
float a = (((float)packed_a / (1 << 14)) - 0.5) * 2.0 * multiplier;

// B
// set all bits after the 14th bit to 0
uint packed_b = packed_int & (1 << 14) - 1;
//   SIIAAAAAAAAAAAAAAABBBBBBBBBBBBBB
// & 00000000000000000011111111111111
// = 000000000000000000BBBBBBBBBBBBBB
// interpret bits as integer and remap to float
float b = ((float(packed_b) / (1 << 13)) - 0.5) * 2.0 * multiplier;

// C
// reconstruct discarded component, known to be the max value
float c = multiplier * ((float(packed_sign) * 2) - 1);
//float c = multiplier;

// REORDER ABC
if (packed_max_index == 0) // x, a = y, b = z
{
    x = c;
    y = a;
    z = b;
}
else if (packed_max_index == 1) // y, a = x, b = z
{
    x = a;
    y = c;
    z = b;
}
else // z, a = x, b = y
{
    x = a;
    y = b;
    z = c;
}

return 1.0;