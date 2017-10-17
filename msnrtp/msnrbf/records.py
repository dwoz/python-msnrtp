'''
The primary stuctures used in the .NET Remoting: Binary Format Data Structure
specification.

Section 2.x.x of MS-NRBF
'''
import struct
from structures import *
from types import *
from enum import *


class TODO(Exception):
    pass


def isclass(o):
    return o.enum in [1, 3, 4, 5]


def issystemclass(o):
    if o.enum in [4]:
        return True
    return False


def hasclassinfo(o):
    return o.enum in [3, 4, 5]


class BinaryRecord(object):
    enum = None
    referencable = True

    @classmethod
    def _getbytes(cls, byts):
        typ, = struct.unpack('<B', byts[0])
        if typ != cls.enum:
            raise Exception(
                "Inavlid record type enum: {}".format(cls.enum)
            )
        return byts[1:]

    @classmethod
    def pack_type(cls):
        return struct.pack('<B', cls.enum)


class SerializationHeader(BinaryRecord):
    '''
    The SerializationHeaderRecord record MUST be the first record in a binary
    searialization

    root_id     An INT32 value (as specified in [MS-DTYP] section 2.2.22) that
                identifies the root of the graph of nodes.


    header_id   An INT32 value (as specified in [MS-DTYP] section 2.2.22) that
                identifies the Array that contains the header objects.
    '''

    enum = 0
    reserved = 0
    major_version = 1
    minor_version = 0

    def __init__(self, root_id, header_id, major_version=1, minor_version=0):
        self.root_id = root_id
        self.header_id = header_id
        self.major_version = major_version
        self.minor_version = minor_version
        self.referenced = False

    def __repr__(self):
        return '<SerializationHeader({}, {}, {}, {}) at {}>'.format(
            self.root_id, self.header_id, self.major_version, self.minor_version,
            hex(id(self))
        )

    def pack(self):
        return self.pack_type() + struct.pack(
            '<iiii',
            self.root_id,
            self.header_id,
            self.major_version,
            self.minor_version
        )

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        return cls(*struct.unpack('<iiii', ibyts[:16]))

    def __eq__(self, other):
        return (
            self.enum == other.enum and
            self.root_id == other.root_id and
            self.header_id == other.header_id and
            self.major_version == other.major_version and
            self.minor_version == other.minor_version
        )


class ClassWithId(BinaryRecord):
    enum = 1

    def __init__(self, object_id, metadata_id):
        self.object_id = object_id
        self.metadata_id = metadata_id
        self.referenced = False

    def __repr__(self):
        return '<ClassWithId(object_id={}, metadata_id={}) at {}>'.format(
            self.object_id, self.metadata_id, hex(id(self))
        )

    def pack(self):
        return self.pack_type() + struct.pack('<ii', self.object_id, self.metadata_id)

    @classmethod
    def unpack(cls, byts):
        byts = cls._getbytes(byts)
        return cls(*struct.unpack('<ii', byts[:8]))


class SystemClassWithMembers(BinaryRecord):
    enum = 2

    def __init__(self, class_info, member_info):
        raise TODO()
        self.class_info = class_info
        self.member_info = member_info
        self.referenced = False

    @property
    def object_id(self):
        return self.class_info.object_id

    @object_id.setter
    def object_id(self, value):
        self.class_info.object_id = value

    @property
    def name(self):
        return self.class_info.name

    def __repr__(self):
        return '<SystemClassWithMembersAndTypes({}, {}) at {}>'.format(
            self.class_info, self.member_info, hex(id(self))
        )

    def __eq__(self, other):
        if isinstance(other, SystemClassWithMembersAndTypes):
            return (
                self.class_info == other.class_info and
                self.member_info == other.member_info
            )
        return False

    def pack(self):
        raise TODO()
        return self.pack_type() + self.class_info.pack() + self.member_info.pack()

    @classmethod
    def unpack(cls, byts):
        raise TODO()
        ibyts = cls._getbytes(byts)
        class_info = ClassInfo.unpack(ibyts)
        ibyts = ibyts[len(class_info.pack()):]
        member_info = MemberTypeInfo.unpack(ibyts, class_info.member_count)
        return cls(class_info, member_info)


