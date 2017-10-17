from msnrbf.enum import primitive_type as pt
from msnrbf.enum import binary_type as bt
from msnrbf.records import BinaryObjectString, ObjectNull
from msnrbf.types import Int32, LengthPrefixedString
from remoting_types import SYSTEMLIB, Object, ClassMember


class RemotingException(Object):
    _library = SYSTEMLIB
    _class = 'System.Runtime.Remoting.RemotingException'
    _members = (
        (
            'class_name',
            ClassMember(
                'ClassName',
                bt.STRING,
                default='System.Runtime.Remoting.RemotingException')
        ),
        (
            'message',
            ClassMember('Message', bt.STRING)
        ),
        (
            'help_url',
            ClassMember('HelpUrl', bt.STRING)
        ),
        (
            'inner_exception',
            ClassMember('InnerException', bt.STRING, 'System.Exception')
        ),
        (
            'stack_trace_string',
            ClassMember('StackTraceString', bt.STRING)
        ),
        (
            'remote_stack_trace_string',
            ClassMember('RemoteStackTraceString', bt.STRING)
        ),
        (
            'remote_stack_index',
            ClassMember('RemoteStackIndex', bt.PRIMITIVE, pt.INT32, 0)
        ),
        (
            'exception_method',
            ClassMember('ExceptionMethod', bt.STRING),
        ),
        (
            'hresult',
            ClassMember('HResult', bt.PRIMITIVE, pt.INT32, -2146233077),
        ),
        (
            'source',
            ClassMember('Source', bt.STRING)
        ),
    )


class CompareInfo(Object):
    _library = SYSTEMLIB
    _class = 'System.Globalization.CompareInfo'
    _members = (
        ('win32LCID', ClassMember('win32LCID', bt.PRIMITIVE, pt.INT32)),
        ('culture', ClassMember('culture', bt.PRIMITIVE, pt.INT32)),
    )


class TextInfo(Object):
    _library = SYSTEMLIB
    _class = 'System.Globalization.TextInfo'
    _members = (
        ('m_nDataItem', ClassMember('m_nDataItem', bt.PRIMITIVE, pt.INT32)),
        (
            'm_userUserOverride',
            ClassMember('m_userUserOverride', bt.PRIMITIVE, pt.BOOLEAN)
        ),
        ('m_win32LangID', ClassMember('m_win32LangID', bt.PRIMITIVE, pt.INT32)),
    )


class CaseInsensativeComparer(Object):
    _library = SYSTEMLIB
    _class = 'System.Collections.CaseInsensitiveComparer'
    # _class = 'System.Collections.CaseInsensitiveCompare'
    _members = [
        (
            'm_compareInfo',
            ClassMember(
                'm_compareInfo',
                bt.SYSTEM_CLASS,
                'System.Globalization.CompareInfo'
            )
        ),
    ]


class CaseInsensativeHashCodeProvider(Object):
    _library = SYSTEMLIB
    _class = 'System.Collections.CaseInsensitiveHashCodeProvider'
    _members = (
        ('m_text', ClassMember('m_text', bt.SYSTEM_CLASS, 'System.Globalization.TextInfo')),
    )


class Hashtable(Object):
    _library = SYSTEMLIB
    _class = 'System.Collections.Hashtable'
    _members = (
        (
            'load_factor',
            ClassMember(
                'LoadFactor', bt.PRIMITIVE, pt.SINGLE,
                default=0.72000002861
            )
        ),
        (
            'version',
            ClassMember(
                'Version', bt.PRIMITIVE, pt.INT32,
                default=2
            )
        ),
        (
            'comparer',
            ClassMember(
                'Comparer',
                bt.SYSTEM_CLASS,
                'System.Collections.CaseInsensitiveComparer'
            )
        ),
        (
            'hash_code_provider',
            ClassMember(
                'HashCodeProvider',
                bt.SYSTEM_CLASS,
                'System.Collections.CaseInsensitiveHashCodeProvider'
            )
        ),
        (
            'hash_size', ClassMember('HashSize', bt.PRIMITIVE, pt.INT32)
        ),
        (
            'keys', ClassMember('Keys', bt.OBJECT_ARRAY)
        ),
        (
            'values', ClassMember('Values', bt.OBJECT_ARRAY)
        ),
    )
