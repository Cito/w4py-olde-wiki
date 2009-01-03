r"""
Provides a dictionary-like interface, where keys and values are
stored in an rfc822 formatted file.  Data is automatically saved
when keys are set.

Examples::

    >>> r = RFC822StringDict('''key: value''')
    >>> r['key']
    'value'
    >>> r.get('nothing', 'default')
    'default'
    >>> r['new'] = '1'
    >>> r.string
    'key: value'
    >>> r.save()
    >>> r.string
    'key: value\nnew: 1\n'
    >>> r['NEW']
    '1'
    >>> r['test'] = 'a\nb\n  c'
    >>> r['test']
    'a\nb\n  c'
    >>> r.save()
    >>> r2 = RFC822StringDict(r.string)
    >>> r2['test']
    'a\nb\n  c'

Note that keys are case insensitive.  All values are stored as
strings, with whitespace stripped.  If you need to store, say, an
integer, be sure to convert the value you get back.  If you pass
lazy=False to the constuctor, then you need not call .save() to
write to disk.
"""

import rfc822
from UserDict import DictMixin
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import os

class RFC822Dict(DictMixin):

    def __init__(self, filename, lazy=True):
        self.filename = filename
        self._data = None
        self.lazy = lazy
        self.dirty = False

    def __getitem__(self, key):
        if self._data is None:
            self._readData()
        value = self._data[key]
        if '\n' in value:
            lines = value.splitlines()
            for i in range(1, len(lines)):
                if lines[i].startswith('    .'):
                    lines[i] = lines[i][5:]
                elif lines[i].startswith(' .'):
                    lines[i] = lines[i][2:]
                else:
                    lines[i] = lines[i].strip()
            value = '\n'.join(lines)
        return value

    def __setitem__(self, key, value):
        value = str(value).strip()
        value = value.replace('\r', '')
        if '\n' in value:
            lines = value.splitlines()
            value = '\n'.join([lines[0]] + ['    .' + l for l in lines[1:]])
        if self._data is None:
            self._readData()
        self._data[key] = value
        self.dirty = True
        if not self.lazy:
            self._saveData()

    def __delitem__(self, key):
        if self._data is None:
            self._readData()
        del self._data[key]
        self.dirty = True
        if not self.lazy:
            self._saveData()

    def getbool(self, key, default=False):
        value = self.get(key)
        if value is None:
            return default
        if value.lower() in ['on', 'yes', '1', 'true']:
            return True
        else:
            return False

    def setbool(self, key, value):
        if value:
            self[key] = 'true'
        else:
            self[key] = 'false'

    def keys(self):
        if self._data is None:
            self._readData()
        return self._data.keys()

    def reset(self):
        self._data = None

    def save(self):
        self.dirty = False
        self._saveData()

    def _readData(self):
        if not os.path.exists(self.filename):
            self._data = rfc822.Message(StringIO())
        else:
            f = open(self.filename)
            self._data = rfc822.Message(f)
            f.close()

    def _saveData(self):
        f = open(self.filename, 'w')
        f.write(self._headerStr(self._data))
        f.close()

    def saveKeyNow(self, key):
        f = open(self.filename, 'a')
        for header in self._data.getallmatchingheaders(key):
            f.write(header)
            if not header.endswith('\n'):
                f.write('\n')
        f.close()

    def _headerStr(self, message):
        headers = message.headers
        result = StringIO()
        for header in headers:
            result.write(header)
            if not header.endswith('\n'):
                result.write('\n')
        return result.getvalue()

class RFC822StringDict(RFC822Dict):

    """
    An RFC822Dict that stores to a string, instead of a file.
    """

    def __init__(self, string, lazy=True):
        self.string = string
        self._data = None
        self.lazy = lazy

    def _readData(self):
        f = StringIO(self.string)
        self._data = rfc822.Message(f)
        f.close()

    def _saveData(self):
        self.string = self._headerStr(self._data)

    def saveKeyNow(self, key):
        pass

class metaprop(object):

    """
    A descriptor for use with objects that have a 'metadata'
    attribute that contains a dictionary like RFC822Dict.

    name:
        The name of the key in the dictionary
    default:
        The value if no key is found; this will *not* be converted
    converter:
        A function that is called with the value from the dictionary.
    unconverter:
        A function that converts a value to be saved in the dictionary
    
    """

    def __init__(self, name, default=None,
                 converter=None, unconverter=None):
        self.name = name
        if converter is not None or not hasattr(self, 'converter'):
            self.converter = converter or utf_unstr
        if unconverter is not None or not hasattr(self, 'unconverter'):
            self.unconverter = unconverter or utf_str
        if default is not None or not hasattr(self, 'default'):
            self.default = default

    def default_func(self, obj):
        return self.default

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        if obj.metadata.has_key(self.name):
            value = obj.metadata[self.name]
            if self.converter:
                return self.converter(value)
        else:
            return self.default_func(obj)

    def __set__(self, obj, value):
        if self.unconverter:
            value = self.unconverter(value)
        if value is None:
            if obj.metadata.has_key(self.name):
                del obj.metadata[self.name]
        else:
            obj.metadata[self.name] = value

    def __delete__(self, obj):
        del obj.metadata[self.name]

def utf_str(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return s

def utf_unstr(s):
    return s.decode('utf-8')
        
class metabool(metaprop):

    """
    A metaprop that coerces booleans nicely.
    """

    def __init__(self, name, default=False, delete_if_default=False):
        metaprop.__init__(self, name, default=default)
        self.delete_if_default = delete_if_default

    def converter(self, value):
        if not value:
            return False
        if value.lower().strip() == 'true':
            return True
        return False

    def unconverter(self, value):
        if self.delete_if_default and bool(value) == bool(self.default):
            return None
        if value:
            return 'True'
        else:
            return 'False'

__test__ = {
    'tests':
    """
    >>> r = RFC822StringDict('''key: value''')
    >>> r['new'] = '   '
    >>> r['new']
    ''
    >>> r.string = 'something: whatever'
    >>> r['new']
    ''
    >>> r.reset()
    >>> r['something']
    'whatever'
    """
    }





if __name__ == '__main__':
    import doctest
    doctest.testmod()