class ClassWithMembers(BinaryRecord):
    '''
    2.3.2.2
    The ClassWithMembers record is less verbose than ClassWithMembersAndTypes.
    It does not contain information about the Remoting Type information of the
    Members. This record can be used when the information is deemed unnecessary
    because it is known out of band or can be inferred from context.
    '''
    enum = 3

    def __init__(self, class_info, library_id):
        self.class_info = class_info
        self.library_id = library_id
        self.referenced = False

    @property
    def object_id(self):
        return self.class_info.object_id

    @object_id.setter
    def object_id(self, v):
        self.class_info.object_id = v

    @property
    def name(self):
        return self.class_info.name

    def pack(self):
        return self.pack_type() + self.class_info.pack() + \
            struct.pack('<i', self.library_id)

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        class_info = ClassInfo.unpack(ibyts)
        library_id, = struct.unpack('<i', ibyts[:4])
        return cls(class_info, library_id)


class SystemClassWithMembersAndTypes(BinaryRecord):
    enum = 4

    def __init__(self, class_info, member_info):
        self.class_info = class_info
        self.member_info = member_info
        self.referenced = False

    @property
    def object_id(self):
        return self.class_info.object_id

    @object_id.setter
    def object_id(self, value):
        self.class_info.object_id = value

    @property
    def name(self):
        return self.class_info.name

    def __repr__(self):
        return '<SystemClassWithMembersAndTypes({}, {}) at {}>'.format(
            self.class_info, self.member_info, hex(id(self))
        )

    def __eq__(self, other):
        if isinstance(other, SystemClassWithMembersAndTypes):
            return (
                self.class_info == other.class_info and
                self.member_info == other.member_info
            )
        return False

    def pack(self):
        return self.pack_type() + self.class_info.pack() + self.member_info.pack()

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        class_info = ClassInfo.unpack(ibyts)
        ibyts = ibyts[len(class_info.pack()):]
        member_info = MemberTypeInfo.unpack(ibyts, class_info.member_count)
        return cls(class_info, member_info)


class ClassWithMembersAndTypes(BinaryRecord):
    enum = 5

    def __init__(self, class_info, member_info, library_id):
        self.class_info = class_info
        self.member_info = member_info
        self.library_id = library_id
        self.referenced = False

    @property
    def object_id(self):
        return self.class_info.object_id

    @object_id.setter
    def object_id(self, v):
        self.class_info.object_id = v

    @property
    def name(self):
        return self.class_info.name

    def __repr__(self):
        return '<ClassWithMembersAndTypes({}, {}, {}) at {}>'.format(
            self.class_info, self.member_info, self.library_id, hex(id(self))
        )

    def __eq__(self, other):
        if isinstance(other, ClassWithMembersAndTypes):
            return (
                self.class_info == other.class_info and
                self.member_info == other.member_info and
                self.library_id == other.library_id
            )
        return False

    def x__repr__(self):
        a = '<ClassWithMembersAndTypes(\n'
        a += '  object_id={}\n'.format(self.class_info.object_id)
        a += '  member_names=\n'
        for b in self.class_info.member_names:
            a += '    {}\n'.format(b)
        a += '  member_info=\n'
        for b in self.member_info:
            a += '    {}\n'.format(b)
        a += '  library_id={}\n'.format(self.library_id)
        a += ') at {}>'.format(hex(id(self)))
        return a

    def pack(self):
        data = self.pack_type()
        data += self.class_info.pack()
        data += self.member_info.pack()
        data += struct.pack('<i', self.library_id)
        return data

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        class_info = ClassInfo.unpack(ibyts)
        ibyts = ibyts[len(class_info.pack()):]
        member_info = MemberTypeInfo.unpack(ibyts, class_info.member_count)
        ibyts = ibyts[len(member_info.pack()):]
        library_id, = struct.unpack('<i', ibyts[:4])
        return cls(
            class_info,
            member_info,
            library_id,
        )


