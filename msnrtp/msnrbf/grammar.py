'''
MS-NRBF - 2.7 Binary Record Grammar

https://tools.ietf.org/html/rfc5234

ABNF productions      Meaning

remotingMessage   =   SerializationHeader
                      *(referenceable)
                      (methodCall/methodReturn)
                      *(referenceable)
                      MessageEnd

methodCall        =   0*1(BinaryLibrary) BinaryMethodCall 0*1(callArray)

methodReturn      =   0*1(BinaryLibrary) BinaryMethodReturn 0*1(callArray)

callArray         =   0*1(BinaryLibrary)
                      ArraySingleObject
                       *(memberReference)
memberReference   =   0*1(BinaryLibrary)
                      (MemberPrimitiveUnTyped / MemberPrimitiveTyped / MemberReference /
                        BinaryObjectString / nullObject /Classes)

nullObject        =   ObjectNull / ObjectNullMultiple / ObjectNullMultiple256

referenceable     =   Classes/Arrays/BinaryObjectString

Classes           =   0*1(BinaryLibrary)
                      (ClassWithId / ClassWithMembers/ ClassWithMembersAndTypes /
                        SystemClassWithMembers / SystemClassWithMembersAndTypes)
                      *(memberReference)

Arrays            =   0*1(BinaryLibrary)
                      ((ArraySingleObject *(memberReference)) /
                        (ArraySinglePrimitive *(MemberPrimitiveUnTyped)) /
                        (ArraySingleString *(BinaryObjectString/MemberReference/nullObject)) /
                        (BinaryArray*(memberReference)) )
'''
from .enum import *
from .enum.message_enum import *
from .enum import record_type as rt
from .enum import binary_type as bt
from .records import *
import logging
from collections import OrderedDict
import hashlib


logger = logging.getLogger(__name__)


class StreamError(Exception):
    pass


class RecordNotFound(Exception):
    pass


class ClassesContext(object):

    def __init__(self, classes=None, classrefs=None):
        self.classes = classes
        # ClassWithId records
        self.classrefs = classrefs
        if self.classes is None:
            self.classes = {}
        if self.classrefs is None:
            self.classrefs = {}

    def _meta_id(self, record):
        if hasattr(record, 'metadata_id'):
            return record.metadata_id
        else:
            return record.object_id

    def get_member_info(self, record):
        return self.classes[self._meta_id(record)].member_info

    def get_class_info(self, record):
        return self.classes[self._meta_id(record)].class_info

    def get_class(self, name):
        for cls_id in self.classes:
            if self.classes[cls_id].name == name:
                return self.classes[cls_id]

    def get_library_id(self, record):
        return self.classes[self._meta_id(record)].library_id

    def add_class(self, record):
        # print('add_class {}'.format(record))
        if record.object_id in self.classes:
            raise Exception
        self.classes[record.object_id] = record

    def add_classref(self, classref):
        if classref.metadata_id not in self.classes:
            raise Exception
        return self.classes[classref.metadata_id]


class RefsContext(object):
    '''

    refables      Objects that can be referenced
    pending       References that have yet to show up in the message
    complete      References that have been fullfilled
    references    Stores message 'referenceable' parts in order
    '''

    def __init__(self, refables=None, pending=None, complete=None, referenceables=None):
        self.refables = refables
        if self.refables is None:
            self.refables = {}
        self.pending = pending
        if self.pending is None:
            self.pending = {}
        self.complete = complete
        if self.complete is None:
            self.complete = {}
        self.referenceables = referenceables
        if self.referenceables is None:
            self.referenceables = []

    def has_pending(self):
        has_pending = False
        for x in self.pending:
            for y in self.pending[x]:
                has_pending = True
                break
        return has_pending

    def _set_complete(self, a):
        if a.record is None:
            raise Exception
        if a.idRef not in self.complete:
            self.complete[a.idRef] = [a]
        else:
            self.complete[a.idRef].append(a)

    def _set_pending(self, a):
        if a.idRef not in self.pending:
            self.pending[a.idRef] = [a]
        else:
            self.pending[a.idRef].append(a)

    def add_refable(self, refable):
        # print('Refable is', refable)
        # if refable.object_id in self.refables:
        #     raise Exception('Refable exists in refables {}'.format(refable.record))
        self.refables[refable.object_id] = refable
        if refable.object_id in self.pending:
            for n, a in enumerate(self.pending[refable.object_id]):
                a._referenceable = refable
                self.pending[refable.object_id].pop(n)
                if not self.pending[refable.object_id]:
                    self.pending.pop(refable.object_id)

    def add_reference(self, ref):
        # print('Reference is', ref)
        if ref.idRef in self.refables:
            ref._referenceable = self.refables[ref.idRef]
            self._set_complete(ref)
            return
        self._set_pending(ref)


