from common import htmlEncode
import convert_html
import test_fixture

dummy_page = test_fixture.Dummy(
    method_sourceLinkForMimeType='source_link',
    width=10, height=20)


def test_text():
    for v in ['a', '1 < 2', 'me&you']:
        converted = convert_html.convert_text(dummy_page,
                                              v, 'text/plain')
        assert htmlEncode(v) in converted
        assert 'source_link' in converted

def test_application():
    converted = convert_html.convert_application(dummy_page, None, 'text/whatever')
    assert 'source_link' in converted

def test_convert_image():
    converted = convert_html.convert_image(dummy_page, None, 'image/whatever')
    assert 'width="10"' in converted
    assert 'height="20"' in converted
    assert 'source_link' in converted

# @@: should test convert_python
