"""
propertymeta.py
Ian Bicking <ianb@colorstudy.com>
"""

class MakeProperties(type):
    """
    A metaclass that runs `makeProperties` on your classes.  Use
    it like::

        class MyClass(object):

            __metaclass__ = MakeProperties

            def attr__get(self):
                return blah

    ``attr__get`` will be magically turned into a property.
    """

    def __new__(mcs, className, bases, d):
        makeProperties(d)
        return type.__new__(mcs, className, bases, d)

def makeProperties(obj):
    """
    This function takes a dictionary of methods and finds
    methods named like:
    * attr__get
    * attr__set
    * attr__del
    * attr__doc
    Except for attr__doc, these should be methods.  It
    then creates properties from these methods, like
    property(attr__get, attr__set, attr__del, attr__doc).
    Missing methods are okay.

    It also takes methods like:
    * attr__class
    Which is turned into a class method.

    You can pass either an object or a dictionary in, where
    the dictionary is obj.__dict__ (the dictionary interface
    allows you to run this on yet-to-be-created objects,
    like in a metaclass `__new__` method).
    """

    if isinstance(obj, dict):
        def setFunc(var, value):
            obj[var] = value
        d = obj
    else:
        def setFunc(var, value):
            setattr(obj, var, value)
        d = obj.__dict__

    props = {}
    for var, value in d.items():
        if var.endswith('__set'):
            props.setdefault(var[:-5], {})['set'] = value
        elif var.endswith('__get'):
            props.setdefault(var[:-5], {})['get'] = value
        elif var.endswith('__del'):
            props.setdefault(var[:-5], {})['del'] = value
        elif var.endswith('__doc'):
            props.setdefault(var[:-5], {})['doc'] = value
        elif var.endswith('__class'):
            setFunc(var[:-7], classmethod(value))

    for var, setters in props.items():
        if len(setters) == 1 and setters.has_key('doc'):
            continue
        if d.has_key(var):
            continue
        setFunc(var,
                property(setters.get('get'), setters.get('set'),
                         setters.get('del'), setters.get('doc')))


def unmakeProperties(obj):
    """
    Accompanies makeProperties -- when you dynamically modify a
    class, adding or removing getters and setters, the property
    will persist (unless you delete the property itself).  This
    goes through and gets rid of properties where any of its
    methods (get, set, delete) have been removed.
    """
    
    if isinstance(obj, dict):
        def delFunc(obj, var):
            del obj[var]
        d = obj
    else:
        delFunc = delattr
        d = obj.__dict__

    for var, value in d.items():
        if isinstance(value, property):
            for prop in [value.fget, value.fset, value.fdel]:
                if prop and not d.has_key(prop.__name__):
                    delFunc(obj, var)
                    break
