import sys
import lazyloader
from test_fixture import DoctestCollector, sorted, assert_error

data1 = """\
[ages]

jeanette = 72
dave = 54

[children]

jeanette = dave
dave = ian
dave = monica
"""

def test_create():
    config = lazyloader.LazyLoader()
    config.loadstring(data1, filename="data1.conf")
    assert sorted(config.keys()) == ['ages', 'children']
    assert config['ages']['jeanette'] == '72'
    assert config['ages']['dave'] == '54'
    assert config['children']['dave'] == 'monica'
    assert config['children']['jeanette'] == 'dave'
    assert config['children'].getlist('dave') == ['ian', 'monica']
    assert config['ages'].convert('jeanette', int) == 72
    assert_error(
        config['children'].convert, 'jeanette', int,
        error=ValueError,
        text_re=r'data1.conf.*line 8.*invalid literal')
    assert_error(
        config['children'].convert, 'joe', str,
        error=KeyError,
        text_re=r'joe.*section.*children')
    assert_error(
        config.__getitem__, 'child',
        error=KeyError)

data2 = """\
[children]
# Another child...
jeanette = mary
"""

def test_fold():
    config = lazyloader.LazyLoader()
    config.loadstring(data1, filename="data1.conf")
    config.loadstring(data2, filename="data2.conf")
    assert config['children']['jeanette'] == 'mary'
    assert (sorted(config['children'].getlist('jeanette'))
            == ['dave', 'mary'])
    assert config['children']['dave'] == 'monica'
    assert sorted(config.keys()) == ['ages', 'children']
    assert sorted(config['children'].keys()) == ['dave', 'jeanette']

data3 = """\
children.mary = vada
[global]
children.mary = armen
"""

data4 = """\
george = chelsea
"""

data5 = """\
[something(here!)]
test.this.out = foo
"""

def test_global():
    config = lazyloader.LazyLoader()
    config.loadstring(data1, filename="data1.conf")
    config.loadstring(data2, filename="data2.conf")
    config.loadstring(data3, filename="data3.conf")
    assert config['children']['mary'] == 'armen'
    assert config['children'].getlist('mary') == ['vada', 'armen']
    merged = lazyloader.LazyLoader()
    merged.loadstring(data4, filename="data4.conf")
    config['children'].merge(merged)
    assert config['children']['george'] == 'chelsea'
    config.merge(merged)
    assert config['george'] == 'chelsea'
    merge2 = lazyloader.LazyLoader()
    merge2.loadstring(data5, filename="data5.conf")
    assert merge2['something']['here!']['test']['this']['out'] == 'foo'
    config.merge(merge2)
    assert config['something']['here!']['test']['this']['out'] == 'foo'

collect_doctest = DoctestCollector(lazyloader)

def parse_keys(n):
    p = lazyloader.LazyLoader()
    return p._parse_keys(n)

def test_parse_section():
    data = [
        ('a', 'a'),
        ('a.b', 'a', 'b'),
        ('this  . that', 'this', 'that'),
        ('this...that', 'this', 'that'),
        ('foo_bar(foo_bar)', 'foobar', 'foo_bar'),
        ('A.(B).C', 'a', 'B', 'c'),
        ('A(B)C', 'a', 'B', 'c'),
        ('a ( b ) . c . d . ( e )', 'a', ' b ', 'c', 'd', ' e '),
        ]
    for trial in data:
        input = trial[0]
        output = list(trial[1:])
        assert parse_keys(input) == output
