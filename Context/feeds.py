from SitePage import *

class feeds(SitePage):

    def awake(self, trans):
        SitePage.awake(self, trans)
        req = self.request()
        name = req.extraURLPath().strip('/')
        self.feedName = name

    def writeHTML(self):
        if self.feedName:
            self.writeFeed(self.feedName)
        else:
            SitePage.writeHTML(self)

    def writeContent(self):
        self.write('<h4>There are two RSS feeds available:</h4>')
        self.write('<p><a href="%s">Recent Changes</a>:'
            ' a feed of all changes to the site.</p>\n'
            '<p><a href="%s">New posts</a>: '
            ' a feed of all new posts to the site.</p>'
               % (self.wiki.linkTo('feeds/recent_changes.xml'),
                  self.wiki.linkTo('feeds/new_pages.xml')))

    def writeFeed(self, name):
        self.response().setHeader('Content-type',
            'application/rss+xml; charset=utf-8')
        if name == 'recent_changes.xml':
            f = open(self.wiki.syndicateRecentChangesFilename)
            self.write(f.read())
            f.close()
        elif name == 'new_pages.xml':
            f = open(self.wiki.syndicateNewPagesFilename)
            self.write(f.read())
            f.close()
        else:
            self.response().setHeader('Status', '404 Not Found')
            self.write('Not Found')

