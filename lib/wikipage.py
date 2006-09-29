"""
The Wiki module primarily exports the `WikiPage` class:
"""

import os, re, time
import shutil
from datetime import datetime, timedelta
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import propertymeta
from rfc822persist import RFC822Dict, metaprop, metabool
try:
    import Image
except ImportError:
    Image = None
import converter_registry
from html_abstracts import find_abstract
from common import *
import user

# Just make sure these are loaded:
import convert_rest
del convert_rest
import convert_html
del convert_html

__all__ = ['WikiPage']

class WikiPage(object):
    """
    WikiPage is a class to represent one page in a WikiWikiWeb [#]_.
    The page may or may not yet exist -- that is, it may not yet
    have content.

    .. [#] http://c2.com/cgi-bin/wiki

    It has the following properties and methods:

        `html`:
            A read-only property giving the HTML for the page.
            If the page does not yet have content the text
            ``"This page has not yet been created"`` is returned.
        `text`:
            The text for the page.  To save new text, simply
            assign to this property.
        .. ignore: html
        .. ignore: text
        .. ignore: setText

    """

    __metaclass__ = propertymeta.MakeProperties

    def __init__(self, wiki, dir, pageName,
        urlName=None, version=None):
        """
        Each page has a name, which is a unique identifier, for example
        ``"FrontPage"``, which identifies the page in the URL and
        for linking.
        """
        self.dir = dir
        self.wiki = wiki
        self.name = pageName
        self.version = version
        self.metadata = RFC822Dict(self.basePath + '.meta')
        self._text = None
        self._summary = None
        self._thumbnail = None
        self._connectionsDirty = False
        self._config = None
        if not self.exists() and urlName is not None:
            self.urlName = urlName
            self.title = guessTitle(urlName)

    def __repr__(self):
        text = '<WikiPage:%s ' % self.name
        if self.version:
            text += 'v.%i ' % self.version
        text += '%s>' % self.wiki.shortRepr()
        return text

    ############################################################
    ## Meta-data
    ############################################################

    def exists(self):
        """Does this page have content yet?"""
        return self.wiki.exists(self.name)

    def readOnly__get(self):
        if self.version:
            return True
        return self.wiki.config.getbool('readonly', False)

    def title__get(self):
        """Page title"""
        return self.metadata.get('title', self.name)
    def title__set(self, value):
        self.metadata['title'] = value.encode('UTF-8')

    def modifiedDate__get(self):
        """Date modified (integer timestamp)"""
        timestamp = self.metadata.get('modifiedDate', None)
        if timestamp is None:
            try:
                return datetime.fromtimestamp(
                    os.stat(self.basePath + ".txt").st_mtime)
            except (OSError, IOError):
                return None
        else:
            return datetime.fromtimestamp(int(timestamp))

    def urlName__get(self):
        urlName = self.metadata.get('urlname', '').lower()
        if urlName:
            return urlName
        elif canonicalName(self.title) == self.name:
            return guessURLName(self.title)
        else:
            return self.name

    def urlName__set(self, value):
        self.metadata['urlname'] = value

    lastChangeLog = metaprop('lastChangeLog', '')
    lastChangeUser = metaprop('lastChangeUser', '')
    creationDate = metaprop(
        'creationDate', datetime.fromtimestamp(0),
        converter=lambda v: datetime.fromtimestamp(int(v)),
        unconverter=lambda v: str(int(v)))
    hasParseErrors = metabool('hasParseErrors', delete_if_default=True)
    mimeType = metaprop('mimetype', default='text/x-restructured-text',
        converter=lambda v: v.lower())
    width = metaprop('width', default=None, converter=int)
    height = metaprop('height', default=None, converter=int)
    comments = metaprop('comments', '')
    originalFilename = metaprop('originalfilename')
    hidden = metabool('hidden')
    distributionOriginal = metabool('distributionoriginal',
        default=False, delete_if_default=True)
    relatedSummaries = metabool('relatedSummaries')
    relatedShowDates = metabool('relatedShowDates', default=True)
    relatedDateLimit = metaprop(
        'relateddatelimit',
        converter=lambda v: v and timedelta(seconds=int(v)),
        unconverter=lambda v: v and v.seconds)
    relatedEntryLimit = metaprop('relatedentrylimit', 0, converter=int)
    relatedSortField = metaprop('relatedsortfield', 'creationDate')
    authorUserID = metaprop('authoruserid', default=None, converter=int)
    # These are mostly for imported pages:
    authorName = metaprop('author', None)
    authorURL = metaprop('authorurl', None)
    authorEmail = metaprop('authoremail', None)

    def authorUser__get(self):
        id = self.authorUserID
        if not id:
            return None
        try:
            return user.manager.userForUserID(id)
        except:
            return None

    def authorUser__set(self, author):
        if author:
            self.authorUserID = author.userID()
        else:
            self.authorUserID = None

    def pageClass__get(self):
        return self.metadata.get('pageclass', 'posting')

    def pageClass__set(self, value):
        self.metadata['pageclass'] = value
        self._config = None

    def config__get(self):
        if self._config is None:
            self._config = self.wiki.config.merge_page_class(self.pageClass)
        return self._config

    def _create_atom_id(self):
        link = self.link
        if link.startswith('http://'):
            link = link[7:]
        elif link.startswith('https://'):
            link = link[8:]
        link = link.replace('#', '/')
        date_text = self.creationDate.strftime('%Y-%m-%d')
        domain, url = link.split('/', 1)
        id = '%s,%s:%s' % (domain, date_text, url)
        id = 'tag:' + id
        return id

    def atomID__get(self):
        atomID = self.metadata.get('atomid', '')
        if not atomID:
            atomID = self.metadata['atomid'] = self._create_atom_id()
            self.metadata.saveKeyNow('atomid')
        return atomID

    def atomID__set(self, value):
        atomID = self.metadata.get('atomid', '')
        if atomID:
            if atomID == value:
                return
            raise ValueError(
                "The ATOM ID for this page has already been created, "
                "and cannot be changed (it is currently %r)"
                % atomID)
        self.metadata['atomid'] = value
        self.metadata.saveKeyNow('atomid')

    def connections__set(self, connections):
        text = []
        for page, type in connections:
            text.append('%s:%s' % (type, page.name))
        self.metadata['connections'] = ','.join(text)
        self._connectionsDirty = True

    def connections__get(self):
        text = self.metadata.get('connections', '')
        text = filter(None, text.split(','))
        conn = []
        for piece in text:
            type, name = piece.split(':', 1)
            conn.append((self.wiki.page(name), type))
        return conn

    def commentPages__get(self):
        return [p for p, type in self.backConnections
                if type == 'comment']

    def backConnections__get(self):
        return self.wiki.backConnections(self)

    def updateRawMetadata(self, d):
        self.metadata.update(d)

    ############################################################
    ## Links
    ############################################################

    def basePath__get(self):
        """
        Returns the base path (sans extension) for this page.
        """
        if self.version:
            return self.archiveBasePath + '.%s' % self.version
        else:
            return os.path.join(self.dir, self.name)

    def archiveBasePath__get(self):
        base = os.path.join(self.dir, 'archive', self.name)
        return base

    def link__get(self):
        if not self.version:
            return self.wiki.linkTo(self.urlName)
        else:
            link = self.wiki.linkTo(self.urlName)
            return link + '?version=%s' % self.version

    def sourceLink__get(self):
        if not self.version:
            return self.wiki.linkTo(self.urlName, source=True)
        else:
            link = self.wiki.linkTo(self.urlName, source=True)
            return link + '?version=%s' % self.version

    def sourceLinkForMimeType(self, mimeType):
        return (self.wiki.basehref
                + self.urlName
                + self.wiki.extensionForMimeType(mimeType))

    def thumbnailLinkForMimeType(self, mimeType):
        return (self.wiki.basehref
                + self.urlName
                + '.thumb.jpg')

    ############################################################
    ## Content
    ############################################################

    def html__get(self):
        """Returns text of HTML for page (HTML fragment only)"""
        if self.exists():
            return self._subWikiLinks(self._rawHTML())
        else:
            return 'This page has not yet been created.'

    def staticHTML__get(self):
        """Returns text of HTML with links to non-existent pages
        removed (HTML fragment only)"""
        if self.exists():
            return self._subStaticLinks(self._rawHTML())
        else:
            # @@: Should this signal an error?
            return 'Page Not Found'

    def _rawHTML(self):
        if not self.exists():
            return ''
        filename = self.basePath + ".html"
        if not os.path.exists(filename):
            return self.rerender(firstRender=True)
        else:
            html = open(filename).read()
            return html

    def rerender(self, alreadyRerendered=None, firstRender=False):
        if alreadyRerendered is None:
            alreadyRerendered = []
        if self.name in alreadyRerendered:
            # To prevent loops
            return
        alreadyRerendered.append(self.name)
        if firstRender:
            origHTML = None
        else:
            origHTML = self.html
        filename = self.basePath + ".html"
        f = open(filename, 'w')
        html = self._renderHTML()
        f.write(html)
        f.close()
        if self._checkErrors(html):
            self.hasParseErrors = True
            if not self.metadata.dirty:
                print "Saving..."
                # This means we can safely update the metadata
                # immediately; otherwise we should wait for the
                # caller to call .save()
                self.metadata.save()
        origSummary = self.summary
        self._summary = self._convertSummary(self._text,
            html, self.mimeType)
        if self._summary:
            f = open(self.basePath + '.summary.html', 'w')
            f.write(self._summary)
            f.close()
        if html != origHTML or self._summary != origSummary:
            for page, type in self.connections:
                if type != 'category':
                    continue
                if page.relatedSummaries:
                    if self._summary != origSummary:
                        page.rerender(alreadyRerendered)
                else:
                    if html != origHTML:
                        page.rerender(alreadyRerendered)
        return html

    def preview(self, text, mimeType):
        """Returns an HTML preview of the text"""
        return self._subWikiLinks(self._convertText(text, mimeType))

    def _subWikiLinks(self, text):
        return self._wikiLinkRE.sub(self._subWikiLinksSubber,
            text.decode('utf-8')).encode('utf-8')

    def _subWikiLinksSubber(self, match):
        name = match.group(2)
        if name.endswith('.html'):
            name = name[:-5]
        if self.wiki.page(name).exists():
            name = self.wiki.page(name).name
            return ('<a class="wiki" href="%s%s%s%s'
                % (self.wiki.linkTo(name), match.group(3),
                    match.group(4), match.group(5)))
        else:
            return ('<span class="nowiki">'
                '%s%s%s%s?%s</span>'
                % (match.group(4), match.group(1),
                    self.wiki.linkTo(name),
                    match.group(3), match.group(5)))

    def _subStaticLinks(self, text):
        return self._wikiLinkRE.sub(self._subStaticLinksSubber, text)
    def _subStaticLinksSubber(self, match):
        name = match.group(2)
        if self.wiki.page(name).exists():
            # Normal link...
            name = self.wiki.page(name).name
            return (match.group(1)
                    + self.wiki.staticLinkTo(name)
                    + match.group(3)
                    + match.group(4)
                    + match.group(5))
        else:
            # Don't include any link at all...
            return match.group(4)

    def text__get(self):
        """
        The text of the page.  ReStructuredText is used, though the
        parsing is internal to the module.  You can assign to this
        property to save new text for the page.
        """
        if self._text is not None:
            return self._text
        if self.exists():
            f = open(self.basePath + ".txt", 'rb')
            self._text = f.read()
            f.close()
            return self._text
        else:
            return ''

    def text__set(self, text):
        """Sets the text for the page (and updates cached HTML at the
        same time)"""
        if self.mimeType.startswith('text/'):
            text = text.replace('\r', '')
            text = text.strip() + '\n'
        elif self.mimeType.startswith('image/') and Image:
            im = Image.open(StringIO(text))
            self.width = im.size[0]
            self.height = im.size[1]
            if im.format == 'GIF':
                self.mimeType = 'image/gif'
            elif im.format == 'JPEG':
                self.mimeType = 'image/jpeg'
            elif im.format == 'PNG':
                self.mimeType = 'image/png'
            else:
                assert 0, "Unknown format: %s" % im.format
            im.thumbnail((self.wiki.config.thumbWidth,
                          self.wiki.config.thumbHeight))
            out = StringIO()
            im.save(out, 'JPEG')
            self._thumbnail = out.getvalue()
        if isinstance(text, unicode):
            text = text.encode('UTF-8')
        self._text = text

    def thumbnail__get(self):
        if self._thumbnail is not None:
            return self._thumbnail
        if self._thumbnail == 0 or not self.exists():
            return None
        filename = self.basePath + '.thumb.jpg'
        if not os.path.exists(filename):
            self._thumbnail = 0
            return None
        f = open(filename, 'rb')
        self._thumbnail = f.read()
        f.close()
        return self._thumbnail

    def recreateThumbnail(self):
        if not self.mimeType.startswith('image/'):
            return
        im = Image.open(StringIO(self.text))
        im.thumbnail((self.wiki.config.thumbWidth,
                      self.wiki.config.thumbHeight))
        f = open(self.basePath + '.thumb.jpg', 'wb')
        im.save(f, 'JPEG')
        f.close()

    def summary__get(self):
        if self._summary == 0:
            return self.html
        elif self._summary is None:
            try:
                f = open(self.basePath + '.summary.html')
            except IOError:
                self._summary = 0
                return self.html
            else:
                self._summary = f.read()
                f.close()
        return self._summary

    def _renderHTML(self):
        out = StringIO()
        text = self._convertText(self.text, self.mimeType)
        if isinstance(text, unicode):
            text = text.encode('UTF-8')
        out.write(text)
        # related = self.relatedPages
        related = [] # @@ no related pages for the time being...
        if related:
            out.write('<div class="related">\n')
            for page in related:
                out.write('<div class="relatedEntry">\n')
                out.write('<h2 class="relatedTitle"><a href="%s" '
                          'class="relatedTitle">%s</a></h2>\n'
                          % (page.link, page.title))
                if self.relatedSummaries:
                    out.write(page.summary)
                else:
                    out.write(page.html)
                if self.relatedShowDates:
                    out.write('<div class="relatedDate">\n')
                    if self.relatedSortField == 'creationDate' \
                       or (self.relatedSortField == 'modifiedDate'
                           and self.modifiedDate == self.creationDate):
                        out.write('Created On: ')
                    elif self.relatedSortField == 'modifiedDate':
                        out.write('Last Modified: ')
                    else:
                        assert 0, (
                            "Unknown sort field: %r"
                            % self.relatedSortField)
                    out.write(self.formatDate(
                        getattr(page, self.relatedSortField)))
                    out.write('</div>\n')
                out.write('</div>\n')
            out.write('</div>\n')
        #keywordPages = self.keywordPages
        keywordPages = []
        if keywordPages:
            out.write('<p>Related terms:\n')
            out.write(', '.join([
                '<a href="%s">%s</a>' % (p.link, htmlEncode(p.title))
                for p in keywordPages]))
            out.write('</p>\n')
        return out.getvalue()

    def _convertText(self, text, mimeType):
        return converter_registry.convert(self, text, mimeType)

    def _convertSummary(self, text, html, mimeType):
        if mimeType in ['text/plain', 'text/html']:
            return find_abstract(html)
        else:
            if mimeType.startswith('image'):
                body = '<img src="%s" alt="%s">' % (
                    self.thumbnailLinkForMimeType(mimeType),
                    htmlEncode(self.title))
            else:
                body = htmlEncode(self.title)
            hrefAttrs = ''
            if self.comments:
                hrefAttrs += ' title="%s"' % htmlEncode(self.comments)
            return '<a href="%s"%s>%s</a>' % (
                self.link,
                hrefAttrs,
                body)

    def _commentText(self):
        if self.comments:
            return '\n<p>%s</p>\n' % self.comments
        else:
            return ''

    _checkErrorsRE = re.compile('class="system-message"')
    def _checkErrors(self, html):
        return self._checkErrorsRE.search(html)

    def save(self):
        action = 'edit'
        if self._text is None and not self.exists():
            self._text = ''
        now = int(time.time())
        if not self.exists():
            action = 'create'
            if not self.metadata.has_key('creationDate'):
                self.metadata['creationDate'] = str(now)
        self.metadata['modifiedDate'] = str(now)
        if self._text is not None:
            f = open(self.basePath + ".txt", 'wb')
            f.write(self._text or '')
            f.close()
        if self._thumbnail is not None:
            f = open(self.basePath + '.thumb.jpg', 'wb')
            f.write(self._thumbnail)
            f.close()
        f = open(self.basePath + ".html", 'w')
        html = self._renderHTML()
        f.write(html)
        f.close()
        self._summary = self._convertSummary(self._text, html,
                                             self.mimeType)
        if self._summary:
            f = open(self.basePath + '.summary.html', 'w')
            f.write(self._summary)
            f.close()
        self.hasParseErrors = self._checkErrors(html)
        self._text = None
        self.metadata.save()
        self.backup()
        self.wiki.notifyChange(self, action=action)
        for page, type in self.connections:
            page.rerender()
            self.wiki.notifyChange(page, 'related', relatedPage=self,
                                   type=type)

    def backup(self):
        """
        Create an archived version of this page.
        """
        dir = os.path.dirname(self.archiveBasePath)
        if not os.path.exists(dir):
            os.mkdir(dir)
        version = 1
        while os.path.exists('%s.%i.txt' % (self.archiveBasePath, version)):
            version += 1
        exts =  ['.txt', '.meta', '.html', '.thumb.jpg', '.summary.html']
        for ext in exts:
            if os.path.exists(self.basePath + ext):
                shutil.copyfile(self.basePath + ext,
                    '%s.%i%s' % (self.archiveBasePath, version, ext))

    def delete(self, versions=None):
        """
        Delete (archived) versions of this page.
        """
        dir = os.path.dirname(self.archiveBasePath)
        maxVersion = 1
        while os.path.exists('%s.%i.txt' % (self.archiveBasePath, maxVersion)):
            maxVersion += 1
        if not versions:
            versions = [maxVersion-1]
        users = {}
        exts =  ['.txt', '.meta', '.html', '.thumb.jpg', '.summary.html']
        oldVersion = newVersion = 1
        while oldVersion < maxVersion:
            if oldVersion in versions:
                username = self.__class__(self.wiki, self.dir, self.name,
                    version=oldVersion).lastChangeUser
                if username not in users:
                    users[username] = True
                for ext in exts:
                    try:
                        os.remove('%s.%i%s' % (self.archiveBasePath, oldVersion, ext))
                    except:
                        pass
                newVersion -= 1
            else:
                if newVersion != oldVersion:
                    for ext in exts:
                        try:
                            os.rename('%s.%i%s' % (self.archiveBasePath, oldVersion, ext),
                                '%s.%i%s' % (self.archiveBasePath, newVersion, ext))
                        except:
                            pass
            newVersion += 1
            oldVersion += 1
        if newVersion == 1:
            for ext in exts:
                try:
                    os.remove(os.path.join(self.dir, self.name + ext))
                except:
                    pass
        elif maxVersion-1 in versions:
            for ext in exts:
                try:
                    shutil.copyfile('%s.%i%s' % (self.archiveBasePath, newVersion-1, ext),
                        os.path.join(self.dir, self.name + ext))
                except:
                    pass
        return users.keys()


    ############################################################
    ## Linking and relations
    ############################################################

    _wikiLinkRE = re.compile(
        r'(<a[^>]* href=["\'])([\-a-z0-9]+(?:[\.\-a-z0-9]+)?)(["\'].*?>)(.*?)(</a>)',
        re.I+re.S)
    def wikiLinks(self):
        """The names of all the wiki pages that this page links to."""
        if self.name == 'index':
            # add some faked links so that these do not appear as orphaned
            results = { 'index': None, 'thiswiki': None, 'wikimarkup': None }
        else:
            results = {}
        for match in self._wikiLinkRE.finditer(self._rawHTML()):
            name = match.group(2)
            if self.wiki.page(name).exists():
                name = self.wiki.page(name).name
            if name.endswith('.html'):
                name = name[:-5]
            results[name] = None
        return results.keys()

    def backlinks__get(self):
        return self.wiki.backlinks(self)

    def relatedPages__get(self):
        field = self.relatedSortField
        entryLimit = self.relatedEntryLimit
        if self.relatedDateLimit:
            dateLimit = datetime.now() - self.relatedDateLimit
        else:
            dateLimit = None
        pages = self.wiki.relatedPages(self)
        pages.sort(lambda a, b, field=field:
                   -cmp(getattr(a, field), getattr(b, field)))
        limitedPages = []
        for i, page in enumerate(pages):
            if entryLimit:
                if i >= entryLimit:
                    if not dateLimit or getattr(page, field) < dateLimit:
                        continue
            elif dateLimit:
                if getattr(page, field) < dateLimit:
                    continue
            limitedPages.append(page)
        return limitedPages

    def versions(self):
        result = []
        version = 1
        while os.path.exists('%s.%i.txt' % (self.archiveBasePath, version)):
            result.append(
                self.__class__(self.wiki, self.dir, self.name, version=version))
            version += 1
        return result

    ############################################################
    ## Searching
    ############################################################

    def searchMatches(self, text):
        return self.searchTitleMatches(text) \
               or self.text.lower().find(text.lower()) != -1

    def searchTitleMatches(self, text):
        return self.title.lower().find(text.lower()) != -1

    def searchNameMatches(self, text):
        return self.name.lower().find(canonicalName(text)) != -1

    def searchSegment(self, text, length=100):
        html = self.html
        html = re.sub(r'<.*?>', '', html)
        pos = html.lower().find(text.lower())
        prefix = postfix = '...'
        start = int(pos-(length/2))
        end = int(pos+(length/2))
        if pos == -1 or start < 0:
            start = 0
            end = length
            prefix = ''
        elif end > len(html):
            start = len(html)-length
            postfix = ''
        return (prefix + html[start:end] + postfix)

    ############################################################
    ## Misc
    ############################################################

    def formatDate(self, date):
        return date.strftime('%c')