class MessageContext(object):

    def __init__(self, header=None, method=None, end=None, _libs=None, _refs=None, _classes=None):
        self.header = header
        self.method = method
        self.end = end
        self._libs = _libs
        self.refs = _refs
        self.classes = _classes
        self._oid = 1
        if self._libs is None:
            self._libs = {}
        if self.refs is None:
            self.refs = RefsContext()
        if self.classes is None:
            self.classes = ClassesContext()
        self.objects = {}

    @property
    def referenceables(self):
        return self.refs.referenceables

    def add_lib(self, lib):
        self._libs[lib.library_id] = lib

    def get_lib(self, lib_id):
        return self._libs[lib_id]

    def set_header(self, header):
        self.header = header

    def set_method(self, method):
        self.method = method

    def add_refable(self, refable):
        self.refs.add_refable(refable)

    def add_reference(self, ref):
        self.refs.add_reference(ref)

    def append_referenceable(self, referenceable):
        self.refs.referenceables.append(referenceable)

    def has_pending_refs(self):
        return self.refs.has_pending()

    def get_member_info(self, record):
        return self.classes.get_member_info(record)

    def get_class(self, name):
        return self.classes.get_class(name)

    def get_class_info(self, record):
        return self.classes.get_class_info(record)

    def get_library_id(self, record):
        return self.classes.get_library_id(record)

    def add_class(self, record):
        self.classes.add_class(record)

    def add_classref(self, record):
        return self.classes.add_classref(record)

    def set_message_end(self, record):
        self.end = record

    def has_exception(self):
        if self.method:
            return self.method.message_enum.ExceptionInArray == 1
        return False

    def has_lib_id(self, library_name):
        for library_id in self._libs:
            if library_name == self._libs[library_id].library_name:
                return library_id

    def value_in_array(self):
        enum = self.method.message_enum
        if self.method:
            if enum.ArgsInArray or enum.ReturnValueInArray:
                return True
        return False

    def next_id(self):
        nid = self._oid
        self._oid += 1
        # if self._oid == 58:
        #     raise Exception
        return nid

    def root_id(self):
        '''
        When a method return or reply is present. This value is 0 when there is
        no call array and when there is a call array present this will be the
        id of the array (usually 1). Otherwise, when there is no method
        present, this is the id of the Class, Array, or BinaryObjectString
        record contained in the serialization stream.
        '''
        return self.header.root_id

    def _hashobj(self, obj):
        if isinstance(obj, BinaryObjectString):
            return hashlib.md5(obj.value).hexdigest()
        else:
            raise Exception()

    def add_object(self, obj):
        objhsh = self._hashobj(obj)
        self.objects[objhsh] = obj

    def get_object(self, obj):
        objhsh = self._hashobj(obj)
        if objhsh in self.objects:
            return self.objects[objhsh]


def _remove_byts(byts_to_rem, byts):
    packedbyts = byts[:len(byts_to_rem)]
    if byts_to_rem != packedbyts:
        raise Exception("{} != {}".format(repr(byts_to_rem), repr(packedbyts)))
    return byts[len(byts_to_rem):]


def _consume_one_of(classes, byts, required=False):
    enum = rt.RecordTypeEnum.unpack(byts[0])
    o = None
    classmap = dict(zip([a.enum for a in classes], classes))
    if enum.n in classmap:
        o = classmap[enum.n].unpack(byts)
        byts = _remove_byts(o.pack(), byts)
    elif required:
        logger.debug("enum: %s\tclassmap: %s", enum, classmap)
        raise RecordNotFound("RecordNotFound")
    # if o:
    #     logger.debug('stream: %s', o)
    return o, byts


