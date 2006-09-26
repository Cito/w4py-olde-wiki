import lazyiniparser

def parse(s, filename='test.ini'):
    p = lazyiniparser.LazyINIParser()
    p.loadstring(s, filename=filename)
    return p.configuration


data = """\
# a test
[section 1]
a = 2
a2 = 3
# one more...
a = 4
"""

def test_simple():
    c = parse(data)
    assert len(c.sections) == 1
    assert c.sections[0].name == 'section 1'
    assert c.sections[0].comment == 'a test'
    items = c.sections[0].items
    assert [i.name for i in items] == ['a', 'a2', 'a']
    assert [i.lineno for i in items] == [3, 4, 6]
    assert c.source() == data
