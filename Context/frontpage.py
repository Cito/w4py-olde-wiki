from SitePage import *
import time

class frontpage(SitePage):

    _cached_content = None
    _cache_time = 0
    _cache_timeout = 60

    def title(self):
        return 'Ian Bicking: A Blog'

    def writeContent(self):
        if time.time() - self._cache_time > self._cache_timeout:
            frontpage._cached_content = self.getContent()
            frontpage._cache_time = time.time()
        self.write(self._cached_content)
        
    def getContent(self):
        result = []
        write = result.append
        recent = [p for p in self.wiki.recentCreated()
                  if p.pageClass == 'posting'][:10]
        for page in recent:
            write('<a href="%s"><h2>%s</h2></a>\n' %
                  (page.link, page.title))
            write(page.html)
            comments = page.commentPages
            if not comments:
                comment_text = 'No comments'
            elif len(comments) == 1:
                comment_text = '1 thread'
            else:
                comment_text = '%i threads' % len(comments)
            write('''
            <div align="right"><a href="%s">#</a> **
            %s **
            <a href="%s#comments">%s</a></div>
            <hr noshade>
            ''' % (page.link, self.format_date(page.creationDate),
                   page.link, comment_text))
        return ''.join(result)
