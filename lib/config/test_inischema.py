from inischema import *


class Schema1(INISchema):

    number = optint()
    maybe = optbool(names=['maybe', 'or not'])
    float = optfloat()
    string = opt()
    string2 = opt()
    rep = optlist(subtype=optint())
    whatever = opt(default=5)


class Schema2(INISchema):

    a = optint()
    default = optdefault()


class Schema3(Schema2):
    pass

Schema3.add_option('default', optdefault(allow_multiple=False))
Schema3.add_option('b', optlist(subtype=optint()))


def parse_schema(schema, string, filename='test.ini'):
    if not isinstance(schema, INISchema):
        schema = schema()
    schema.loadstring(string)
    return schema


load_ini = """
number = 1
float = 1
or not = true
string = something
string2=something
rep=1
rep=5
rep=10
"""


def test_load():
    s = parse_schema(Schema1, load_ini)
    assert s.as_dict() == {
        'number': 1,
        'maybe': True,
        'float': 1.0,
        'string': 'something',
        'string2': 'something',
        'rep': [1, 5, 10]}
    assert s.number == 1
    assert s.rep == [1, 5, 10]
    assert s.whatever == 5
    assert s.string == 'something'

def test_unload():
    s = parse_schema(Schema1, load_ini)
    assert s.ini_repr() == """\
float=1.0
maybe=true
number=1
rep=1
rep=5
rep=10
string=something
string2=something
whatever=5
"""

default_ini = """
a = 1
b = 2
c = 3
"""

def test_default():
    s = parse_schema(Schema2, default_ini)
    assert s.as_dict() == {
        'a': 1,
        'default': {'b': ['2'],
                    'c': ['3']}}
    assert s.as_dict(fold_defaults=True) == {
        'a': 1,
        'b': ['2'],
        'c': ['3']}

def test_default2():
    s = parse_schema(Schema3, default_ini)
    assert s.as_dict() == {
        'a': 1,
        'b': [2],
        'default': {'c': '3'}}
    assert s.as_dict(fold_defaults=True) == {
        'a': 1, 'b': [2], 'c': '3'}

def test_gen():
    s = parse_schema(Schema2, default_ini)
    assert s.ini_repr() == "a=1\nb=2\nc=3\n"
    s.a = 2
    assert s.ini_repr() == "a=2\nb=2\nc=3\n"

def test_gen2():
    s = parse_schema(Schema3, default_ini)
    assert s.ini_repr() == "a=1\nb=2\nc=3\n"
    s.a = 2
    assert s.ini_repr() == "a=2\nb=2\nc=3\n"