def _consume_record(reccls, byts, required=False):
    return _consume_one_of([reccls], byts, required)


def _instanceof(x, typs):
    for typ in typs:
        if isinstance(x, typ):
            return True
    return False


class MemberPrimitiveUnTyped(object):

    def __init__(self, typ, value):
        self.typ = typ
        self.value = value

    def __repr__(self):
        return '<MemberPrimitiveUnTyped({}, {})>'.format(self.typ, self.value)

    def pack(self):
        return self.value.pack()

    @classmethod
    def unpack(cls, typ, byts):
        value = unpack_primitive_type(typ, byts)
        return cls(typ, value)

    @classmethod
    def consume(cls, typ, byts):
        o = cls.unpack(typ, byts)
        return o, _remove_byts(o.pack(), byts)


class Classes(object):

    _class_ref_recs = [
        ClassWithId,
    ]
    _system_class_recs = [
        SystemClassWithMembers,
        SystemClassWithMembersAndTypes,
    ]
    _userspace_class_recs = [
        ClassWithMembers,
        ClassWithMembersAndTypes,
    ]
    _recs = _class_ref_recs + _system_class_recs + _userspace_class_recs

    def __init__(self, ctxt, lib=None, record=None, refs=None, member_info=None):
        self.ctxt = ctxt
        self.lib = lib
        self._class = None
        if self.lib:
            self.ctxt.add_lib(lib)
        if _instanceof(record, self._class_ref_recs):
            self._class = self.ctxt.add_classref(record)
        elif _instanceof(record, [ClassWithMembersAndTypes, SystemClassWithMembersAndTypes]):
            # self.ctxt.add_class(record)
            self._class = record
        else:
            logger.warn("class not added to context: %s", record)
        self.record = record
        self.refs = refs
        if self.refs is None:
            self.refs = []
        self._member_info = member_info

    @property
    def member_info(self):
        return self.ctxt.get_member_info(self.record)

    @property
    def class_info(self):
        return self.ctxt.get_class_info(self.record)

    @property
    def class_name(self):
        return self.class_info.name

    @property
    def library_id(self):
        if _instanceof(self._class, self._userspace_class_recs):
            return self._class.library_id

    @property
    def library_name(self):
        if isinstance(self._class, SystemClassWithMembersAndTypes):
            return
        else:
            return self.ctxt.get_lib(self.library_id).library_name

    @property
    def object_id(self):
        return self.record.object_id

    def stream(self):
        stream = []
        if self.lib:
            stream.append(self.lib)
        stream.append(self.record)
        for ref in self.refs:
            stream.extend(ref.stream())
        return stream

    def pack(self):
        data = ''
        if self.lib:
            data += self.lib.pack()
        data += self.record.pack()
        for ref in self.refs:
            data += ref.pack()
        return data

    @classmethod
    def unpack(cls, ctxt, byts):
        lib, byts = _consume_record(BinaryLibrary, byts)
        record, byts = _consume_one_of([
                ClassWithId,
                ClassWithMembers,
                ClassWithMembersAndTypes,
                SystemClassWithMembersAndTypes
            ],
            byts,
            required=True
        )
        if _instanceof(record, [ClassWithId]):
            member_info = ctxt.get_member_info(record)
        else:
            member_info = record.member_info
        refs = []
        try:
            for x, y in member_info:
                if x == bt.PRIMITIVE:
                    ref, byts = MemberRef.consume(ctxt, byts, y)
                    # print("*Primitive ref", ref)
                elif x == bt.STRING:
                    ref, byts = MemberRef.consume(ctxt, byts)
                    # print("*String ref", ref)
                else:
                    ref, byts = MemberRef.consume(ctxt, byts)
                    # print("*Member ref", ref)
                if not ref:
                    raise StreamError
                refs.append(ref)
        except Exception as e:
            logger.exception('*** %s', record)
            raise e
        if _instanceof(record, [ClassWithMembersAndTypes, SystemClassWithMembersAndTypes]):
            ctxt.add_class(record)
        return cls(ctxt, lib, record, refs)

    @classmethod
    def consume(cls, ctxt, byts):
        o = cls.unpack(ctxt, byts)
        return o, _remove_byts(o.pack())


