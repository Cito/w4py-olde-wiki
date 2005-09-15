from SitePage import *

class orphans(SitePage):

    def title(self):
        return 'Orphaned pages'

    def writeContent(self):
        pages = self.wiki.orphanPages()
        self.write('<p>These <b>%i</b> pages are not linked to from '
                   'any other pages.</p>\n'
                   % len(pages))
        self.writeSimplePageList(pages)
