import struct

BOOLEAN = 1
BYTE = 2
CHAR = 3
DECIMAL = 5
DOUBLE = 6
INT16 = 7
INT32 = 8
INT64 = 9
SBYTE = 10
SINGLE = 11
TIMESPAN = 12
DATETIME = 13
UINT16 = 14
UINT32 = 15
UINT64 = 16
NULL = 17
STRING = 18


Boolean = 'Boolean'
Byte = 'Byte'
Char = 'Char'
Decimal = 'Decimal'
Int16 = 'Int16'
Int32 = 'Int32'
Int64 = 'Int64'
SByte = 'SByte'
Single = 'Single'
TimeSpan = 'TimeSpan'
DateTime = 'DateTime'
UInt16 = 'UInt16'
UInt32 = 'UInt32'
UInt32 = 'UInt32'
UInt64 = 'UInt64'
Null = 'Null'
String = 'String'


_PrimitiveTypeEnum = {
    BOOLEAN: Boolean,
    BYTE: Byte,
    CHAR: Char,
    DECIMAL: Decimal,
    INT16: Int16,
    INT32: Int32,
    INT64: Int64,
    SBYTE: SByte,
    SINGLE: Single,
    TIMESPAN: TimeSpan,
    DATETIME: DateTime,
    UINT16: UInt16,
    UINT32: UInt32,
    UINT64: UInt64,
    NULL: Null,
    STRING: String,
}


class PrimitiveTypeEnum(object):

    def __init__(self, enum):
        self.enum = enum

    def __repr__(self):
        return '<PrimitiveTypeEnum({}) at {}>'.format(
            _PrimitiveTypeEnum[self.enum], hex(id(self)))

    def __str__(self):
        return 'PrimitiveTypeEnum:{}:{}'.format(self.enum, self.name)

    @property
    def name(self):
        return _PrimitiveTypeEnum[self.enum]

    def pack(self):
        return struct.pack('<B', self.enum)

    @classmethod
    def unpack(cls, byte):
        return cls(*struct.unpack('<B', byte))

    def __eq__(self, other):
        if not isinstance(other, PrimitiveTypeEnum):
            return self.enum == other
        return self.enum == other.enum
