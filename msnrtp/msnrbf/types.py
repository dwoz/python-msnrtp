'''
Primitive type definitions. Much of the info for these data type definitions
comes from MS-DTYP. This module aims to impliment those types used by the .NET
remoting protocole MS-NRTP and the binary message format MS-NRBF.

MS-NRBF - 2.1.1 Common Data Types
'''
import binascii
import struct
import logging
from enum import primitive_type


logger = logging.getLogger(__name__)


def setbit(n, offset):
    mask = 1 << offset
    return (n | mask)


def clearbit(n, offset):
    mask = ~(1 << offset)
    return (n & mask)


def bits(b, high_bit_first=False):
    if b > 255:
        raise Exception("Single byte has max 255")
    l = []
    if high_bit_first:
        x = reversed(xrange(8))
    else:
        x = xrange(8)
    for i in x:
        l.append((b >> i) & 1)
    return l


def frombits(l, high_bit_first=False):
    if len(l) > 8:
        raise Exception("Only eight bits in a single byte")
    x = xrange(8)
    n = 0
    if high_bit_first:
        l = list(reversed(l))
    for i in x:
        if l[i]:
            n = setbit(n, i)
        else:
            n = clearbit(n, i)
    return n


def pack_length(length):
    length_bits = bin(length)[2:]
    length_words = []
    while length_bits:
        length_words.append(length_bits[-7:])
        length_bits = length_bits[:-7]
    encoded_words = []
    length_words = list(reversed(length_words))
    while length_words:
        w = length_words[-1].zfill(7)
        length_words = length_words[:-1]
        if length_words:
            last_bit = '1'
        else:
            last_bit = '0'
        encoded_words.append([int(a) for a in (last_bit + w)])
    return ''.join([chr(frombits(b, high_bit_first=True)) for b in encoded_words])


def unpack_length(byts):
    idx = 0
    length_bits = []
    origbits = bin(int(binascii.hexlify(byts), 16))[2:].zfill(16)
    while True:
        b = ord(byts[idx])
        encoded_bits = bits(b, high_bit_first=True)
        length_bits.append(encoded_bits[1:])
        idx += 1
        if encoded_bits[0] == 0:
            break
    length_bits = reversed(length_bits)
    lbits = []
    for a in length_bits:
        for b in a:
            lbits.append(b)
    length = int(''.join((str(_) for _ in lbits)), 2)
    return length, idx


class PrimitiveType(object):
    enum = None

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<PrimitiveType({})>'.format(self.value)

    def __eq__(self, other):
        if isinstance(other, PrimitiveType):
            return self.enum == other.enum and self.value == other.value
        return False

    def _to_py(self):
        return self.value

    def _from_py(self, value):
        self.value = value


class LengthPrefixedString(PrimitiveType):
    enum = primitive_type.STRING

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<LengthPrefixedString({}) at {}>'.format(
            self.value, hex(id(self))
        )

    @property
    def length(self):
        return len(self.value.encode('utf-8'))

    @property
    def encoded_length(self):
        return pack_length(self.length)

    def pack(self):
        return self.encoded_length + self.value.encode('utf-8')

    @classmethod
    def unpack(cls, byts):
        length, start = unpack_length(byts)
        a = byts[start:]
        return cls(a[:length].decode('utf-8'))


class Boolean(PrimitiveType):
    enum = primitive_type.BOOLEAN

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<Boolean({})>'.format(self.value)

    def pack(self):
        return struct.pack('<B', self.value)

    @classmethod
    def unpack(cls, byts):
        i, = struct.unpack('<B', byts[:1])
        if i != 0 and i != 1:
            raise Exception
        return cls(i)


class Single(PrimitiveType):
    enum = primitive_type.SINGLE

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<{}({}) at {}>'.format(
            'Single', self.value, hex(id(self))
        )

    def pack(self):
        return struct.pack('<f', self.value)

    @classmethod
    def unpack(cls, byts):
        return cls(*struct.unpack('<f', byts[:4]))


class Int32(PrimitiveType):
    enum = primitive_type.INT32

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<{}({}) at {}>'.format(
            'Int32', self.value, hex(id(self))
        )

    def pack(self):
        return struct.pack('<i', self.value)

    @classmethod
    def unpack(cls, byts):
        return cls(*struct.unpack('<i', byts[:4]))


class Int64(PrimitiveType):
    enum = primitive_type.INT64

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<{}({}) at {}>'.format(
            'Int64', self.value, hex(id(self))
        )

    def pack(self):
        return struct.pack('<q', self.value)

    @classmethod
    def unpack(cls, byts):
        return cls(*struct.unpack('<q', byts[:8]))


class UInt64(PrimitiveType):
    enum = primitive_type.UINT64

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<{}({}) at {}>'.format(
            'UInt64', self.value, hex(id(self))
        )

    def pack(self):
        return struct.pack('<Q', self.value)

    @classmethod
    def unpack(cls, byts):
        return cls(*struct.unpack('<Q', byts[:8]))


class Datetime(PrimitiveType):
    enum = primitive_type.DATETIME

    def __init__(self, ticks, tzinfo):
        self.ticks = ticks
        self.tzinfo = tzinfo

    def __repr__(self):
        return '<{}({}, {}) at {}>'.format(
            'Datetime', self.ticks, self.tzinfo, hex(id(self))
        )

    def pack(self):
        upper = bin(self.ticks)[2:].zfill(62)
        lower = bin(self.tzinfo)[2:].zfill(2)
        return binascii.unhexlify('{:0>16x}'.format(int(upper + lower, 2)))

    @classmethod
    def unpack(cls, byts):
        bindata = bin(int(binascii.hexlify(byts[:8]), 16))[2:].zfill(64)
        ticks = int(bindata[:62], 2)
        tzinfo = int(bindata[62:], 2)
        return cls(ticks, tzinfo)


_enum = {
    Boolean.enum: Boolean,
    Single.enum: Single,
    Int32.enum: Int32,
    Int64.enum: Int64,
    UInt64.enum: UInt64,
    Datetime.enum: Datetime,
    LengthPrefixedString.enum: LengthPrefixedString,
}


def pack_primitive_type(kind, value):
    return _enum[kind](value).pack()


def unpack_primitive_type(kind, byts):
    if isinstance(kind, primitive_type.PrimitiveTypeEnum):
        kind = kind.enum
    return _enum[kind].unpack(byts)


def consume_primitive_type(kind, byts):
    p = unpack_primitive_type(kind, byts)
    pdata = p.pack()
    if pdata != byts[:len(pdata)]:
        raise Exception("Bytes do not match")
    return p, byts[len(pdata):]
