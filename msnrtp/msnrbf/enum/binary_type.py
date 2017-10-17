import struct


PRIMITIVE = 0
STRING = 1
OBJECT = 2
SYSTEM_CLASS = 3
CLASS = 4
OBJECT_ARRAY = 5
STRING_ARRAY = 6
PRIMITIVE_ARRAY = 7

Primitive = 'Primitive'
String = 'String'
Object = 'Object'
SystemClass = 'SystemClass'
Class = 'Class'
ObjectArray = 'ObjectArray'
StringArray = 'StringArray'
PrimitiveArray = 'PrimiiveArray'

_BinaryTypeEnum = {
    PRIMITIVE: Primitive,
    STRING: String,
    OBJECT: Object,
    SYSTEM_CLASS: SystemClass,
    CLASS: Class,
    OBJECT_ARRAY: ObjectArray,
    STRING_ARRAY: StringArray,
    PRIMITIVE_ARRAY: PrimitiveArray,
}


class BinaryTypeEnum(object):

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return '<BinaryTypeEnum({}) at {}>'.format(
            _BinaryTypeEnum[self.n], hex(id(self)))

    def __str__(self):
        return 'BinaryTypeEnum:{}:{}'.format(self.n, self.name)

    def __eq__(self, other):
        if not isinstance(other, BinaryTypeEnum):
            return self.n == other
        return self.n == other.n

    @property
    def name(self):
        return _BinaryTypeEnum[self.n]

    def pack(self):
        return struct.pack('<B', self.n)

    @classmethod
    def unpack(cls, byte):
        n = struct.unpack('<B', byte)[0]
        return cls(n)
