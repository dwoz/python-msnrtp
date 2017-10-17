'''
Structures used by the .NET remoting protocol

MS-NRBF 2.3.1 Common Structures
'''
from types import (
    LengthPrefixedString, consume_primitive_type, unpack_primitive_type,
    pack_primitive_type
)
from enum import *
import struct


class ClassTypeInfo(object):
    '''2.1.1.8'''

    def __init__(self, name, library_id):
        self.name = name
        self.library_id = library_id

    def __repr__(self):
        return '<ClassTypeInfo({}, {}) at {}>'.format(
            self.name, self.library_id, hex(id(self))
        )

    def pack(self):
        return LengthPrefixedString(self.name).pack() + struct.pack('<i', self.library_id)

    @classmethod
    def unpack(cls, byts):
        lps = LengthPrefixedString.unpack(byts)
        ibyts = byts[len(lps.pack()):]
        library_id, = struct.unpack('<i', ibyts[:4])
        return cls(lps.value, library_id)


class ClassInfo(object):
    '''
    MS-NRBF 2.3.1.1 ClassInfo
    '''

    def __init__(self, object_id, name, member_count, member_names):
        self.object_id = object_id
        self.name = name
        self.member_count = member_count
        self.member_names = member_names

    def __repr__(self):
        return (
            '<ClassInfo(object_id={}, name={}, member_count={}, member_names={})'
            ' at {}>').format(
                self.object_id, self.name, self.member_count, self.member_names,
                hex(id(self))
            )

    def __eq__(self, other):
        return (
            self.object_id == other.object_id and
            self.name == other.name and
            self.member_count == other.member_count and
            self.member_names == other.member_names
        )

    def pack(self):
        data = struct.pack('<i', self.object_id)
        data += LengthPrefixedString(self.name).pack()
        data += struct.pack('<i', self.member_count)
        for name in self.member_names:
            data += LengthPrefixedString(name).pack()
        return data

    @classmethod
    def unpack(cls, byts):
        unpacked = 0
        object_id, = struct.unpack('<i', byts[:4])
        member_byts = byts[4:]
        unpacked += 4
        name = LengthPrefixedString.unpack(member_byts)
        member_byts = member_byts[len(name.pack()):]
        unpacked += len(name.pack())
        member_count, = struct.unpack('<i', member_byts[:4])
        member_byts = member_byts[4:]
        unpacked += 4
        member_names = []
        for _ in xrange(member_count):
            lpstr = LengthPrefixedString.unpack(member_byts)
            member_byts = member_byts[len(lpstr.pack()):]
            unpacked += len(lpstr.pack())
            member_names.append(lpstr.value)
        return cls(
            object_id,
            name.value,
            member_count,
            member_names,
        )


class MemberTypeInfo(object):
    '''
    '''

    def __init__(self, member_info):
        self.member_info = member_info

    def __repr__(self):
        return '<MemberTypeInfo({}) at {}>'.format(self.member_info, hex(id(self)))

    def pack(self):
        data = ''
        for typ, additional_info in self.member_info:
            data += typ.pack()
        for typ, additional_info in self.member_info:
            if additional_info:
                data += additional_info.pack()
        return data

    def __eq__(self, other):
        return self.member_info == other.member_info

    def __iter__(self):
        return iter(self.member_info)

    @classmethod
    def unpack(cls, byts, member_count=1):
        member_types = []
        while len(member_types) < member_count:
            member_types.append(bt.BinaryTypeEnum.unpack(byts[0]))
            byts = byts[1:]
        member_info = []
        for typ in member_types:
            o = cls.unpack_additional_info(typ, byts)
            member_info.append((typ, o))
            if o:
                byts = byts[len(o.pack()):]
        return cls(member_info)

    @staticmethod
    def unpack_additional_info(typ, byts):
        if typ.n == 0:
            return pt.PrimitiveTypeEnum.unpack(byts[0])
        elif typ.n == 3:
            return LengthPrefixedString.unpack(byts)
        elif typ.n == 4:
            return ClassTypeInfo.unpack(byts)
        elif typ.n == 7:
            return pt.PrimitiveTypeEnum.unpack(byts[0])
        else:
            return None


class ArrayInfo(object):
    '''
    ArrayInfo is a structure that contains the object_id and length (number of
    elements in array)
    '''

    def __init__(self, object_id, length):
        self.object_id = object_id
        self.length = length

    def __repr__(self):
        return '<ArrayInfo(object_id={}, length={}) at {}'.format(
            self.object_id, self.length, hex(id(self))
        )

    def __eq__(self, other):
        assert self.object_id == other.object_id, (self.object_id, other.object_id)
        assert self.length == other.length
        return self.object_id == other.object_id and \
            self.length == other.length

    def pack(self):
        return struct.pack('<ii', self.object_id, self.length)

    @classmethod
    def unpack(cls, byts):
        object_id, length = struct.unpack('<ii', byts[:8])
        return cls(object_id, length)


class ValueWithCode(object):

    def __init__(self, enum, value):
        self.enum = enum
        self.value = value

    def pack(self):
        return struct.pack('<B', self.enum) + pack_primitive_type(self.enum, self.value)

    @classmethod
    def unpack(cls, byts):
        enum = PrimitiveTypeEnum.unpack(byts[:1])
        value = unpack_primitive_type(enum.enum, byts[1:])
        return cls(enum.enum, value.value)


class ArrayOfValueWithCode(object):

    def __init__(self, values):
        self.values = values

    def __len__(self):
        return len(self.values)

    def pack(self):
        data = struct.pack('<i', len(self.values))
        for val in self.values:
            data += val.pack()
        return data

    @classmethod
    def unpack(cls, byts):
        length, = struct.unpack('<i', byts[:4])
        byts = byts[4:]
        values = []
        while len(values) < length:
            val = ValueWithCode.unpack(byts)
            packed_data = val.pack()
            if packed_data != byts[:len(packed_data)]:
                logger.debug(
                    "values dont' match %s != %s",
                    repr(packed_data), repr(byts[:len(packed_data)])
                )
                raise Exception()
            byts = byts[len(packed_data):]
            values.append(val)
        return cls(values)


class StringValueWithCode(object):
    '''
    The StringValueWithCode structure is a ValueWithCode where
    PrimitiveTypeEnumeration is String (18).
    '''

    enum = 18  # PrimitiveTypeEnum(STRING)

    def __init__(self, value):
        self.value = value

    def pack(self):
        return struct.pack('<B', self.enum) + LengthPrefixedString(self.value).pack()

    @classmethod
    def unpack(cls, byts):
        typ, = struct.unpack('<B', byts[0])
        if typ != cls.enum:
            raise Exception(
                "Inavlid record type enum: {}".format(cls.enum)
            )
        byts = byts[1:]
        return cls(LengthPrefixedString.unpack(byts).value)
