import iniparser
import re

def parse(s, filename='test.ini'):
    p = iniparser.BasicParser()
    p.loadstring(s, filename=filename)
    return p

def raises(sample, match):
    if isinstance(match, str):
        match = re.compile(match)
    try:
        parse(sample)
    except iniparser.ParseError, e:
        if match and not match.search(str(e)):
            raise
    else:
        assert 0, "Parsing %r should have raised an error" % sample

def test_no_section():
    raises(
        """# A file...
a=10
""", r'^Assignments can only.*')
        
def test_no_equal():
    raises(
        """[a file]
this is a test
""", r'^Lines should look like.*')

def test_bad_section():
    raises(
        """[file
""", r'^Invalid section.*')

def test_empty_section():
    raises(
        """[]
""", r'^Empty section name.*')

def test_equal_colon():
    sec = parse("""[test]
a=1:2
b: 1=3""").data['test']
    assert sec['a'] == ['1:2']
    assert sec['b'] == ['1=3']

def test_multi_section():
    data = parse("""[test]
#a=1
a=2
a=3
a=4
[test2]
a=1
""").data
    assert data['test']['a'] == ['2', '3', '4']
    assert data['test2']['a'] == ['1']

def test_continuation():
    data = parse("""[test]
a = a
   pretty
 bird
\tb=3
b=another
  line
[test2]
[test3]
c=[blah]
  [blah]""").data
    assert data['test']['a'] == ['a\npretty\nbird\nb=3']
    assert data['test']['b'] == ['another\nline']
    assert data['test3']['c'] == ['[blah]\n[blah]']
        
