from SitePage import *
import time

class frontpage(SitePage):

    _cached_content = None
    _cache_time = 0
    _cache_timeout = 60

    def title(self):
        return self.wiki.config.get('rss') and \
            self.wiki.config.get('rss').get('title') or 'The Wiki Frontpage'

    def writeRelatedLinks(self):
        description = self.wiki.config.get('rss') and \
            self.wiki.config.get('rss').get('description')
        if description:
            self.write('<meta name="description" content="%s">\n'
                % description)
        SitePage.writeRelatedLinks(self)

    def writeContent(self):
        if time.time() - self._cache_time > self._cache_timeout:
            frontpage._cached_content = self.getContent()
            frontpage._cache_time = time.time()
        self.write(self._cached_content)

    def getContent(self):
        result = []
        write = result.append
        if self.wiki.config.getbool('blog', False):
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
        else: # use index as front page
            page = self.wiki.page('index')
            write(page.html)
            if self.user():
                write('<div align="right"><a href="%s">Edit this page</a>'
                    '</div>\n' % (page.link))
        return ''.join(result)