class Arrays(object):
    _recs = [
        ArraySingleObject,
        ArraySinglePrimitive,
        ArraySingleString,
        # BinaryArray
    ]

    def __init__(self, ctxt, record=None, refs=None):
        self.ctxt = ctxt
        self.record = record
        self.refs = refs
        if self.refs is None:
            self.refs = []

    @property
    def object_id(self):
        return self.record.object_id

    def stream(self):
        stream = [self.record]
        for ref in self.refs:
            stream.extend(ref.stream())
        return stream

    def pack(self):
        data = self.record.pack()
        for ref in self.refs:
            data += ref.pack()
        return data

    @classmethod
    def unpack(cls, ctxt, byts):
        lib, byts = _consume_record(BinaryLibrary, byts)
        record, byts = _consume_one_of(
            cls._recs,
            byts,
            required=True
        )
        refs = []
        if isinstance(record, ArraySingleObject) or isinstance(record, BinaryArray):
            # We've not actualy seen a BinaryArray so this may need a todo.
            for x in range(record.array_info.length):
                ref, byts = MemberRef.consume(ctxt, byts)
                refs.append(ref)
            # member refs
        elif isinstance(record, ArraySinglePrimitive):
            raise TODO()
            # member prim untyped
            pass
        elif isinstance(record, ArraySingleString):
            raise TODO()
            # (BinaryObjectString/MemberReference/nullObject)
            pass
        else:
            raise StreamError()
        return cls(ctxt, record, refs)


class NullObject(object):
    _recs = [
        ObjectNull,
        ObjectNullMultiple,
        ObjectNullMultiple256,
    ]

    def __init__(self, ctxt, record):
        self.ctxt = ctxt
        self.record = record

    def stream(self):
        return [self.record]

    def pack(self):
        return self.record.pack()

    @classmethod
    def unpack(cls, ctxt, byts):
        record, byts = _consume_one_of(
            cls._recs,
            byts,
            required=True
        )
        return cls(ctxt, record)


class MethodCall(object):

    def __init__(self, ctxt, lib=None, method=None, array=None):
        self.ctxt = ctxt
        self.lib = lib
        if self.lib:
            self.ctxt.add_lib(lib)
        self.method = method
        self.array = array

    @property
    def message_enum(self):
        return self.method.message_enum

    def pack(self):
        data = ''
        if self.lib:
            data = lib.pack()
        data += self.method.pack()
        if self.array:
            data += self.array.pack()
        return data

    @classmethod
    def unpack(cls, byts):
        lib, byts = _consume_record(BinaryLibrary, byts)
        method, byts = _consume_record(BinaryMethodCall, byts)
        if not method:
            raise StreamError("Expected library and/or method call")
        arry = None
        if cls._should_have_array(method):
            arry, byts = CallArray.consume(byts)
        return cls(lib, method, arry)

    @classmethod
    def _should_have_array(cls, method):
        e = method.message_enum
        if (e.ArgsInArray or e.ArgsIsArray or
                e.ContextInArray):
            return True
        return False

    @classmethod
    def consume(cls, byts):
        o = cls.unpack(byts)
        return o, _remove_byts(o.pack(), byts)


class MethodReturn(object):

    def __init__(self, ctxt, lib=None, method=None, array=None):
        self.ctxt = ctxt
        self.lib = lib
        if self.lib:
            self.ctxt.add_lib(lib)
        self.method = method
        self.array = array

    @property
    def message_enum(self):
        return self.method.message_enum

    def stream(self):
        stream = []
        if self.lib:
            stream.append(self.lib)
        stream.append(self.method)
        if self.array:
            stream.extend(self.array.stream())
        return stream

    def pack(self):
        byts = ''
        if self.lib:
            byts += self.lib.pack()
        byts += self.method.pack()
        if self.array:
            byts += self.array.pack()
        return byts

    @classmethod
    def unpack(cls, ctxt, byts):
        lib, byts = _consume_record(BinaryLibrary, byts)
        method, byts = _consume_record(BinaryMethodReturn, byts, required=True)
        arry, byts = CallArray.consume(ctxt, byts)
        return cls(ctxt, lib, method, arry)

    @classmethod
    def _unpack_callarray(cls, byts):
        lib, byts = _consume_record(BinaryLibrary, byts)

    @classmethod
    def consume(cls, ctxt, byts):
        o = cls.unpack(ctxt, byts)
        return o, _remove_byts(o.pack(), byts)


