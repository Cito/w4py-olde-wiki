from convert_rest import convert_rest

tests = [("""
Test
----

This is a test_
""",
          '''
<div class="document" id="test">
<h1 class="title">Test</h1>
<p>This is a <a class="reference" href="test">test</a></p>
</div>
''')]

def test_conversions():
    for rest, html in tests:
        assert convert_rest(None, rest) == html

