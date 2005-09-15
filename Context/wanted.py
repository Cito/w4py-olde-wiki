from SitePage import *

class wanted(SitePage):

    def title(self):
        return 'Wanted pages'

    def writeContent(self):
        pages = self.wiki.wantedPages()
        # sort by most wanted, then name:
        pages.sort(lambda a, b: cmp((-len(a[1]), a[0].name),
                                    (-len(b[1]), b[0].name)))
        self.write('<p>These <b>%i</b> pages are being linked to, but '
                   'have not been created yet.</p>\n'
                   % len(pages))
        self.write('<table>\n')
        self.write('<tr class="header">\n')
        self.write('<th>Wanted page</th>\n')
        self.write('<th>Wanted by</th>\n')
        self.write('</tr>\n')
        index = 0
        for page, wants in pages:
            index += 1
            for subindex, want in enumerate(wants):
                self.write('<tr class="%s"><td>'
                           % ['odd', 'even'][index%2])
                if not subindex:
                    self.write('<a href="%s">%s</a>'
                               % (page.link, page.title))
                self.write('</td><td><a href="%s">%s</a></td></tr>\n'
                           % (want.link, self.htmlEncode(want.title)))
        self.write('</table>')