class BinaryObjectString(BinaryRecord):
    enum = 6

    def __init__(self, object_id, value):
        self.object_id = object_id
        self.value = value
        self.referenced = False

    def __eq__(self, other):
        return (
            self.object_id == other.object_id and
            self.value == other.value
        )

    def __repr__(self):
        return "<BinaryObjectString(object_id={}, value={}) at {}>".format(
            self.object_id, self.value, hex(id(self))
        )

    def pack(self):
        data = self.pack_type()
        data += struct.pack('<i', self.object_id)
        data += LengthPrefixedString(self.value).pack()
        return data

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        object_id, = struct.unpack('<i', ibyts[:4])
        lpsval = LengthPrefixedString.unpack(ibyts[4:])
        ab = lpsval.pack()
        bb = ibyts[4:4+len(ab)]
        if bb != ab:
            raise Exception("Bytes do not match {} {}".format(repr(bb), repr(ab)))
        return cls(object_id, lpsval.value)


class BinaryArray(BinaryRecord):
    enum = 7

    def __init__(self, object_id, value):
        self.object_id = object_id
        self.value = value
        self.referenced = False

    def __eq__(self, other):
        return (
            self.object_id == other.object_id and
            self.value == other.value
        )

    def __repr__(self):
        return "<BinaryObjectString(object_id={}, value={}) at {}>".format(
            self.object_id, self.value, hex(id(self))
        )

    def pack(self):
        data = self.pack_type()
        data += struct.pack('<i', self.object_id)
        data += LengthPrefixedString(self.value).pack()
        return data

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        object_id, = struct.unpack('<i', ibyts[:4])
        lpsval = LengthPrefixedString.unpack(ibyts[4:])
        ab = lpsval.pack()
        bb = ibyts[4:4+len(ab)]
        if bb != ab:
            raise Exception("Bytes do not match {} {}".format(repr(bb), repr(ab)))
        return cls(object_id, lpsval.value)


class MemberPrimitiveTyped(BinaryRecord):
    enum = 8

    def __init__(self, typ, value):
        self.typ = typ
        self.value = value
        self.referenced = False

    def pack(self):
        return self.pack_type() + self.value.pack()

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        typenum, = struct.unpack('<B', ibyts[0])
        value = unpack_primitive_type(typ, byts)


class MemberReference(BinaryRecord):
    '''
    A Class, Array,or BinaryObjectString record MUST exist in the serialization
    stream with the value as its ObjectId. Unlike other ID references, there is
    no restriction on where the record that defines the ID appears in the
    serialization stream; that is, it MAY appear after the referencing
    record.
    '''
    enum = 9

    def __init__(self, idRef):
        # if idRef < 1:
        #     raise Exception("idRef must be a positive integer (2.5.3)")
        self.idRef = idRef

    def __repr__(self):
        return '<MemberReference(idRef={}) at {}>'.format(self.idRef, hex(id(self)))

    def __eq__(self, other):
        if isinstance(other, MemberReference):
            return self.idRef == other.idRef
        return False

    def pack(self):
        return self.pack_type() + struct.pack('<i', self.idRef)

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        return cls(*struct.unpack('<i', ibyts[:4]))


class ObjectNull(BinaryRecord):
    enum = 10

    def __init__(self):
        self.referenced = False

    def pack(self):
        return self.pack_type()

    @classmethod
    def unpack(cls, byts):
        cls._getbytes(byts)
        return cls()


class MessageEnd(BinaryRecord):
    enum = 11
    referenced = False

    def pack(self):
        return self.pack_type()

    @classmethod
    def unpack(cls, byts):
        cls._getbytes(byts)
        return cls()


class BinaryLibrary(BinaryRecord):
    enum = 12

    def __init__(self, library_id, library_name):
        self.library_id = library_id
        self.library_name = library_name
        self.referenced = False

    def __repr__(self):
        return '<BinaryLibrary({}, {}) at {}>'.format(
            self.library_id, self.library_name, hex(id(self))
        )

    def __eq__(self, other):
        if isinstance(other, BinaryLibrary):
            return (
                self.library_id == other.library_id and
                self.library_name == other.library_name
            )
        return False

    def pack(self):
        return self.pack_type() + struct.pack('<i', self.library_id) + \
            LengthPrefixedString(self.library_name).pack()

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        library_id, = struct.unpack('<i', ibyts[:4])
        library_name = LengthPrefixedString.unpack(ibyts[4:])
        return cls(library_id, library_name.value)


