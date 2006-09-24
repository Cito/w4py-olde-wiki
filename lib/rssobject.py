"""
This presents an object that can read from an RSS 2.0 file, be
modified in place, then be written out to an RSS 2.0 file.
Essentially it is an object representation of the RSS file.
"""

__version__ = '0.1'

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import xml.sax
import xml.sax.handler
import xml.sax.saxutils
import time
from datetime import datetime
import os

############################################################
## Utilities
############################################################

class NoDefault:
    pass

class metasetter(object):

    def __init__(self, name, converter=None, unconverter=None,
                 default=NoDefault):
        self.name = name
        self.converter = converter
        self.unconverter = unconverter
        self.default = default

    def __get__(self, obj, type=None):
        if self.default is NoDefault:
            value = obj.metadata[self.name]
        else:
            value = obj.metadata.get(self.name, self.default)
        if self.unconverter:
            return self.unconverter(value)
        else:
            return value

    def __set__(self, obj, value):
        if self.converter:
            value = self.converter(value)
        obj.metadata[self.name] = value
        if self.name not in obj.metadataOrder:
            obj.metadataOrder.append(self.name)

    def __delete__(self, obj):
        del obj.metadata[self.name]

def formatDate(value=None):
    format = '%a, %d %b %Y %H:%M:%S GMT'
    if value is None:
        value = time.gmtime()
    if isinstance(value, (int, float, time.struct_time)):
        return time.strftime(format, value)
    elif isinstance(value, (str, unicode)):
        return value
    else:
        # @@: should also deal with time tuples
        return value.strftime(format)

def parseDate(datestr):
    return datetime(
        *time.strptime(datestr, '%a, %d %b %Y %H:%M:%S GMT')[:7])

def xmlEncode(val):
    assert isinstance(val, (str, unicode)), "Bad type: %r" % val
    return xml.sax.saxutils.escape(val, {'"': '&quot;'})

############################################################
## Public classes
############################################################

class RSS(object):

    defaultGenerator = 'rssobject.py v%s' % __version__

    def __init__(self, filename=None, text=None, metadata=None,
                 items=None, sortOrder=None):
        assert not text or not filename, (
            "You cannot provide both text and a filename/file object")
        self.items = []
        self.metadata = {}
        self.metadataOrder = []
        if filename and not isinstance(filename, (str, unicode)):
            # assume it's a file-like object
            self.parseFile(filename)
            self.filename = None
        elif filename:
            if os.path.exists(filename):
                f = open(filename)
                self.parseFile(f)
                f.close()
            self.filename = filename
        elif text:
            self.parseFile(StringIO(text))
            self.filename = None
        else:
            self.metadata = {}
            self.items = []
        self.sortOrder = sortOrder
        if metadata:
            self.metadata.update(metadata)
        if items:
            for item in items:
                self.addItem(item, len(items))

    def parseFile(self, f):
        xml.sax.parse(f, SAXHandler(self))

    def writeText(self, filename=None):
        if filename is None:
            assert self.filename, (
                "If you didn't pass a filename to the RSS constructor, "
                "you must pass one to writeText")
            filename = self.filename
        if not isinstance(filename, (str, unicode)):
            # assume it's a file-like object
            f = filename
        else:
            f = open(filename, 'w')
        f.write(str(self))
        f.close()

    def fillMetadata(self):
        metadata = self.metadata.copy()
        if not metadata.get('generator'):
            metadata['generator'] = self.defaultGenerator
        if not metadata.get('lastBuildDate'):
            metadata['lastBuildDate'] = formatDate()
        if not metadata.get('pubDate'):
            metadata['pubDate'] = formatDate()
        return metadata

    def __str__(self):
        result = StringIO()
        result.write('<?xml version="1.0"?>\n<rss version="2.0">\n'
                     '<channel>\n')
        seenItems = False
        metadata = self.fillMetadata()
        items = []
        for name in self.metadataOrder:
            if name == 'item':
                if not seenItems:
                    items.append(('item', None))
                    seenItems = True
                continue
            if name in metadata:
                items.append((name, metadata[name]))
                del metadata[name]
        items.extend(metadata.items())
        if not seenItems:
            items.append(('item', None))
        for name, value in items:
            if name == 'item':
                for i in self.items:
                    result.write(str(i))
                continue
            if isinstance(value, unicode):
                value = value.encode('UTF-8')
            result.write('<%s>%s</%s>\n'
                         % (name, xmlEncode(value), name))
        result.write('</channel>\n</rss>\n')
        return result.getvalue()

    def addItem(self, item, maxItems):
        self.items.append(item)
        self.items = self.sortItems(self.items)
        while len(self.items) > maxItems:
            self.items.pop(0)

    def sortItems(self, items):
        if not self.sortOrder:
            return items
        sorter = self.sortOrder
        reversed = False
        if isinstance(sorter, str):
            if sorter.startswith('-'):
                reversed = True
                sorter = sorter[1:]
            sorter = lambda a, b, sorter=sorter: (
                cmp(getattr(a, sorter), getattr(b, sorter)))
        items = items[:]
        items.sort(sorter)
        if reversed:
            items.reverse()
        return items

    title = metasetter('title')
    link = metasetter('link')
    description = metasetter('description')
    language = metasetter('language')
    copyright = metasetter('copyright')
    managingEditor = metasetter('managingEditor')
    webMaster = metasetter('webMaster')
    pubDate = metasetter('pubdate', formatDate)
    lastBuildDate = metasetter('lastBuildDate', formatDate)
    category = metasetter('category')
    generator = metasetter('generator')
    docs = metasetter('docs')
    cloud = metasetter('cloud')
    ttl = metasetter('ttl', str, int)
    image = metasetter('image')
    rating = metasetter('rating')
    textInput = metasetter('textInput')
    skipHours = metasetter('skipHours')
    skipdays = metasetter('skipDays')

