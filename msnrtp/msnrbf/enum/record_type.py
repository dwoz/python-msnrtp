import collections
import struct

SerializedStreamHeader = 0
ClassWithId = 1
SystemClassWithMembers = 2
ClassWithMembers = 3
SystemClassWithMembers = 4
ClassWithMembersAndTypes = 5
BinaryObjectString = 6
BinaryArray = 7
MemberPrimitiveTyped = 8
MemberReference = 9
ObjectNull = 10
MessageEnd = 11
BinaryLibrary = 12
ObjectNullMultiple256 = 13
ObjectNullMultiple = 14
ArraySinglePrimitive = 15
ArraySingleObject = 16
ArraySingleString = 17
MethodCall = 22
MethodReturn = 22

SERIALIZED_STREAM_HEADER = 'SERIALIZED_STREAM_HEADER'
CLASS_WITH_ID = 'CLASS_WITH_ID'
SYSTEM_CLASS_WITH_MEMBERS = 'SYSTEM_CLASS_WITH_MEMBERS'
CLASS_WITH_MEMBERS = 'CLASS_WITH_MEMEBRS'
SYSTEM_CLASS_WITH_MEMEBRS = 'SYSTEM_CLASS_WITH_MEMEBRS'
CLASS_WITH_MEMBERS_AND_TYPES = 'CLASS_WITH_MEMEBRS_AND_TYPES'
BINARY_OBJECT_STRING = 'BINARY_OBJECT_STRING'
BINARY_ARRAY = 'BINARY_ARRAY'
MEMBER_PRIMITIVE_TYPED = 'MEMBER_PRIMITIVE_TYPED'
MEMBER_REFERENCE = 'MEMEBER_REFERENCE'
OBJECT_NULL = 'OBJECT_NULL'
MESSAGE_END = 'MESSAGE_END'
BINARY_LIBRARY = 'BINARY_LIBRARY'
OBJECT_NULL_MULTIPLE_256 = 'OBJECT_NULL_MULTIPLE_256'
OBJECT_NULL_MULTIPLE = 'OBJECT_NULL_MULTIPLE'
ARRAY_SINGLE_PRIMITIVE = 'ARRAY_SINGLE_PRIMITIVE'
ARRAY_SINGLE_OBJECT = 'ARRAY_SINGLE_OBJECT'
ARRAY_SINGLE_STRING = 'ARRAY_SINGLE_STRING'
METHOD_CALL = 'METHOD_CALL'
METHOD_RETURN = 'METHOD_RETURN'


_RecordTypeEnum = {
    SerializedStreamHeader: SERIALIZED_STREAM_HEADER,
    ClassWithId: CLASS_WITH_ID,
    SystemClassWithMembers: SYSTEM_CLASS_WITH_MEMBERS,
    ClassWithMembers: CLASS_WITH_MEMBERS,
    SystemClassWithMembers: SYSTEM_CLASS_WITH_MEMEBRS,
    ClassWithMembersAndTypes: CLASS_WITH_MEMBERS_AND_TYPES,
    BinaryObjectString: BINARY_OBJECT_STRING,
    BinaryArray: BINARY_ARRAY,
    MemberPrimitiveTyped: MEMBER_PRIMITIVE_TYPED,
    MemberReference: MEMBER_REFERENCE,
    ObjectNull: OBJECT_NULL,                # 0x0A
    MessageEnd: MESSAGE_END,                # 0x0B
    BinaryLibrary: BINARY_LIBRARY,  # 0x0C
    ObjectNullMultiple256: OBJECT_NULL_MULTIPLE_256,   # 0x0D
    ObjectNullMultiple: OBJECT_NULL_MULTIPLE,       # 0x0E
    ArraySinglePrimitive: ARRAY_SINGLE_PRIMITIVE,     # 0x0F
    ArraySingleObject: ARRAY_SINGLE_OBJECT,        # 0x10
    ArraySingleString: ARRAY_SINGLE_STRING,        # 0x11
    MethodCall: METHOD_CALL,        # 0x15
    MethodReturn: METHOD_RETURN,    # 0x16
}


class RecordTypeEnum(object):
    '''2.1.2.1 RecordTypeEnumeration

    This enumeration identifiers the type of record. Each record (except for
    MemberPrimitiveUnUntyped) starts with a record type enumeartion. The size
    of the enumartion is one byte.

      0  0x00  SerializedStreamHeader
      1  0x01  ClassWithId
      2  0x02  SystemClassWithMembers
      3  0x03  ClassWithMembers
      4  0x04  SystemClassWithMembersAndTypes
      5  0x05  ClassWithMembersAndTypes
      6  0x06  BinaryObjectString
      7  0x07  BinaryArray
      8  0x08  MemberPrimitiveTyped
      9  0x09  MemberReference
     10  0x0A  ObjectNull
     11  0x0B  MessageEnd
     12  0x0C  BinaryLibrary
     13  0x0D  ObjectNullMultiple256
     14  0x0E  ObjectNullMultiple
     15  0x0F  ArraySinglePrimitive
     16  0x10  ArraySingleObject
     17  0x11  ArraySingleString
     21  0x15  MethodCall
     22  0x16  MethodReturn
   '''

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return '<RecordTypeEnum({}) at {}>'.format(self.n, hex(id(self)))

    def __str__(self):
        return 'RecordTypeEnum:{}:{}'.format(self.n, self.name)

    def __eq__(self, other):
        if isinstance(other, RecordTypeEnum):
            return self.n == other.n
        return self.n == other

    @property
    def name(self):
        return _RecordTypeEnum[self.n]

    @classmethod
    def unpack(cls, byte):
        n = struct.unpack('<B', byte)[0]
        return cls(n)