class ObjectNullMultiple256(BinaryRecord):
    enum = 13

    def __init__(self, count):
        self.count = count
        self.referenced = False

    def pack(self):
        return self.pack_type() + struct.pack('<B', self.count)

    @classmethod
    def unpack(cls, byts):
        byts = cls._getbytes(byts)
        count, = struct.unpack('<B', byts[:1])
        return cls(count)


class ObjectNullMultiple(BinaryRecord):
    enum = 14

    def __init__(self, count):
        self.count = count
        self.referenced = False

    def pack(self):
        return self.pack_type() + struct.pack('<I', self.count)

    @classmethod
    def unpack(cls, byts):
        byts = cls._getbytes(byts)
        count, = struct.unpack('<I', byts[:4])
        return cls(count)


class ArraySinglePrimitive(BinaryRecord):
    '''
    The ArraySinglePrimitive record contains a single-dimensional Array in
    which all Members are Primitive Value.
    '''
    enum = 15

    def __init__(self, array_info, enum):
        raise TODO()
        self.array_info = array_info
        self.enum = enum
        self.referenced = False

    @property
    def object_id(self):
        return self.array_info.object_id

    @object_id.setter
    def object_id(self, object_id):
        self.array_info.object_id = object_id

    def __repr__(self):
        return '<ArraySinglePrimitive({}) at {}>'.format(self.array_info, hex(id(self)))

    def __eq__(self, other):
        if not isinstance(other, ArraySinglePrimitive):
            logger.warn("Not a matching instance type %s", other)
            return False
        return self.array_info == other.array_info

    def pack(self):
        return self.pack_type() + self.array_info.pack() + struct.pack('<B', self.enum)

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        array_info = ArrayInfo.unpack(ibyts)
        ibyts = ibyts[len(array_info.pack()):]
        enum = struct.unpack('<B', ibyts[0])
        return cls(array_info, enum)


class ArraySingleObject(BinaryRecord):
    '''
    The ArraySingleObject record contains a single dimensional array in which
    each member record may contain any data value.
    '''
    enum = 16

    def __init__(self, array_info):
        self.array_info = array_info
        self.referenced = False

    @property
    def object_id(self):
        return self.array_info.object_id

    @object_id.setter
    def object_id(self, object_id):
        self.array_info.object_id = object_id

    def __repr__(self):
        return '<ArraySingleObject({}) at {}>'.format(self.array_info, hex(id(self)))

    def __eq__(self, other):
        if not isinstance(other, ArraySingleObject):
            logger.warn("Not a matching instance type %s", other)
            return False
        return self.array_info == other.array_info

    def pack(self):
        return self.pack_type() + self.array_info.pack()

    @classmethod
    def unpack(cls, byts):
        ibyts = cls._getbytes(byts)
        return cls(ArrayInfo.unpack(ibyts))


class ArraySingleString(BinaryRecord):
    '''
    '''
    enum = 17

    def __init__(self, array_info):
        raise TODO()
        self.array_info = array_info
        self.referenced = False

    @property
    def object_id(self):
        return self.array_info.object_id

    @object_id.setter
    def object_id(self, object_id):
        self.array_info.object_id = object_id

    def __repr__(self):
        return '<ArraySingleObject({}) at {}>'.format(self.array_info, hex(id(self)))

    def __eq__(self, other):
        if not isinstance(other, ArraySingleObject):
            logger.warn("Not a matching instance type %s", other)
            return False
        return self.array_info == other.array_info

    def pack(self):
        return self.pack_type() + self.array_info.pack()

    @classmethod
    def unpack(cls, byts):
        raise TODO()
        ibyts = cls._getbytes(byts)
        return cls(ArrayInfo.unpack(ibyts))


class MethodReturnCallArray(ArraySingleObject):
    pass


