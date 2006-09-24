import test_wiki
import os
import wiki
import rfc822persist
from test_fixture import DoctestCollector
import re

setup_module = test_wiki.setup_module

def test_page():
    conf = test_wiki.make_conf()
    w = wiki.GlobalWiki(conf).site('test.domain')
    page = w.page('test1')
    assert not page.exists()
    assert not page.readOnly
    assert page.title == 'Test1'
    assert page.text == ''
    page.title = 'Test 1'
    assert page.title == 'Test 1'
    # Haven't saved yet:
    assert not page.exists()
    assert page.modifiedDate is None
    page.text = 'A test\n'
    assert page.text == 'A test\n'
    assert not page.exists()
    page.save()
    assert page.modifiedDate is not None
    assert page.text == 'A test\n'
    assert 'A test' in page.html
    assert page.exists()
    assert page.creationDate == page.modifiedDate
    assert not page.hasParseErrors
    assert page.mimeType == 'text/x-restructured-text'
    assert page.width is None
    assert page.height is None
    assert page.comments == ''
    assert not page.originalFilename
    assert not page.hidden
    assert not page.distributionOriginal
    assert page.basePath == os.path.join(w.basepath, 'test1')
    assert page.archiveBasePath == os.path.join(w.basepath, 'archive', 'test1')
    # None = current version
    assert page.version is None
    assert page.link == 'http://test.domain/test1.html'
    assert page.sourceLink == 'http://test.domain/test1.txt'
    assert page.sourceLinkForMimeType('image/jpeg') == 'http://test.domain/test1.jpg'
    assert page.thumbnailLinkForMimeType('image/jpeg') == 'http://test.domain/test1.thumb.jpg'
    assert 'A test' in page.staticHTML
    assert 'Another test' in page.preview('Another test', 'text/x-restructured-text')
    assert 'Test 1' in page.summary
    assert page.link in page.summary
    assert page.wikiLinks() == []
    assert page.backlinks == []
    versions = page.versions()
    assert len(versions) == 1
    assert versions[0].version == 1
    assert versions[0].name == page.name
    assert not page.searchMatches('whatever')
    assert page.searchMatches('test')
    assert page.searchTitleMatches('1')
    assert page.searchNameMatches('1')
    assert 'A test' in page.searchSegment('test')

def test_relations():
    conf = test_wiki.make_conf()
    w = wiki.GlobalWiki(conf).site('test.domain')
    page = w.page('test3')
    page.text = 'whatever'
    page.save()
    page.text = 'link to test4_ there'
    page.save()
    assert len(page.versions()) == 2
    assert page.versions()[0].text != page.text
    assert page.versions()[-1].text == page.text
    links = page.wikiLinks()
    assert len(links) == 1
    assert links[0] == 'test4'
    page2 = w.page('test4')
    back = page2.backlinks
    assert len(back) == 1
    assert back[0].name == 'test3'
    page2.connections = [(page, 'comment')]
    page2.save()
    p2conn = page2.connections
    assert len(p2conn) == 1
    assert p2conn[0][1] == 'comment'
    assert p2conn[0][0].name == 'test3'
    pconn = page.backConnections
    assert len(pconn) == 1
    assert pconn[0][1] == 'comment'
    assert pconn[0][0].name == 'test4'
    page.text = 'Link to <a href="test5.html">test3</a>'
    page.mimeType = 'text/html'
    page.save()
    assert page2.backlinks == []
    assert page.wikiLinks() == ['test5']
    page5 = w.page('test5')
    back = page5.backlinks
    assert len(back) == 1
    assert back[0].name == 'test3'
    print page.html
    assert re.search(r'<a [^>]*href="[^"]*test5.html">', page.html)
    assert 'class="nowiki"' in page.html
    assert 'class="wiki"' not in page.html
    page5.text = 'test'
    page5.save()
    print page.html
    assert re.search(r'<a [^>]*href="[^"]*test5.html">', page.html)
    assert 'class="nowiki"' not in page.html
    assert 'class="wiki"' in page.html

def test_error():
    conf = test_wiki.make_conf()
    w = wiki.GlobalWiki(conf).site('test.domain')
    page = w.page('badtest')
    page.text = 'A test__!_\n\nthis is a test'
    page.save()
    assert page.hasParseErrors
    assert 'system-messages' in page.html
    assert 'Anonymous hyperlink mismatch' in page.html

collect_doctest = DoctestCollector(rfc822persist)
