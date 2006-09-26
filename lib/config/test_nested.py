import nested
NestedDict = nested.NestedDict
from pprint import pprint

from test_fixture import DoctestCollector
from test_fixture import sorted

def test_empty():
    d = NestedDict()
    d['a'] = 1
    assert d['a'] == 1
    d['a'] = 2
    assert d['a'] == 2
    src = {'c': 2}
    d['b'] = src
    assert d['b'] == src
    assert d['b'] is src
    assert d['b']['c'] == 2
    d2 = d.clone()
    assert d == d2
    d2['a'] = 3
    assert d.items() != d2.items()
    assert list(d.iteritems()) != list(d2.iteritems())
    print list(d.iteritems()), list(d2.iteritems())
    print d.configs, d2.configs
    assert d != d2
    assert repr(d) != repr(d2)
    assert d2['a'] == 3
    d3 = d.copy()
    assert d == d3
    assert d != None
    assert d != []
    assert d != object()

def test_nested():
    src = {
        'a': 1,
        'b': {
        'c': 2,
        'd': 3,
        }}
    shadow = {
        'b': {
        'c': 5,
        'e': 6,
        }}
    d = NestedDict([shadow, src])
    assert d['a'] == 1
    assert d['b']['c'] == 5
    assert d['b']['d'] == 3
    assert sorted(d.keys()) == ['a', 'b']
    assert sorted(d['b'].keys()) == ['c', 'd', 'e']
    assert isinstance(d['b'], NestedDict)
    concrete = {'a': 1, 'b': {'c': 5, 'd': 3, 'e': 6}}
    pprint(d)
    pprint(concrete)
    assert d == concrete

collect_doctest = DoctestCollector(nested)
