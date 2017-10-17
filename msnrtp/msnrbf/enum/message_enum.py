import ctypes
import struct


c_uint16 = ctypes.c_uint16
_RESERVED = "Reserved"


class _Fields(ctypes.LittleEndianStructure):

    _fields_ = [
            ("NoArgs", c_uint16, 1),
            ("ArgsInline", c_uint16, 1),
            ("ArgsIsArray", c_uint16, 1),
            ("ArgsInArray", c_uint16, 1),
            ("NoContext", c_uint16, 1),
            ("ContextInline", c_uint16, 1),
            ("ContextInArray", c_uint16, 1),
            ("MethodSignatureInArray", c_uint16, 1),
            ("PropertyInArray", c_uint16, 1),
            ("NoReturnValue", c_uint16, 1),
            ("ReturnValueVoid", c_uint16, 1),
            ("ReturnValueInline", c_uint16, 1),
            ("ReturnValueInArray", c_uint16, 1),
            ("ExceptionInArray", c_uint16, 1),
            ("GenericMethod", c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
            (_RESERVED, c_uint16, 1),
        ]


def pp(enum, pfields=None):
    if pfields is None:
        pfields = [x[0] for x in _Fields._fields_ if x[0] != _RESERVED]


class MessageEnum(ctypes.Union):
    _anonymous_ = ('bit',)
    _fields_ = [
        ('bit', _Fields),
        ('asWord', c_uint16)
    ]

    def __eq__(self, other):
        return self.asWord == other.asWord

    def __init__(self, **kwargs):
        super(MessageEnum, self).__init__()
        for k in kwargs:
            v = 1 if kwargs[k] else 0
            setattr(self, k, v)

    @classmethod
    def fromword(cls, n):
        o = cls()
        o.asWord = n
        return o

    def pack(self):
        return struct.pack('<I', self.asWord)

    @classmethod
    def unpack(cls, byts):
        return cls.fromword(struct.unpack('<I', byts[:4])[0])