class BinaryMethodCall(BinaryRecord):

    enum = 21

    def __init__(
            self, message_enum, method_name, type_name, call_context=None,
            args=None):
        self.message_enum = message_enum
        self.method_name = method_name
        self.type_name = type_name
        self.call_context = call_context
        self.args = args
        self.referenced = False

    def pack(self):
        data = struct.pack(
            '<B', self.enum
        )
        data += self.message_enum.pack()
        data += struct.pack('<B', 0x12)
        data += LengthPrefixedString(self.method_name).pack()
        data += struct.pack('<B', 0x12)
        data += LengthPrefixedString(self.type_name).pack()
        if self.call_context:
            data += struct.pack('<i', len(self.call_context))
            data += self.call_context
        if self.args:
            data += self.args.pack()
        return data

    @classmethod
    def unpack(cls, byts):
        byts = cls._getbytes(byts)
        enum = MessageEnum.unpack(byts[:4])
        byts = byts[4:]
        method_name = StringValueWithCode.unpack(byts)
        byts = byts[len(method_name.pack()):]
        type_name = StringValueWithCode.unpack(byts)
        byts = byts[len(type_name.pack()):]
        call_context = None
        if enum.ContextInline:
            raise NotImplementedError()
        args = None
        if enum.ArgsInline:
            args = ArrayOfValueWithCode.unpack(byts)
        return cls(enum, method_name.value, type_name.value, call_context, args)


class BinaryMethodReturn(BinaryRecord):

    enum = 22

    def __init__(self, message_enum, return_value=None, call_context=None, args=None):
        self.message_enum = message_enum
        self.return_value = return_value
        self.call_context = call_context
        self.args = args
        self.referenced = False

    def __repr__(self):
        return '<BinaryMethodReturn({}) at {}>'.format(self.message_enum, hex(id(self)))

    def __eq__(self, other):
        assert self.message_enum == other.message_enum
        assert self.return_value == other.return_value
        assert self.call_context == other.call_context
        assert self.args == other.args
        return (
            self.message_enum == other.message_enum and
            self.return_value == other.return_value and
            self.call_context == other.call_context and
            self.args == other.args
        )

    def pack(self):
        # Searialization header record, MS-NRBF 2.6.1
        # data = struct.pack(
        #     '<Biiii', 0, 1, -1, 1, 0
        # )

        # Binary Library, MS-NRBF 2.6.2

        data = self.pack_type()
        data += self.message_enum.pack()
        if self.message_enum.ReturnValueInline:
            raise NotImplemented
        if self.message_enum.ContextInline:
            raise NotImplemented
        if self.message_enum.ArgsInline:
            raise NotImplemented
        # data += struct.pack('<B', 0x12)
        # data += struct.pack('<B', len([1]))
        # data += self.method_name
        # data += struct.pack('<B', 0x12)
        # data += struct.pack('<B', len(self.type_name))
        # data += self.type_name
        # if self.call_context:
        #     data += struct.pack('<i', len(self.call_context))
        #     data += self.call_context
        # if self.args:
        #     data += struct.pack('<i', len(self.args))
        #     for arg in self.args:
        #         data += struct.pack('<B', 0x12)
        #         data += struct.pack('<B', len(arg))
        #         data += arg
        # data += struct.pack('<B', 11)
        return data

    @classmethod
    def unpack(cls, byts):
        '''
        A MessageFlags value that indicates whether the Return Value,
        Arguments, Message Properties, and Call Context are present. The value
        also specifies whether the Return Value, Arguments, and Call Context
        are present in this record or the following MethodReturnCallArray
        record. For this record, the field MUST NOT have the
        MethodSignatureInArray or GenericMethod bits set
        '''
        ibyts = cls._getbytes(byts)
        enum = MessageEnum.unpack(ibyts[:4])
        if enum.ReturnValueInline:
            raise NotImplemented
        if enum.ContextInline:
            raise NotImplemented
        if enum.ArgsInline:
            raise NotImplemented
        return cls(enum)


record_types = {
    0: SerializationHeader,
    1: ClassWithId,
    2: SystemClassWithMembers,
    3: ClassWithMembers,
    4: SystemClassWithMembersAndTypes,
    5: ClassWithMembersAndTypes,
    6: BinaryObjectString,
    7: BinaryArray,
    8: MemberPrimitiveTyped,
    9: MemberReference,
    10: ObjectNull,
    11: MessageEnd,
    12: BinaryLibrary,
    13: ObjectNullMultiple256,
    14: ObjectNullMultiple,
    15: ArraySinglePrimitive,
    16: ArraySingleObject,
    17: ArraySingleString,
    21: BinaryMethodCall,
    22: BinaryMethodReturn,
}