class RSSItem(object):

    def __init__(self, metadataOrder=None, **kw):
        self.metadataOrder = metadataOrder or []
        self.metadata = kw

    def __str__(self):
        metadata = self.fillMetadata()
        result = StringIO()
        result.write('<item>\n')
        items = []
        for name in self.metadataOrder:
            if name in metadata:
                items.append((name, metadata[name]))
                del metadata[name]
        items.extend(metadata.items())
        for name, value in items:
            if isinstance(value, unicode):
                value = value.encode('UTF-8')
            result.write('<%s>%s</%s>\n' %
                         (str(name), xmlEncode(value), str(name)))
        result.write('</item>\n')
        return result.getvalue()

    def fillMetadata(self):
        metadata = self.metadata.copy()
        if metadata.get('link') and not metadata.get('guid'):
            metadata['guid'] = metadata['link']
        elif metadata.get('guid') and not metadata.get('link'):
            metadata['link'] = metadata['guid']
        if not metadata.get('pubDate'):
            metadata['pubDate'] = formatDate()
        return metadata

    title = metasetter('title')
    link = metasetter('link')
    description = metasetter('description')
    author = metasetter('author')
    category = metasetter('category')
    comments = metasetter('comments')
    enclosure = metasetter('enclosure')
    guid = metasetter('guid')
    pubDate = metasetter('pubDate')
    source = metasetter('source')

############################################################
## Parser
############################################################

class SAXHandler(xml.sax.handler.ContentHandler):

    metadataFields = ['title', 'link', 'description', 'language',
                      'copyright', 'managingEditor', 'webMaster',
                      'pubDate', 'lastBuildDate', 'category',
                      'generator', 'docs', 'cloud', 'ttl',
                      'image', 'rating', 'textInput', 'skipHours'
                      'skipDays',
                      ]

    itemMetadataFields = ['title', 'link', 'description', 'author',
                          'category', 'comments', 'enclosure', 'guid',
                          'pubDate', 'source',
                          ]

    def __init__(self, rss):
        self.rss = rss

    def startDocument(self):
        self.rss.items = []
        self.rss.metadata = {}
        self.rss.metadataOrder = []
        self.collectItem = None
        self.collectMetadata = None
        self.chars = None

    def startElement(self, name, attrs):
        if name in ('rss', 'channel'):
            return
        if name == 'item':
            assert self.chars is None, \
                   "Extra characters lying around: %r" % self.chars
            self.collectItem = {}
            return
        if self.collectItem is None:
            lookingFor = self.metadataFields
        else:
            lookingFor = self.itemMetadataFields
        assert name in lookingFor, \
               "The tag name %r is unknown (from %r)" % (name, lookingFor)
        assert not attrs, ("We can't deal with attributes at this "
                           "time (%s: %s)" % (name, attrs.items()))
        self.collectMetadata = name
        assert self.chars is None, \
               "Extra characters lying around: %r" % self.chars
        self.chars = []

    def endElement(self, name):
        if name in ('rss', 'channel'):
            return
        if name == 'item':
            assert self.collectItem, "</item> outside of <item>"
            assert self.chars is None, \
                   "Extra characters lying around: %r" % self.chars
            self.createItem()
            self.collectItem = None
            return
        if self.collectItem is None:
            metadata = self.rss.metadata
            self.rss.metadataOrder.append(name)
        else:
            metadata = self.collectItem
            metadata.setdefault('metadataOrder', []).append(name)
        assert self.collectMetadata is not None, \
               "</%s> outside of <%s>" % (name, name)
        metadata[self.collectMetadata] = ''.join(self.chars)
        self.chars = None
        self.collectMetadata = None

    def characters(self, char):
        if self.chars is None and not char.strip():
            return
        assert self.chars is not None, "Unexpected chars: %r" % char
        self.chars.append(char)

    def createItem(self):
        self.collectItem = dict([(str(v[0]), v[1])
                                 for v in
                                 self.collectItem.items()])
        item = RSSItem(**self.collectItem)
        self.rss.items.append(item)

rssAttributes = [
    'title',
    'link',
    'description',
    'language',
    'copyright',
    'managingEditor',
    'webMaster',
    'pubDate',
    'lastBuildDate',
    'category',
    'generator',
    'docs',
    'cloud',
    'ttl',
    'image',
    'rating',
    'textInput',
    'skipHours',
    'skipdays',
    ]
