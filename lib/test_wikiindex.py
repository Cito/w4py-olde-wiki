import wikiindex
import os
import py

def set_match(s1, s2):
    """
    Treats lists like dictionaries when testing equality
    """
    if not len(s1) == len(s2):
        return False
    for item in s1:
        if item not in s2:
            return False
    return True

def recur_delete(dir):
    if not os.path.isdir(dir):
        os.unlink(dir)
    else:
        for fn in os.listdir(dir):
            recur_delete(os.path.join(dir, fn))
        os.rmdir(dir)


def runner(func):
    global base_dir
    base_dir = os.path.join(os.path.dirname(__file__), 'tmp')
    if os.path.exists(base_dir):
        recur_delete(base_dir)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    index = wikiindex.WikiIndex(base_dir)
    func(index)

def test_links(index):
    index.setLinks('test', ['test2', 'test3'])
    assert set_match(index.forwardLinks('test'), ['test2', 'test3'])
    assert set_match(index.backlinks('test'), [])
    assert set_match(index.backlinks('test2'), ['test'])
    index.setLinks('test2', ['test', 'blah'])
    assert set_match(index.forwardLinks('test2'), ['test', 'blah'])
    assert set_match(index.backlinks('test2'), ['test'])
    assert set_match(index.backlinks('test'), ['test2'])
    assert set_match(index.forwardLinks('test'), ['test2', 'test3'])
    assert set_match(index.forwardLinks('test'), ['test2', 'test3'])
    index.setLinks('test', ['test3'])
    assert set_match(index.forwardLinks('test'), ['test3'])
    assert set_match(index.backlinks('test2'), [])
    py.test.raises(Exception, index.setLinks, 'test', 'blah')

test_links = runner(test_links)

def test_connections(index):
    index.setConnections('test', [('test2', 'comment'), ('test3', 'attach')])
    assert set_match(index.connections('test'),
                     [('test2', 'comment'), ('test3', 'attach')])
    assert set_match(index.backConnections('test2'),
                     [('test', 'comment')])
    assert set_match(index.backConnections('test3'),
                     [('test', 'attach')])
    assert set_match(index.connections('test2'), [])
    assert set_match(index.backConnections('test'), [])
    index.setConnections('test2', [('test', 'attach')])
    assert set_match(index.connections('test2'), [('test', 'attach')])
    assert set_match(index.connections('test'),
                     [('test2', 'comment'), ('test3', 'attach')])
    assert set_match(index.backConnections('test3'),
                     [('test', 'attach')])
    index.setConnections('test', [('test3', 'attach')])
    assert set_match(index.backConnections('test3'),
                     [('test', 'attach')])
    assert set_match(index.backConnections('test2'), [])
    assert set_match(index.connections('test'), [('test3', 'attach')])

def teardown_module(mod):
    recur_delete(base_dir)

test_connections = runner(test_connections)
