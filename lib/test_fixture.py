from py.test.collect import Collector
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

class ParamCollector(Collector):

    def collect_function(self, extpy):
        if not extpy.check(func=1, basestarts='test_'):
            return
        func = extpy.resolve()
        if hasattr(func, 'params'):
            params = func.params
            for i, param in enumerate(params):
                item = self.Item(extpy, *param)
                item.name += '.%i' % i
                yield item
        else:
            yield extpy

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

class DoctestItem:

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
