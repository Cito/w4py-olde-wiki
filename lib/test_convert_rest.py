from convert_rest import convert_rest

tests = [("""
Test
----

This is a test_
""",
          '''
<h1 class="title">Test</h1>
<div class="document" id="test">
<p>This is a <a class="wiki reference" href="test">test</a></p>
</div>
''')]

def test_conversions():
    for rest, html in tests:
        assert convert_rest(None, rest) == html

