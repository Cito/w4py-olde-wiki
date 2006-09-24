import os
import shutil
import wiki
from wikiconfig import WikiConfig

def make_conf():
    conf = WikiConfig()
    conf.load(os.path.join(os.path.dirname(__file__), "test.conf"))
    return conf

def setup_module(module):
    shutil.rmtree(os.path.join(os.path.dirname(__file__), 'test_data'), True)
    os.mkdir(os.path.join(os.path.dirname(__file__), 'test_data'))

def test_global():
    conf = make_conf()
    g = wiki.GlobalWiki(conf)
    s = g.site('test.domain')
    assert s.globalWiki is g
    assert s.canonical is None
    assert g.config['testval'] == 'A'
    assert g.config['testval2'] == 'None'
    assert s.config['testval'] == 'B'
    assert s.config['testval2'] == 'A'
    assert s.basepath.endswith(os.sep+'test.domain')
    assert s.basepath.startswith(g.root)
    s2 = g.site('test.virtual')
    assert s2.globalWiki is g
    assert s2.canonical is s
    assert s2.config['testval'] == 'C'
    assert s2.config['testval2'] == 'A'

def test_wiki():
    conf = make_conf()
    w = wiki.GlobalWiki(conf).site('test.domain')
    assert w.filenameForName('test').endswith('test.txt')
    assert not w.exists('test')
    assert w.search('test') == []
    assert w.searchTitles('test') == []
    assert w.searchNames('test') == []
    dist = set(('thiswiki',))
    assert dist.issuperset(p.name for p in w.recentPages())
    assert dist.issuperset(p.name for p in w.orphanPages())
    assert dist.issuperset(p.name for p in w.allPages())
    assert w.linkTo('test') == 'http://test.domain/test.html'
    assert w.linkTo('test.link') == 'http://test.domain/test.link'
    assert w.linkTo('test', source=True) == 'http://test.domain/test.txt'
    assert w.staticLinkTo('test') == 'http://static.domain/test.html'
    assert w.staticLinkTo('test.link') == 'http://static.domain/test.link'
    assert w.canonicalDomain == w.domain
    w.rebuildHTML()
    w.rebuildStatic()
    w.recreateThumbnails()
    w.rebuildIndex()
    w.checkDistributionFiles()
    rss = str(w.syndicateRecentChanges)
    assert rss.startswith('<?xml')
    assert rss.find('<channel>') != -1
    for mime_type, ext in [('text/plain', '.txt'),
                           ('image/jpeg', '.jpg'),
                           ('text/x-restructured-text', '.txt'),
                           ('text/html', '.html'),
                           ]:
        assert w.extensionForMimeType(mime_type) == ext
