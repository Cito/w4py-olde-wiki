from SitePage import *
import re

class search(SitePage):

    def awake(self, trans):
        SitePage.awake(self, trans)
        req = self.request()
        self.titleSearch = req.field('searchTitle', '').strip()
        self.bodySearch = req.field('searchBody', '').strip()
        self.gotoSearch = req.field('searchGoto', '').strip()
        self.genericSearch = req.field('search', '')
        if isinstance(self.genericSearch, list):
            self.genericSearch = self.genericSearch[0]
        self.genericSearch = self.genericSearch.strip()
        if self.genericSearch:
            if self.genericSearch.lower().startswith('title:'):
                junk, self.titleSearch = self.genericSearch.split(':', 1)
                self.titleSearch = self.titleSearch.strip()
            elif self.genericSearch.lower().startswith('goto:'):
                junk, self.gotoSearch = self.genericSearch.split(':', 1)
                self.gotoSearch = self.gotoSearch.strip()
            else:
                self.bodySearch = self.genericSearch
        self.results = None
        self.explanation = 'Search'
        if self.bodySearch:
            self.explanation = 'Search for "%s"' % self.htmlEncode(self.bodySearch)
            self.results = self.wiki.search(self.bodySearch)
        elif self.titleSearch:
            self.explanation = 'Title search for "%s"' % self.htmlEncode(self.titleSearch)
            self.results = self.wiki.searchTitles(self.titleSearch)
        elif self.gotoSearch:
            self.explanation = 'Goto "%s"' % self.htmlEncode(self.gotoSearch)
            self.results = self.wiki.searchNames(self.gotoSearch)
            if self.results:
                if len(self.results) > 1:
                    self.message('Also matched: %s'
                                 % ', '.join(['<a href="%s">%s</a>'
                                              % (page.link, page.title)
                                              for page in self.results[1:]]))
                self.sendRedirectAndEnd(self.results[0].link)

    def writeContent(self):
        self.writeForm()
        if self.results is not None:
            if not self.results:
                self.write('<p>No pages found</p>\n')
            else:
                self.writeResults(self.results)

    def title(self):
        return self.explanation

    def htTitle(self):
        return ''

    def writeForm(self):
        self.write('''
        <form action="" method="GET" id="searchbar">
        <label for="search">Search:
        <input type="text" name="search" size=30 value="%s" style="font-weight: bold">
        </label>
        <input type="submit" value="search"><br>
        <span style="font-size: small">
        <i>Prefix your search with </i><tt>title:</tt><i> to search
        just titles; </i><tt>goto:</tt><i> to jump to best match</i></span></form>'''
                   % (self.htmlEncode(self.genericSearch or self.titleSearch or self.bodySearch)))

    def writeResults(self, results):
        results.sort(lambda a, b: cmp(a.name, b.name))
        self.write('<dl>\n')
        query = self.bodySearch or self.titleSearch
        regex = re.compile('(%s)' % re.escape(query), re.I)
        for page in results:
            self.write('<dt><a href="%s">%s</a></dt>\n'
                       % (page.link, self.htmlEncode(page.title)))
            segment = self.htmlEncode(page.searchSegment(query, length=200))
            segment = regex.sub(r'<b class="found">\1</b>', segment)
            self.write('<dd class="summary">%s</dd>'
                       % segment)
        self.write('</dl>\n')
        
