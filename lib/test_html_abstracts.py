from html_abstracts import *
from test_fixture import ParamCollector as Collector

def test_match(input, output):
    assert find_abstract(input).strip() == output.strip()

test_match.params = tests = [
    ("""
    This is a test
    blah blah
    <p>and more</p>

    <div class="abstract">this is the abstract</div>
    and more
    """, "this is the abstract"),
    ("""
    Another test.

    And some more.

    blah blah <p class="abstract">here
there</p>stop
""", "here\nthere"),
    ("""
    <p>
    The first para.
    </p>

    <p>
    The second para
    </p>
    """, "\n    The first para.\n    "),
    ("""\nThe whole doc...\n\n""",
     """\nThe whole doc...\n\n"""),
    ]


