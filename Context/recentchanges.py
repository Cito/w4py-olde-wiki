from SitePage import *


class recentchanges(SitePage):

    def writeContent(self):
        recentType = self.request().field('type', 'changes')
        if recentType == 'changes':
            pages = self.wiki.recentPages()
        elif recentType == 'created':
            pages = self.wiki.recentCreated()
        else:
            assert 0, "Unknown type: %r" % recentType

        limit = int(self.request().field('limit', 0))
        if limit:
            pages = pages[:limit]

        if recentType == 'changes':
            self.write('<p>RSS feed of recent changes: <a href="%s" title="RSS of recent changes" id="recentchanges_xml"><img src="%s" width=19 height=9 border=0></a>\n'
                       % (self.wiki.linkTo('feeds/recent_changes.xml'),
                          self.wiki.linkTo('miniXmlButton.gif')))
        elif recentType == 'created':
            self.write('<p>RSS feed of new posts: <a href="%s" title="RSS of new posts" id="recentchanges_xml"><img src="%s" width=19 height=9 border=0></a>\n'
                       % (self.wiki.linkTo('feeds/new_pages.xml'),
                          self.wiki.linkTo('miniXmlButton.gif')))
            

        self.write('''<table>
        <tr class="header">
        <th>Page</th>
        <th>Last modified</th>
        <th>Log message</th>
        <th>User</th>
        </tr>
        ''')
        index = 0
        anyError = False
        for page in pages:
            index += 1
            if index % 2:
                rowClass = 'even'
            else:
                rowClass = 'odd'
            if page.hasParseErrors:
                anyError = True
                bang = ('<img src="%s" width=12 height=18 '
                        'alt="[errors]" title="Markup errors were found in this document">\n'
                        % (self.wiki.linkTo('exclamation.gif')))
            else:
                bang = ''
            self.write('<tr class="%s"><td><a href="%s">%s</a>%s</td>\n'
                       % (rowClass, page.link, page.title, bang))
            self.write('<td>%s</td>\n'
                       % self.format_date(page.modifiedDate, nonbreaking=True))
            self.write('<td>%s</td>\n'
                       % self.htmlEncode(page.lastChangeLog or ''))
            self.write('<td>%s</td>\n'
                       % self.htmlEncode(page.lastChangeUser or ''))
            self.write('</tr>\n')
        self.write('</table>')
        if anyError:
            self.write('''
            <p><img src="%s" width=12 height=18 alt="[errors]">
            indicates that errors occured while trying to parse the
            document.</p>
            ''' % self.wiki.linkTo('exclamation.gif'))

    def title(self):
        return 'Recent Changes'