class Referenceable(object):
    _classes_recs = Classes._recs
    _arrays_recs = Arrays._recs

    def __init__(self, ctxt, record):
        self.ctxt = ctxt
        self.record = record
        self.ctxt.add_refable(self)
        # self.ctxt.append_referenceable(self)

    # @property
    # def object_id(self):
    #     return self.record.object_id

    def __getattr__(self, val):
        return getattr(self.record, val)

    def stream(self):
        return self.record.stream()

    def pack(self):
        return self.record.pack()

    @classmethod
    def unpack(cls, ctxt, byts):
        lib, tmpbyts = _consume_record(BinaryLibrary, byts)
        tmprec, tmpbyts = _consume_one_of(
            cls._classes_recs + cls._arrays_recs + [BinaryObjectString],
            tmpbyts,
            required=True
        )
        record = None
        if isinstance(tmprec, BinaryObjectString):
            record = tmprec
        else:
            for x in cls._classes_recs:
                if isinstance(tmprec, x):
                    record = Classes.unpack(ctxt, byts)
                    break
            for x in cls._arrays_recs:
                if isinstance(tmprec, x):
                    record = Arrays.unpack(ctxt, byts)
                    break
        if record is None:
            raise StreamError()
        return cls(ctxt, record)

    @classmethod
    def consume(cls, ctxt, byts):
        o = cls.unpack(ctxt, byts)
        return o, _remove_byts(o.pack(), byts)


class MemberRef(object):
    _classes_recs = Classes._recs
    _null_recs = NullObject._recs

    def __init__(self, ctxt, lib=None, ref=None, typ=None, referenceable=None):
        self.ctxt = ctxt
        self.lib = lib
        if self.lib:
            self.ctxt.add_lib(lib)
        self.ref = ref
        self._referenceable = None
        self._record = None
        self.typ = typ

        if isinstance(ref, MemberReference):
            ctxt.add_reference(self)
            self.ref = ref
        else:
            self._record = ref
        if isinstance(ref, BinaryObjectString):
            ctxt.add_refable(ref)
        # Arrays?
        # print("Ref is ref", self.ref)

    @property
    def record(self):
        if self._record:
            return self._record
        if self._referenceable:
            return self._referenceable
        else:
            raise Exception("Referenceable not added yet")

    @property
    def idRef(self):
        return self.ref.idRef

    def stream(self):
        stream = []
        if self.lib:
            stream.append(self.lib)
        try:
            stream.extend(self.ref.stream())
        except AttributeError as e:
            # print(self, self.ref)
            stream.append(self.ref)
        return stream

    def pack(self):
        if self.lib:
            return self.lib.pack() + self.ref.pack()
        return self.ref.pack()

    @classmethod
    def unpack(cls, ctxt, byts, typ=None):
        lib = None
        # (MemberPrimitiveUnTyped / MemberPrimitiveTyped / MemberReference /
        # BinaryObjectString / nullObject /Classes)
        if typ:
            tmprec, tmpbyts = MemberPrimitiveUnTyped.consume(typ, byts)
        else:
            tmplib, tmpbyts = _consume_record(BinaryLibrary, byts)
            tmprec, tmpbyts = _consume_one_of(
                cls._classes_recs + cls._null_recs + [
                    MemberPrimitiveTyped,
                    MemberReference,
                    BinaryObjectString,
                ],
                byts,
                required=True
            )
        if _instanceof(tmprec, cls._classes_recs):
            ref = Classes.unpack(ctxt, byts)
        elif _instanceof(tmprec, cls._null_recs):
            ref = NullObject.unpack(ctxt, byts)
        else:
            ref = tmprec
        return cls(ctxt, lib, ref, typ)

    @classmethod
    def consume(cls, ctxt, byts, typ=None):
        o = cls.unpack(ctxt, byts, typ)
        return o, _remove_byts(o.pack(), byts)


