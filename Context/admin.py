from SitePage import *
from lib.import_atom import import_atom

class admin(SitePage):

    def title(self):
        return 'Administration'

    def loginRequired(self):
        return True

    def pageClass(self):
        return 'admin'

    def actions(self):
        return ['rebuildIndex', 'rebuildHTML', 'rebuildStatic',
                'recreateThumbnails', 'import_atom']

    def rebuildIndex(self):
        self.wiki.rebuildIndex()
        self.done()

    def rebuildHTML(self):
        self.wiki.rebuildHTML()
        self.done()

    def rebuildStatic(self):
        self.wiki.rebuildStatic()
        self.done()

    def recreateThumbnails(self):
        self.wiki.recreateThumbnails()
        self.done()

    def done(self):
        self.sendRedirectAndEnd('admin')

    def import_atom(self):
        output = []
        atom_data = self.request().field('atom_upload')
        if not isinstance(atom_data, str):
            atom_data = atom_data.value
        redirects = import_atom(
            self.wiki, atom_data, output.append)
        redirects_page = self.wiki.page('redirects')
        if not redirects_page.exists():
            redirects_page.hidden = True
            redirects_page.pageType = 'admin'
            redirects_page.mimeType = 'text/x-redirect-list'
        redirect_map = {}
        for line in redirects_page.text.splitlines():
            from_link, to_link = line.split(None, 1)
            redirect_map.setdefault(from_link, []).append(to_link)
        for from_link, to_link in redirects:
            if to_link in redirect_map.get(from_link, []):
                continue
            redirect_map.setdefault(from_link, []).append(to_link)
        redirect_map = redirect_map.items()
        redirect_map.sort()
        lines = []
        for from_link, to_links in redirect_map:
            for to_link in to_links:
                lines.append('%s %s\n' % (from_link, to_link))
        redirects_page.text = ''.join(lines)
        redirects_page.lastChangeLog = 'Updated from atom import'
        redirects_page.save()
        for line in output:
            self.message(line)
        self.sendRedirectAndEnd('admin')

    def writeContent(self):
        self.write('<h3>Commands:</h3>\n')
        self.write('<form action="admin" method="POST">\n')
        for desc, name in [('Rebuild index', 'rebuildIndex'),
                           ('Rebuild/rerender all HTML', 'rebuildHTML'),
                           ('Rebuild static site', 'rebuildStatic'),
                           ('Recreate thumbnails', 'recreateThumbnails'),
                           ]:
            self.write('<p><input type="submit" name="_action_%s" value="%s"></p>\n'
                       % (name, desc))
        self.write('</form>')
        self.write('''
            <script type="text/javascript">
            function upload_submit() {
              el = document.getElementById(\'upload_button\');
              el.value = \'Uploading...\';
              el.disabled = true;
            }
            </script>
            <form action="admin" method="POST" enctype="multipart/form-data"
            onSubmit="upload_submit()">
            <input type="hidden" name="_action_" value="import_atom">
            <h4>ATOM (or maybe RSS) feed to import:</h4>
            <p><input type="file" name="atom_upload">
            <input type="submit" id="upload_button" value="Upload"></p>
            </form>
        ''')
