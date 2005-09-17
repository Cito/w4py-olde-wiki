import os
import wikipage
import rssobject
import propertymeta
import threading
import wikiindex
try:
    import pooledtemplate
except ImportError:
    pooledtemplate = None
import mimetypes
import filequeue
import sshclient
import ftpclient
import warnings
from common import canonicalName
import rfc822persist
from WebKit.HTTPExceptions import *

warnings.filterwarnings(
    'ignore',
    message='tempnam is a potential security risk to your program')

class GlobalWiki(object):

    def __init__(self, config):
        """
        root is the path to root storage location for Wiki sites.
        This class will make any necessary subdirectories or other
        structure.
        """
        self.config = config
        self.root = os.path.join(os.path.dirname(__file__), config['basepath'])
        assert os.path.exists(self.root), "Nonexistant root: %r" % self.root
        self.specialNames = {}
        self.cachedWikis = {}
        self.cacheLock = threading.Lock()
        self.allSites = {}

    def site(self, domain):
        """
        Retrieves the Wiki that corresponds to this domain.
        Currently by looking for a similarly named subdirectory
        (creating directory if necessary).
        """
        assert '/' not in domain
        # We go through all this trouble to make sure Wikis are
        # unique per domain, and that they have a link to their
        # canonical form if necessary, which is also unique; all
        # done in a threadsafe manner.
        try:
            return self.cachedWikis[domain]
        except KeyError:
            self.cacheLock.acquire()
            try:
                try:
                    return self.cachedWikis[domain]
                except KeyError:
                    return self._makeSite(domain)
            finally:
                self.cacheLock.release()

    def _makeSite(self, domain):
        config = self.config.clone()
        try:
            local_config = self.config['vhost'][domain]
        except KeyError:
            raise HTTPNotFound, "The domain %s is unknown" % domain
        canonical_domain = local_config.get('canonical')
        if canonical_domain is not None and canonical_domain != domain:
            canonical_config = self.config['vhost'][canonical_domain]
            config.merge(canonical_config)
            try:
                canonical = self.cachedWikis[canonical_domain]
            except KeyError:
                canonical = self._makeSite(canonical_domain)
                self.cachedWikis[canonical_domain] = canonical
        else:
            canonical = None
        config.merge(local_config)
        result = Wiki(globalWiki=self, config=config,
                      canonical=canonical, domain=domain)
        self.cachedWikis[domain] = result
        return result

    def addSpecialName(self, specialName):
        """
        A 'special name' is a name which isn't in the wiki, but
        still exists as a page.  Like 'recentchanges', which is
        not a wiki page.
        """
        self.specialNames[specialName] = None

