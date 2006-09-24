from py.test.collect import Collector
from py.test import Item
import doctest24 as doctest
import sys
from cStringIO import StringIO
import types

class Dummy(object):

    def __init__(self, **kw):
        for name, value in kw.items():
            if name.startswith('method_'):
                name = name[len('method_'):]
                value = DummyMethod(value)
            setattr(self, name, value)

class DummyMethod(object):

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self, *args, **kw):
        return self.return_value

class DoctestCollector(Collector):

    def __init__(self, extpy_or_module):
        if isinstance(extpy_or_module, types.ModuleType):
            self.module = extpy_or_module
            self.extpy = None
        else:
            self.extpy = extpy_or_module
            self.module = self.extpy.getpymodule()

    def __call__(self, extpy):
        # we throw it away, because this has been set up to explicitly
        # check another module; maybe this isn't clean
        if self.extpy is None:
            self.extpy = extpy
        return self

    def __iter__(self):
        finder = doctest.DocTestFinder()
        tests = finder.find(self.module)
        for t in tests:
            yield DoctestItem(self.extpy, t)

class DoctestItem(Item):

    def __init__(self, extpy, doctestitem, *args):
        self.extpy = extpy
        self.doctestitem = doctestitem
        self.name = extpy.basename
        self.args = args

    def execute(self, driver):
        runner = doctest.DocTestRunner()
        teardown = None
        #driver.setup_path(self.extpy)
        #target, teardown = driver.setup_method(self.extpy)
        try:
            (failed, tried), run_output = capture_stdout(runner.run, self.doctestitem)
            if failed:
                raise self.Failed(msg=run_output, tbindex=-2)
        finally:
            if teardown:
                teardown(target)

def capture_stdout(func, *args, **kw):
    newstdout = StringIO()
    oldstdout = sys.stdout
    sys.stdout = newstdout
    try:
        result = func(*args, **kw)
    finally:
        sys.stdout = oldstdout
    return result, newstdout.getvalue()

def assert_error(func, *args, **kw):
    kw.setdefault('error', Exception)
    kw.setdefault('text_re', None)
    error = kw.pop('error')
    text_re = kw.pop('text_re')
    if text_re and isinstance(text_re, str):
        import re
        real_text_re = re.compile(text_re, re.S)
    else:
        real_text_re = text_re
    try:
        value = func(*args, **kw)
    except error, e:
        if real_text_re and not real_text_re.search(str(e)):
            assert False, (
                "Exception did not match pattern; exception:\n  %r;\n"
                "pattern:\n  %r"
                % (str(e), text_re))
    except Exception, e:
        assert False, (
            "Exception type %s should have been raised; got %s instead (%s)"
            % (error, e.__class__, e))
    else:
        assert False, (
            "Exception was expected, instead successfully returned %r"
            % (value))

def sorted(l):
    l = list(l)
    l.sort()
    return l
