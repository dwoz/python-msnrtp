from msnrbf.enum import primitive_type as pt
from msnrbf.enum import binary_type as bt
from msnrbf.structures import ClassTypeInfo
from msnrbf.types import *


SYSTEMLIB = 'SYSTEMLIB'


def with_metaclass(mcls):
    '''
    Define metaclass on class (py 2 and 3 compaitble)
    '''
    def decorator(cls):
        body = vars(cls).copy()
        # clean out class body
        body.pop('__dict__', None)
        body.pop('__weakref__', None)
        return mcls(cls.__name__, cls.__bases__, body)
    return decorator


class ClassMember(object):
    '''
    ClassMember acts as both an attribute definition holder, and the descriptor
    which provides instance attributes.
    '''

    def __init__(self, name=None, btype=None, ptype=None, default=None, _attrname=None, _obj=None):
        self.name = name
        self._btype = btype
        self._ptype = ptype
        self._attrname = _attrname
        self._value = default
        self._obj = _obj

    def __get__(self, obj, cls, *args, **kwargs):
        if cls:
            if self.name not in obj._data:
                obj._data[self.name] = self.build_val()
            return obj._data[self.name]
        return self

    def __set__(self, obj, value, *args, **kwargs):
        if obj:
            obj._data[self.name] = value

    def set_obj(self, obj):
        self._obj = obj

    def build_val(self):
        if self._val_is_class():
            cls = self._lookup_class_cls()
            if not cls:
                msg = "{}".format(self._ptype)
                raise Exception(msg)
            return cls()
        if self._val_is_array():
            return []
        return self._value

    def _lookup_class_cls(self):
        if self._obj is None:
            raise Exception("Provide an obj via set_obj method first")
        for lname in self._obj._libraries:
            for cname in self._obj._libraries[lname]:
                if cname == self._ptype:
                    return self._obj._libraries[lname][cname]

    def _val_is_class(self):
        return self._btype in [bt.CLASS]

    def _val_is_system_class(self):
        return self._btype in [bt.SYSTEM_CLASS]

    def _val_is_array(self):
        return self._btype in [bt.OBJECT_ARRAY]

    def _val_is_primitive(self):
        return self._btype == bt.PRIMITIVE

    def member_info(self):
        if self._val_is_primitive():
            return (bt.BinaryTypeEnum(self._btype), pt.PrimitiveTypeEnum(self._ptype))
        elif self._val_is_system_class():
            return (bt.BinaryTypeEnum(self._btype), LengthPrefixedString(self._ptype))
        elif self._val_is_class():
            return (bt.BinaryTypeEnum(self._btype), ClassTypeInfo(self._ptype, None))
        else:
            return (bt.BinaryTypeEnum(self._btype), None)


def _obj__new__(factory, obj, cls, *args, **kwargs):
    '''
    __new__ method of new object classes

    factory and objname arguments are curried from the factroy at object
    creation time.
    '''
    newcls = super(obj, cls).__new__(cls)
    newcls._data = {}
    return newcls


def _obj__init__(factory, obj, self, *args, **kwargs):
    '''
    __init__ method of new object classes

    factory and objname arguments are curried from the factroy at object
    creation time.
    '''
    pass


def _obj_register_members(cls, newcls):
    '_register_members method of new object classes'
    for name, descriptor in newcls._members:
        # if name in kwargs:
        #     members._members[name]._value = kwargs[name]
        descriptor.set_obj(cls)
        descriptor.build_val()
        setattr(newcls, name, descriptor)


def _obj_register_class(cls, newcls):
    '_register_class method of new object classes'
    cls._register_library(newcls)
    if newcls._class not in cls._libraries[newcls._library]:
        cls._libraries[newcls._library][newcls._class] = newcls
    cls._register_members(newcls)
    if not hasattr(newcls, '_referenceable'):
        newcls._referenceable = True


def _obj_register_library(cls, newcls):
    '_register_libray method of new object classes'
    if newcls._library not in cls._libraries:
        cls._libraries[newcls._library] = {}


def _obj_lookup_class(cls, libname, clsname):
    if cls is None:
        raise Exception("Provide an obj via set_obj method first")
    if libname in cls._libraries:
        if clsname in cls._libraries[libname]:
            return cls._libraries[libname][clsname]


def _obj_member_info(cls):
    if len(cls.mro()) > 2:
        return [x[1].member_info() for x in cls._members]
    else:
        raise Exception("Method must be called on subclass")


def _obj_member_names(cls):
    if len(cls.mro()) > 2:
        return [x[1].name for x in cls._members]
    else:
        raise Exception("Method must be called on subclass")


def _obj_is_system_class(cls):
    return cls._library == SYSTEMLIB


def _obj_hash_values(self):
    data = {}
    for name, descriptior in self._members:
        data[name] = getattr(self, name)
    return hash(frozenset(data.items()))


class ObjectFactory(object):
    '''
    Creates remoting objects and remembers them for later introspection.

    Each remoting object created is a namespace for classes and modules of a
    remoting service. The factory remembers all objects it creates. Generally,
    there should only ever be the need for one factory instance and one object
    class.
    '''

    def __init__(self, objects=None, watchers=None):
        self.objects = objects
        if self.objects is None:
            self.objects = {}

    def __call__(self, name):
        factory = self

        def __new__(cls, *args, **kwargs):
            obj = factory.objects[name]
            return _obj__new__(factory, obj, cls, *args, **kwargs)

        def __init__(self, *args, **kwargs):
            obj = factory.objects[name]
            _obj__init__(factory, obj, self, *args, **kwargs)

        clsdata = {
            '__new__': __new__,
            '__init__': __init__,
            '_name': name,
            '_watcher': None,
            '_factory': self,
            '_libraries': {},
            '_register_members': classmethod(_obj_register_members),
            '_register_class': classmethod(_obj_register_class),
            '_register_library': classmethod(_obj_register_library),
            'lookup_class': classmethod(_obj_lookup_class),
            'member_info': classmethod(_obj_member_info),
            'member_names': classmethod(_obj_member_names),
            'is_system_class': classmethod(_obj_is_system_class),
            'hash_values': _obj_hash_values,
        }
        base_cls = type(name, (object,), clsdata)
        watcher = self._watcher_factory(base_cls)
        cls = with_metaclass(watcher)(base_cls)
        self.objects[name] = cls
        return cls

    def _watcher_factory(self, obj):
        def __init__(cls, name, bases, clsdict):
            if len(cls.mro()) > 2:
                obj._register_class(cls)
            else:
                pass
            super(type, cls).__init__(name, bases, clsdict)
        typdata = {
            '__init__': __init__,
        }
        return type(obj.__name__, (type,), typdata)


class ObjArray(object):

    def __init__(self, nodes=None):
        self._nodes = nodes
        if self._nodes is None:
            self._nodes = []

    def __getitem__(self, idx):
        return self._nodes[idx]

    def __setitem__(self, idx, val):
        self._nodes[idx] = val

    def __iter__(self):
        return iter(self._nodes)

    def __len__(self):
        return len(self._nodes)

    def append(self, val):
        self._nodes.append(val)


object_factory = ObjectFactory()
Object = object_factory('Object')
