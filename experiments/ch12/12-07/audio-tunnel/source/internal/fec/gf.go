package fec

// Arithmetic in GF(256), the field of bytes, with the primitive polynomial
// x^8 + x^4 + x^3 + x^2 + 1. It is the field every practical erasure code uses:
// its elements are exactly one byte, so a symbol is a vector over it with no
// packing, and 255 non-zero elements are enough coefficients that an equation
// is degenerate about once in 256.
const primitivePolynomial = 0x11d

var (
	// exp and log turn multiplication into addition of discrete logarithms.
	// exp is doubled in length so a sum of two logarithms, which can reach
	// 508, indexes it without a conditional subtraction.
	gfExp [512]byte
	gfLog [256]byte
	// gfMul is the full multiplication table. At 64 KiB it fits in L2 and
	// turns the encoder's inner loop into one indexed load per byte, which is
	// what makes coding cheap enough to sit in the data path.
	gfMul [256][256]byte
)

func init() {
	x := 1
	for i := 0; i < 255; i++ {
		gfExp[i] = byte(x)
		gfLog[byte(x)] = byte(i)
		x <<= 1
		if x&0x100 != 0 {
			x ^= primitivePolynomial
		}
	}
	for i := 255; i < 512; i++ {
		gfExp[i] = gfExp[i-255]
	}
	for a := 1; a < 256; a++ {
		for b := 1; b < 256; b++ {
			gfMul[a][b] = gfExp[int(gfLog[a])+int(gfLog[b])]
		}
	}
}

// inv returns the multiplicative inverse. Zero has none; callers construct
// their arguments so it cannot arise, and this returns zero rather than
// panicking in a data path.
func inv(a byte) byte {
	if a == 0 {
		return 0
	}
	return gfExp[255-int(gfLog[a])]
}

// mulSliceXor accumulates coefficient times in into out, byte by byte. This is
// the whole cost of encoding and decoding, so it is written as one bounds-check
// hint and a table lookup rather than a call per byte.
func mulSliceXor(coefficient byte, in, out []byte) {
	if coefficient == 0 {
		return
	}
	if coefficient == 1 {
		for i := range out {
			out[i] ^= in[i]
		}
		return
	}
	table := &gfMul[coefficient]
	in = in[:len(out)]
	for i := range out {
		out[i] ^= table[in[i]]
	}
}
