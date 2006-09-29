import shelve
import os
import atexit

_shelvesToClose = []

def _closeHandler():
    while _shelvesToClose:
        _shelvesToClose.pop().close()

atexit.register(_closeHandler)

class WikiIndex(object):

    _dbName = 'index.db'

    def __init__(self, dir):
        self.dir = dir
        self.filename = os.path.join(self.dir, self._dbName)
        self.store = shelve.open(self.filename)
        _shelvesToClose.append(self.store)

    def exists(cls, dir):
        return os.path.exists(os.path.join(dir, cls._dbName))
    exists = classmethod(exists)

    def clear(self):
        """Clear the index."""
        self.store.clear()

    def backlinks(self, pageName):
        """Returns a list of pages that link to pageName."""
        return self._getLinks('backlink', pageName)

    def forwardLinks(self, pageName):
        """Returns a list of pages to which pageName links."""
        return self._getLinks('forward', pageName)

    def _setBacklinks(self, pageName, links):
        self._setLinks('backlink', pageName, links)

    def _setForwardLinks(self, pageName, links):
        self._setLinks('forward', pageName, links)

    def setLinks(self, pageName, links):
        """Indexes all the backlinks for a page.

        Also indexes forward links, so that we can tell
        when a backlink needs to be removed.

        """
        oldLinks = self.forwardLinks(pageName)
        oldLinks.sort()
        newLinks = links[:]
        newLinks.sort()
        toRemove = []
        toAdd = []
        while links and oldLinks:
            if links[0] > oldLinks[0]:
                toRemove.append(oldLinks.pop(0))
            elif links[0] < oldLinks[0]:
                toAdd.append(links.pop(0))
            else:
                oldLinks.pop(0)
        toRemove.extend(oldLinks)
        toAdd.extend(newLinks)
        for link in toRemove:
            prev = self.backlinks(link)
            try:
                prev.remove(pageName)
            except ValueError:
                # @@: because it's not transactional and concurrency
                # control is poor, we might not have consistent data
                # here, so we might not find the link
                pass
            self._setBacklinks(link, prev)
        for link in toAdd:
            prev = self.backlinks(link)
            prev.append(pageName)
            prev.sort()
            self._setBacklinks(link, prev)
        self._setForwardLinks(pageName, links)

    def _getLinks(self, type, pageName):
        result = self.store.get(str('%s.%s' % (type, pageName)), '')
        result = filter(None, result.split(','))
        return result

    def _setLinks(self, type, pageName, links):
        links = ','.join(unique(links))
        self.store['%s.%s' % (type, pageName)] = links

    def connections(self, pageName):
        """Returns a list of all the connections.

        The list has the form [(connection_type_string, pageName), ...].
        This is pages connected *to* this page.
        """
        result = self.store.get('connections.%s' % pageName, '')
        values = result.split(',')
        connections = []
        for value in values:
            if not value:
                continue
            connectionType, pageName = value.split(':', 1)
            connections.append((pageName, connectionType))
        return connections

    def setConnections(self, pageName, connections):
        oldConnections = self.connections(pageName)
        values = ','.join([
            '%s:%s' % (t, n) for n, t in connections])
        self.store['connections.%s' % pageName] = values
        for connPage, type in connections:
            back = self.backConnections(connPage)
            if (pageName, type) in back:
                # @@: Really this shouldn't happen, as it signals
                # a data integrity problem
                continue
            back.append((pageName, type))
            self._setBackConnections(connPage, back)
        for connPage, type in oldConnections:
            if (connPage, type) in connections:
                continue
            back = self.backConnections(connPage)
            if (pageName, type) not in back:
                # @@: again shouldn't happen
                continue
            back.remove((pageName, type))
            self._setBackConnections(connPage, back)

    def backConnections(self, pageName):
        result = self.store.get('back_connections.%s' % pageName, '')
        values = result.split(',')
        backConn = []
        for value in values:
            if not value:
                continue
            connectionType, pageName = value.split(':', 1)
            backConn.append((pageName, connectionType))
        return backConn

    def _setBackConnections(self, pageName, backConn):
        values = ','.join([
            '%s:%s' % (t, n) for n, t in backConn])
        self.store['back_connections.%s' % pageName] = values

    def _packDict(self, d):
        return ','.join(['%s:%s' % (k, v)
                         for (k, v) in d.items()])

    def _unpackDict(self, s):
        v = [t.split(':', 1) for t in s.split(',') if t]
        try:
            return dict(v)
        except ValueError:
            raise ValueError, "Bad dict: %r (became %r)" % (s, v)

def unique(vals):
    result = {}
    for v in vals:
        result[v] = None
    return result.keys()
