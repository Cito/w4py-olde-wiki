from SitePage import SitePage
import time

class frontpage(SitePage):

    _cached_content = None
    _cache_time = 0
    _cache_timeout = 60

    def title(self):
        return self.wiki.config.get('rss') and \
            self.wiki.config.get('rss').get('title') or 'The Wiki Frontpage'

    def writeRelatedLinks(self):
        SitePage.writeRelatedLinks(self)
        description = self.wiki.config.get('rss') and \
            self.wiki.config.get('rss').get('description')
        if description:
            self.write('<meta name="description" content="%s">\n' % description)
        if self.user() and self.checkPermission('edit'):
            # add universal edit button
            page = self.wiki.page('index')
            self.write('<link rel="alternate" type="application/wiki"'
                ' title="Edit this page" href="%s?_action_=edit">'  % page.link)

    def writeContent(self):
        if self.wiki.config.getbool('blog', False):
            if not self._cached_contenttime or \
                    time() - self._cache_time > self._cache_timeout:
                frontpage._cached_content = self.getBlogContent()
                frontpage._cache_time = time.time()
            self.write(self._cached_content)
        else:
            self.write(self.getWikiContent())

    def getBlogContent(self):
        result = []
        write = result.append
        recent = [p for p in self.wiki.recentCreated()
                  if p.pageClass == 'posting'][:10]
        for page in recent:
            write('<a href="%s"><h2>%s</h2></h2>\n' %
                  (page.link, page.title))
            write(page.html)
            comments = page.commentPages
            if not comments:
                comment_text = 'No comments'
            elif len(comments) == 1:
                comment_text = '1 thread'
            else:
                comment_text = '%i threads' % len(comments)
            write('<div align="right"><a href="%s">#</a> ** %s ** '
                '<a href="%s#comments">%s</a></div>\n'
                % (page.link, self.format_date(page.creationDate),
                       page.link, comment_text))
            write('<hr noshade>\n')
        result.pop() # remove last <hr>
        return ''.join(result)

    def getWikiContent(self):
        page = self.wiki.page('index')
        result = page.html
        if self.user() and self.checkPermission('edit'):
            result += ('\n<div align="right"><a href="%s?_action_=edit">'
                'Edit this page</a></div>\n') % page.link
        return result