class CallArray(object):

    def __init__(self, ctxt, lib=None, array=None, refs=None):
        self.ctxt = ctxt
        self.lib = lib
        if self.lib:
            self.ctxt.add_lib(lib)
        self.array = array
        self.refs = refs
        if self.refs is None:
            self.refs = []

    def stream(self):
        stream = []
        if self.lib:
            stream.append(self.lib)
        stream.append(self.array)
        for ref in self.refs:
            stream.extend(ref.stream())
        return stream

    def pack(self):
        byts = ''
        if self.lib:
            byts += self.lib.pack()
        byts += self.array.pack()
        for ref in self.refs:
            byts += ref.pack()
        return byts

    @classmethod
    def unpack(cls, ctxt, byts):
        lib, byts = _consume_record(BinaryLibrary, byts)
        array, byts = _consume_record(ArraySingleObject, byts, required=True)
        refs = []
        for i in range(array.array_info.length):
            ref, byts = MemberRef.consume(ctxt, byts)
            refs.append(ref)
        return cls(ctxt, lib, array, refs)

    @classmethod
    def consume(cls, ctxt, byts):
        o = cls.unpack(ctxt, byts)
        return o, _remove_byts(o.pack(), byts)


class ClassExists(Exception):
    pass


class RemotingMessage(object):

    def __init__(self, context=None, context_cls=MessageContext):
        self.context = context
        if self.context is None:
            self.context = context_cls(self)

    @property
    def header(self):
        return self.context.header

    @property
    def method(self):
        return self.context.method

    @property
    def refs(self):
        return self.context.referenceables

    @property
    def end(self):
        return self.context.end

    def stream(self):
        stream = [self.header] + self.method.stream()
        for ref in self.refs:
            stream.extend(ref.stream())
        stream.append(self.end)
        return stream

    def pack(self):
        data = self.header.pack()
        if self.method:
            data += self.method.pack()
        for ref in self.refs:
            data += ref.pack()
        data += self.end.pack()
        return data

    @classmethod
    def unpack(cls, byts, context=None, context_cls=MessageContext):
        if context is None:
            context = context_cls()
        header, byts = _consume_record(SerializationHeader, byts)
        context.set_header(header)
        # TODO: Refs could be here
        method, byts = cls._consume_method(context, byts)
        context.set_method(method)
        while context.has_pending_refs():
            try:
                ref, byts = Referenceable.consume(context, byts)
            except RecordNotFound:
                break
            context.append_referenceable(ref)
        end, byts = _consume_record(MessageEnd, byts, required=True)
        context.set_message_end(end)
        return cls(context)

    @classmethod
    def _consume_method(cls, ctxt, byts):
        method = None
        lib, byts = _consume_record(BinaryLibrary, byts)
        enum = rt.RecordTypeEnum.unpack(byts[0])
        if enum == BinaryMethodCall.enum:
            method, byts = MethodCall.consume(ctxt, byts)
        elif enum == BinaryMethodReturn.enum:
            method, byts = MethodReturn.consume(ctxt, byts)
        return method, byts

    @classmethod
    def build_method_call(cls, method, context=None, context_cls=MessageContext):
        if context is None:
            context = context_cls()
        context.set_header(SerializationHeader(0, 0, 0))
        context.set_method(method)
        context.set_message_end(MessageEnd())
        return cls(context)

    @classmethod
    def build_method_return(
            cls, value=None, exception=None, ctxt=None,
            context_cls=MessageContext):
        cls.clsvals = {}
        cls.objects = {}
        if ctxt is None:
            ctxt = context_cls()
        # TODO: Header values based on value type and  exception
        ctxt.set_header(SerializationHeader(1, -1, 1))
        method = MethodReturn(ctxt)
        if exception:
            method.method = BinaryMethodReturn(MessageEnum(ExceptionInArray=True))
            ctxt.set_method(method)
            arrayrec = ArraySingleObject(ArrayInfo(ctxt.next_id(), 1))
            method.array = CallArray(ctxt, array=arrayrec)
            method.array.refs.append(excepion)
        else:
            # TODO: Enum values based on exception and value type
            method.method = BinaryMethodReturn(MessageEnum(ReturnValueInArray=True))
            ctxt.set_method(method)
            if not cls._is_object(value):
                raise Exception
            arrayrec = ArraySingleObject(ArrayInfo(ctxt.next_id(), 1))
            method.array = CallArray(ctxt, array=arrayrec)
            for parent, n, node in cls.nodeiter(value):
                if cls._is_object(node):
                    cls.handle_cls(ctxt, parent, n, node)
                elif cls._is_array(node):
                    cls.handle_ary(ctxt, parent, n, node)
                else:
                    cls.handle_typ(ctxt, parent, n, node)
        ctxt.set_message_end(MessageEnd())
        return cls(ctxt)

    @staticmethod
    def _is_object(val):
        from remoting_types import Object
        return isinstance(val, Object)

    @staticmethod
    def _is_array(val):
        from remoting_types import ObjArray
        return isinstance(val, ObjArray)

    @classmethod
    def build_system_class(cls, value, ctxt):
        vhash = value.hash_values()
        if vhash in cls.clsvals:
            logger.debug('hash exists %s %s', value, cls.clsvals[vhash].object_id)
            ctxt.next_id()
            return cls.clsvals[vhash], True
            # raise ClassExists()
            # raise Exception
        clsrec = ctxt.get_class(value._class)
        if clsrec:  # and cls.library_id == lib_id:
            clsid = ctxt.next_id()
            # if clsrec.object_id < 0:
            #     clsid = - clsid
            clsrecord = ClassWithId(clsid, clsrec.object_id)
        else:

            class_info = ClassInfo(
                ctxt.next_id(),
                value._class,
                len(value.member_names()),
                value.member_names(),
            )
            member_info = MemberTypeInfo(value.member_info())
            clsrecord = SystemClassWithMembersAndTypes(class_info, member_info)
            ctxt.add_class(clsrecord)
        if vhash not in cls.clsvals:
            cls.clsvals[vhash] = clsrecord
        return clsrecord, False

    @classmethod
    def build_userspace_class(cls, value, ctxt, noref=False):
        def normid(x, noref):
            if noref:
                return - x
            return x
        vhash = value.hash_values()
        if vhash in cls.clsvals:
            raise ClassExists(value)
        libs = []
        lib = None
        lib_id = ctxt.has_lib_id(value._library)
        if not lib_id:
            lib = BinaryLibrary(ctxt.next_id(), value._library)
            ctxt.add_lib(lib)
            lib_id = lib.library_id
        clsrec = ctxt.get_class(value._class)
        if clsrec and clsrec.library_id == lib_id:
            clsid = ctxt.next_id()
            if clsrec.object_id < 0:
                clsid = - clsid
            clsrecord = ClassWithId(clsid, clsrec.object_id)
            # raise Exception()
        else:
            class_info_rec = ClassInfo(
                normid(ctxt.next_id(), noref),
                value._class,
                len(value.member_names()),
                value.member_names()
            )
            member_info = value.member_info()
            member_info_rec = MemberTypeInfo(value.member_info())
            clsrecord = ClassWithMembersAndTypes(class_info_rec, member_info_rec, lib_id)
            ctxt.add_class(clsrecord)
        cls.clsvals[vhash] = clsrecord
        return clsrecord, lib

    @classmethod
    def nodeiter(cls, value=None):
        stack = [(None, 0, value)]
        while stack:
            cur_parent, cur_n, cur_node = stack[0]
            stack = stack[1:]
            if cls._is_object(cur_node):
                for n, (x, y) in enumerate(cur_node.member_info()):
                    attrname = cur_node._members[n][0]
                    memberval = getattr(cur_node, attrname)
                    stack.append((cur_node, n, memberval))
                yield (cur_parent, cur_n, cur_node)
            elif cls._is_array(cur_node):
                for n, a in enumerate(cur_node):
                    stack.append((cur_node, n, a))
                yield (cur_parent, cur_n, cur_node)
            else:
                yield (cur_parent, cur_n, cur_node)

    @classmethod
    def handle_cls(cls, ctxt, parent, n, node):
        if node.is_system_class():
            lib = None
            try:
                clsrecord, existing = cls.build_system_class(node, ctxt)
            except ClassExists:
                pass
            classes = Classes(ctxt, lib, clsrecord)
            node._g = classes
            ref = MemberRef(ctxt, ref=MemberReference(clsrecord.object_id))
            if existing:
                logger.debug('existing: %s', clsrecord)
            else:
                refable = Referenceable(ctxt, classes)
                ctxt.append_referenceable(refable)
            if not parent:
                ctxt.method.array.refs.append(ref)
            else:
                parent._g.refs.append(ref)
        elif node._referenceable:
            clsrecord, lib = cls.build_userspace_class(node, ctxt)
            classes = Classes(ctxt, lib, clsrecord)
            node._g = classes

            ref = MemberRef(ctxt, ref=MemberReference(clsrecord.object_id))
            refable = Referenceable(ctxt, classes)
            ctxt.append_referenceable(refable)
            if not parent:
                ctxt.method.array.refs.append(ref)
            else:
                parent._g.refs.append(ref)
        else:
            clsrecord, lib = cls.build_userspace_class(node, ctxt, True)
            if isinstance(parent._g, Classes):
                if not parent._g.lib:
                    parent._g.lib = lib
                    lib = None
            classes = Classes(ctxt, lib, clsrecord)
            node._g = classes
            if cls._is_array(parent):
                logger.debug('Will do ref %s %s', clsrecord, parent._g)
                if clsrecord.object_id < 0:
                    clsrecord.object_id = - clsrecord.object_id
                ref = MemberRef(ctxt, ref=MemberReference(clsrecord.object_id))
                refable = Referenceable(ctxt, classes)
                ctxt.append_referenceable(refable)
                member = ref
            else:
                logger.debug('Wont do ref %s %s', clsrecord, parent._g)
                member = classes

            if not parent:
                ctxt.method.array.refs.append(member)
            else:
                parent._g.refs.append(member)

    @classmethod
    def handle_ary(cls, ctxt, parent, n, node):
        array_info = ArrayInfo(object_id=ctxt.next_id(), length=len(node))
        aryrec = ArraySingleObject(array_info)
        arrays = Arrays(ctxt, aryrec)
        node._g = arrays
        ref = MemberRef(ctxt, ref=MemberReference(aryrec.object_id))
        refable = Referenceable(ctxt, arrays)
        ctxt.append_referenceable(refable)
        if not parent:
            ctxt.method.array.refs.append(ref)
        else:
            parent._g.refs.append(ref)
            # raise Exception

    @classmethod
    def handle_typ(cls, ctxt, parent, n, node):

        if cls._is_object(parent):
            nbt, npt = parent.member_info()[n]
            if nbt == bt.PRIMITIVE:
                rec = MemberPrimitiveUnTyped(typ=npt, value=node)
                ref = MemberRef(ctxt, ref=rec, typ=npt)
            else:
                tmprec = BinaryObjectString(object_id=None, value=node)
                existing_rec = ctxt.get_object(tmprec)
                if existing_rec:
                    ctxt.next_id()
                    ref = MemberRef(ctxt, ref=MemberReference(idRef=existing_rec.object_id))
                else:
                    # rec = BinaryObjectString(object_id=ctxt.next_id(), value=node)
                    tmprec.object_id = ctxt.next_id()
                    ctxt.add_object(tmprec)
                    ref = MemberRef(ctxt, ref=tmprec)
        else:
            if isinstance(node, unicode) or isinstance(node, str):
                rec = BinaryObjectString(object_id=ctxt.next_id(), value=node)
                ctxt.add_object(rec)
                ref = MemberRef(ctxt, ref=rec)
                # tmprec = BinaryObjectString(object_id=None, value=node)
                # existing_rec = ctxt.get_object(tmprec)
                # if existing_rec:
                #     ctxt.next_id()
                #     print("**** {}".format(existing_rec.object_id))
                #     ref = MemberRef(ctxt, ref=MemberReference(idRef=existing_rec.object_id))
                # else:
                #     #rec = BinaryObjectString(object_id=ctxt.next_id(), value=node)
                #     tmprec.object_id = ctxt.next_id()
                #     ctxt.add_object(tmprec)
                #     ref = MemberRef(ctxt, ref=tmprec)
            else:
                # print(node)
                raise Exception
        if not parent:
            ctxt.method.array.refs.append(ref)
        else:
            parent._g.refs.append(ref)