class Wiki(object):

    __metaclass__ = propertymeta.MakeProperties

    def __init__(self, globalWiki, domain, config, canonical):
        self.config = config
        self.domain = domain
        self.globalWiki = globalWiki
        self.canonical = canonical
        self.template = None

        if self.config.has_key('localbasepath'):
            self.basepath = self.config['localbasepath']
        else:
            if canonical:
                domain = canonical.domain
            else:
                domain = self.domain
            self.basepath = os.path.join(os.path.dirname(__file__),
                                         self.config['basepath'], domain)
        if not os.path.exists(self.basepath):
            os.mkdir(self.basepath)

        # @@: this doesn't work well...
        self.basehref = self.config.get('basehref',
                                        'http://%s' % self.domain)
        if not self.basehref.endswith('/'):
            self.basehref += '/'

        if self.config.getbool('staticpublish', False):
            self.publishQueue = filequeue.FileQueue(os.path.join(
                self.basepath, 'publish.queue'))

        if not canonical:
            if (config.getbool('rebuildindex', False) or
                not wikiindex.WikiIndex.exists(self.basepath)):
                needRebuild = True
            else:
                needRebuild = False
            self.index = wikiindex.WikiIndex(self.basepath)
            if config.getbool('rebuildhtml', False):
                self.rebuildHTML()
            if needRebuild:
                self.rebuildIndex()
            if config.getbool('rebuildstatic', False):
                self.rebuildStatic()
            self.checkDistributionFiles()
        else:
            self.index = canonical.index
        self._knownAtomIDs = {}

    def __repr__(self):
        return '<%s>' % self.shortRepr()

    def shortRepr(self):
        if not self.canonical:
            return 'Wiki:%s' % self.domain
        else:
            return 'Wiki:%s aliases %s' % (self.domain,
                                           self.canonical.domain)

    ############################################################
    ## Pages
    ############################################################

    def page(self, name, version=None):
        """
        Returns a page by the given name, with the given version
        (None == current version)
        """
        urlName = name
        name = canonicalName(name)
        return wikipage.WikiPage(self, self.basepath,
            name, urlName=urlName, version=version)

    def pageByAtomID(self, atomID):
        if atomID in self._knownAtomIDs:
            return self.page(self._knownAtomIDs[atomID])
        for page in self.allPages():
            self._knownAtomIDs[page.atomID] = page.name
        if atomID in self._knownAtomIDs:
            return self.page(self._knownAtomIDs[atomID])
        return None

    def filenameForName(self, filename):
        return os.path.join(self.basepath, filename + '.txt')

    def exists(self, name):
        """
        True if wiki page by name exists.
        """
        if self.globalWiki.specialNames.has_key(name):
            return True
        else:
            return os.path.exists(self.filenameForName(name))

    def search(self, text):
        """
        Search titles and bodies of pages for ``text``, returning list
        of pages
        """
        return [page for page in self.allPages()
                if page.searchMatches(text)]

    def searchTitles(self, text):
        """Search page titles for ``text``, returning list of pages"""
        return [page for page in self.allPages()
                if page.searchTitleMatches(text)]

    def searchNames(self, text):
        return [page for page in self.allPages()
                if page.searchNameMatches(text)]

    def recentPages(self):
        """All pages, sorted by date modified, most recent first"""
        pages = self.allPages()
        pages.sort(lambda a, b: cmp(b.modifiedDate, a.modifiedDate))
        return pages

    def recentCreated(self):
        """All pages, sorted by date created, most recent first"""
        pages = self.allPages()
        pages.sort(lambda a, b: cmp(b.creationDate, a.creationDate))
        return pages

    def orphanPages(self):
        """All pages which are not linked to by another page"""
        orphans = []
        for page in self.allPages():
            if not page.backlinks:
                orphans.append(page)
        orphans.sort(lambda a, b: cmp(a.name, b.name))
        return orphans

    def wantedPages(self):
        wantedPages = {}
        existant = []
        for page in self.allPages():
            existant.append(page.name)
            for link in self.index.forwardLinks(page.name):
                wantedPages.setdefault(link, []).append(page)
        for name in existant:
            if wantedPages.has_key(name):
                del wantedPages[name]
        return [(self.page(name), wants)
                for (name, wants) in wantedPages.items()]

    def allPages(self):
        """All pages with content in the system"""
        return [self.page(filename[:-4])
                for filename in os.listdir(self.basepath)
                if filename.endswith('.txt')]

    ############################################################
    ## Links
    ############################################################

    def linkTo(self, pageName, source=False):
        """
        Returns the href to refer to pageName
        """
        if isinstance(pageName, wikipage.WikiPage):
            page = pageName
            pageName = pageName.name
        else:
            page = self.page(pageName)
        pageName = pageName.lower()
        if '.' in pageName:
            # Already has an extension
            return self.basehref + pageName
        else:
            url = self.basehref + pageName
            if not source:
                return url + str(self.config.get('wikiextension', '.html'))
            else:
                return url + self.extensionForMimeType(page.mimeType)

    def staticLinkTo(self, pageName):
        if isinstance(pageName, wikipage.WikiPage):
            pageName = pageName.name
        if '.' in pageName:
            # already has an extension
            return self.config['statichref'] + pageName
        else:
            return (self.config['statichref']
                    + pageName
                    + self.config.get('staticextension', '.html'))

    ############################################################
    ## Content
    ############################################################

    def notifyChange(self, page, action, **args):
        """
        Called by the page everytime it is changed, so global
        indexing and updating can occur.
        """
        if action != 'connected':
            changed = self.syndicateRecentChanges
            desc = page.lastChangeLog or ''
            if page.lastChangeUser:
                desc += ' -- %s' % page.lastChangeUser
            item = rssobject.RSSItem(
                title=page.title,
                description=desc,
                link='http://%s%s' % (self.canonicalDomain, page.link),
                guid='http://%s%s?version=%s' % (
                self.canonicalDomain,
                page.link,
                page.versions()[-1].version),
                )
            changed.addItem(item, 10)
            changed.writeText()
            self.index.setLinks(page.name, page.wikiLinks())

        if action == 'create' and page.pageClass in ('posting',):
            new = self.syndicateNewPages
            link = 'http://%s%s' % (self.canonicalDomain, page.link)
            item = rssobject.RSSItem(
                title=page.title,
                description=page.html,
                link=link,
                guid=link,
                pubDate=rssobject.formatDate(page.creationDate))
            new.addItem(item, 10)
            new.writeText()

        self.schedulePublish(page)
        if action in ('create', 'delete'):
            for linkingPage in self.backlinks(page):
                self.schedulePublish(linkingPage)
        if page._connectionsDirty:
            page._connectionDirty = False
            self.index.setConnections(
                page.name,
                [(p.name, type) for p, type in page.connections])

    def canonicalDomain__get(self):
        if self.canonical:
            return self.canonical.domain
        else:
            return self.domain
    canonicalDomain = property(canonicalDomain__get)

    def schedulePublish(self, page):
        if not self.config.getbool('staticpublish', False):
            return
        assert pooledtemplate, (
            "You must install Cheetah (cheetahtemplate.org) to use "
            "static publishing")
        self.publishQueue.set(page.name)

    def publish(self):
        if not self.config.getbool('staticpublish', False):
            return
        pages = [self.page(n) for n in self.publishQueue.popmany(20)]
        if not pages:
            return
        try:
            meth = self.config.staticMethod
            print 'Publishing via %s: %s' % (
                meth,
                ', '.join([p.name for p in pages]))
            if meth == 'file':
                self.publishFile(pages)
            elif meth in ('ssh', 'scp', 'sftp'):
                self.publishRemote(pages, sshclient)
            elif meth == 'ftp':
                self.publishRemote(pages, ftpclient)
            else:
                assert 0, "Unknown static publishing method: %r" % meth
        except:
            self.publishQueue.extend([p.name for p in pages])
            raise

    def publishFile(self, pages):
        for page in pages:
            if not os.path.exists(self.config.staticPath):
                os.mkdir(self.config.staticPath)
            base = os.path.join(self.config.staticPath, page.name )
            f = open(base + '.html', 'wb')
            f.write(self.publishedText(page))
            f.close()
            if not page.mimeType == 'text/html':
                f = open(base + self.extensionForMimeType(page.mimeType), 'wb')
                f.write(page.text)
                f.close()

    def publishRemote(self, pages, remoteModule):
        fileList = self._publishTempFiles(pages)
        try:
            remoteModule.uploadFiles(
                hostname=self.config.staticHostname,
                fileList=fileList,
                username=self.config.staticUsername,
                password=self.config.staticPassword)
        finally:
            self._unpublishTempFiles(fileList)

    def _publishTempFiles(self, pages):
        fileList = []
        for page in pages:
            source = os.tempnam()
            dest = os.path.join(self.config.staticPath, page.name )
            f = open(source, 'wb')
            f.write(self.publishedText(page))
            f.close()
            fileList.append((source, dest + '.html'))
            if not page.mimeType == 'text/html':
                source = os.tempnam()
                f = open(source, 'wb')
                f.write(page.text)
                f.close()
                fileList.append(
                    (source,
                     dest + self.extensionForMimeType(page.mimeType)))
        return fileList

    def _unpublishTempFiles(self, fileList):
        for source, dest in fileList:
            os.unlink(source)

    def publishedText(self, page):
        if self.template is None:
            if not os.path.exists(self.config.staticTemplate):
                filename = (
                    os.path.join(os.path.dirname(__file__),
                                 'default_static.tmpl'))
            else:
                filename = self.config.staticTemplate
            self.template = pooledtemplate.Template(file=filename)
        return self.template.eval(page=page)

    def rebuildHTML(self):
        print "Rerending HTML"
        for page in self.allPages():
            page.rerender()

    def rebuildStatic(self):
        print "Rebuilding static pages"
        for page in self.allPages():
            self.schedulePublish(page)

    def recreateThumbnails(self):
        print "Recreating thumbnails"
        for page in self.allPages():
            page.recreateThumbnail()

    def syndicateRecentChanges__get(self):
        """
        Returns the rssobject.RSS object.
        """
        rss = rssobject.RSS(self.syndicateRecentChangesFilename)
        conf = self.config.get('rss', {})
        for attribute in rssobject.rssAttributes:
            value = conf.get(attribute)
            if value:
                setattr(rss, attribute, value)
        rss.link = 'http://%s%s' % (self.canonicalDomain, self.basehref)
        return rss

    def syndicateRecentChangesFilename__get(self):
        return os.path.join(self.basepath, 'rss_recent_changes.xml')

    def syndicateNewPages__get(self):
        def sorter(item1, item2):
            return cmp(
                rssobject.parseDate(item1.pubDate),
                rssobject.parseDate(item2.pubDate))
        rss = rssobject.RSS(self.syndicateNewPagesFilename, sortOrder=sorter)
        conf = self.config.get('rss', {})
        for attribute in rssobject.rssAttributes:
            value = conf.get(attribute)
            if value:
                setattr(rss, attribute, value)
        rss.link = 'http://%s%s' % (self.canonicalDomain, self.basehref)
        return rss

    def syndicateNewPagesFilename__get(self):
        return os.path.join(self.basepath, 'rss_new_pages.xml')

    def extensionForMimeType(self, mimeType):
        return _reverseMimeMap[mimeType]

    availableMimeTypes = [
        'text/x-restructured-text',
        'text/html',
        'text/plain',
        'text/x-python',
        'image/gif',
        'image/png',
        'image/jpeg',
        'image/*',
        'application/*',
        ]

    ############################################################
    ## Relations and indexing
    ############################################################

    def backlinks(self, page):
        return [self.page(name)
                for name in self.index.backlinks(page.name)]

    def connectedPages(self, page):
        return [(self.page(name), type)
                for name, type
                in self.index.connections(page.name)]

    def connectPage(self, sourcePage, destPage, type):
        connections = self.index.connections(destPage.name)
        sourceName = sourcePage.name
        for name, connType in connections:
            if name == sourceName and connType == type:
                return
        connections.append((sourceName, type))
        self.index.setConnections(destPage.name, connections)

    def unconnectPage(self, sourcePage, destPage, type):
        connections = self.index.connections(destPage.name)
        try:
            connections.remove((sourcePage.name, type))
        except ValueError:
            pass
        else:
            self.index.setConnections(destPage.name, connections)

    def backConnections(self, page):
        result = []
        for name, type in self.index.backConnections(page.name):
            result.append((self.page(name), type))
        return result

    ############################################################
    ## Administrative and maintenance functions
    ############################################################

    def rebuildIndex(self):
        print "Rebuilding index"
        for page in self.allPages():
            self.index.setLinks(page.name, page.wikiLinks())
            self.index.setConnections(
                page.name,
                [(p.name, type) for p, type in page.connections])

    def checkDistributionFiles(self):
        sourcePath = os.path.join(os.path.dirname(__file__), 'distpages')
        names = []
        files = {}
        for filename in os.listdir(sourcePath):
            base, ext = os.path.splitext(filename)
            files.setdefault(base, []).append(filename)
            if ext == '.meta':
                names.append(base)
        for name in names:
            page = self.page(name)
            if not page.exists() or page.distributionOriginal:
                f = open(os.path.join(sourcePath, name+'.txt'), 'r')
                newText = f.read()
                f.close()
                d = rfc822persist.RFC822Dict(
                    os.path.join(sourcePath, name+'.meta'), 'r')
                if page.text == newText:
                    for name, value in page.metadata.items():
                        if d.has_key(name) and d[name] != value:
                            break
                    else:
                        continue
                print "Updating %s from distribution" % name
                page.updateRawMetadata(d)
                page.text = newText
                page.distributionOriginal = True
                page.lastChangeLog = 'Updated from distribution'
                page.save()

_reverseMimeMap = {}
for _extDict in [mimetypes.types_map, mimetypes.common_types]:
    for _key, _value in _extDict.items():
        _reverseMimeMap[_value] = _key

# We can't add this to mimetypes, because then the .txt extension
# would be overwritten there.
_reverseMimeMap['text/x-restructured-text'] = '.txt'
# Theoretically it should be .jpeg, but .jpg is conventional:
_reverseMimeMap['image/jpeg'] = '.jpg'
# No .htm
_reverseMimeMap['text/html'] = '.html'
_reverseMimeMap['text/x-redirect-list'] = '.redirect'
