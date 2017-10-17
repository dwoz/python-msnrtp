import os
import sys
from msnrtp import SingleMessage, OP_REQUEST, RequestUriHeader, ContentTypeHeader
import packetview
from msnrbf.grammar import *
import logging
from msnrbf.records import *

from remoting_types import Object, ObjArray
from system_classes import *


def pprm(rm):
    print rm.header
    if rm.method:
        print rm.method
    for ref in rm.refs:
        print(ref.record)
    print rm.end


def _normalize_record(val):
    if isinstance(val, MemberRef):
        return _normalize_record(val.record)
    if isinstance(val, Referenceable):
        return val.record
    return val


def xpopulate_value(obj):
    ctxt = MessageContext()
    method = MethodReturn(ctxt)
    method.method = BinaryMethodReturn(MessageEnum(ReturnValueInArray=True))

    arrayrec = ArraySingleObject(ArrayInfo(ctxt.next_id(), 1))
    method.array = CallArray(ctxt, array=arrayrec)

    class_info = ClassInfo(
        ctxt.next_id(),
        obj._class,
        obj.member_names(),
        len(obj.member_names()),
    )
    member_info = MemberTypeInfo(obj.member_info())
    clsrecord = ClassWithMembersAndTypes(class_info, member_info, None)

    lib = None
    if obj._library != SYSTEMLIB:
        lib_id = ctxt.has_lib_id(obj._library)
        if not lib_id:
            lib = BinaryLibrary(ctxt.next_id(), obj._library)

    clsrecord.library_id = lib.library_id
    classes = Classes(ctxt, lib, clsrecord)

    value = MemberRef(ctxt, ref=MemberReference(class_info.object_id))
    refable = Referenceable(ctxt, classes)

    # print(value.record.record)

    for n, (x, y) in enumerate(classes.member_info):
        # print(x, y)
        attrname = obj._members[n][0]
        # print(getattr(obj, attrname))

    return method


def populate_object(val):
    # print("populat_object({})".format(val))
    record = _normalize_record(val)
    if isinstance(record, BinaryObjectString):
        return record.value
    elif isinstance(record, Classes):
        objcls = Object.lookup_class(record.library_name or SYSTEMLIB, record.class_name)
        if not objcls:
            # print(record, val)
            raise Exception(record.library_name or SYSTEMLIB, record.class_name, Object._libraries)
        obj = objcls()
        for n, ((btyp, ptyp), ref) in enumerate(zip(record.member_info, record.refs)):
            name = obj._members[n][0]
            refrec = _normalize_record(ref)
            if btyp in [bt.CLASS, bt.SYSTEM_CLASS]:
                setattr(obj, name, populate_object(refrec))
            elif btyp in [bt.OBJECT_ARRAY]:
                arry = ObjArray()
                for sn, sref in enumerate(refrec.refs):
                    subrefrec = _normalize_record(sref)
                    arry.append(populate_object(sref))
                setattr(obj, name, arry)
                # populate_object(getattr(obj, name), refrec)
                pass
            else:
                # print(refrec.value)
                setattr(obj, name, refrec.value)
    else:
        return record.value
    return obj


def soreted_stream():
    from msnrbf.stream import Stream
    stream = Stream(msg.message)
    for a in stream:
        # print(a)
        pass

    def key(x):
        if hasattr(x, 'object_id'):
            return x.object_id
        return 0

    for a in sorted(stream.nodes, key=key):
        print(a)


def test_grammar_a(datadir):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

    # with open('data/response1.pkt', 'rb') as fp:
    #     resp = fp.read()

    # msg = SingleMessage.unpack(resp)
    # packetview.view(msg.message)
    # rm = RemotingMessage.unpack(msg.message)
    # assert rm.pack() == msg.message

    with open('{}/response2.pkt'.format(datadir), 'rb') as fp:
        resp = fp.read()

    msg = SingleMessage.unpack(resp)
    packetview.view(msg.message)
    a_rm = RemotingMessage.unpack(msg.message)

    assert a_rm.pack() == msg.message

    a_value = a_rm.method.array.refs[0]
    a_stream = []
    for i in a_rm.stream():
        a_stream.append(i)
        # print(i)

    print('*' * 80)
    obj = populate_object(a_value)

    b_rm = RemotingMessage.build_method_return(value=obj)
    # assert a_rm.pack() == b_rm.pack()
    b_stream = []
    for a in b_rm.stream():
        b_stream.append(a)
    for n, b_node in enumerate(b_stream):
        a_node = None
        try:
            a_node = a_stream[n]
        except:
            pass
        print('{: 4} A: {}'.format(n, a_node))
        print('{: 4} B: {}'.format(n, b_node))
        # assert a_node == b_node, (a_node, b_node)
