from SitePage import *
from lib import wikipage
from lib import htmldiff
from lib import menubar
from WebKit.HTTPExceptions import *
try:
    import tidy
except ImportError:
    tidy = None
import re
import os
import mimetypes
import datetime
from lib.format_date import format_date_relative
from lib.common import dedent

def test(val, a, b=''):
    if val:
        return a
    else:
        return b

class Main(SitePage):

    def __init__(self):
        SitePage.__init__(self)
        self._inputTypeCleaners = {}
        self._inputTypeCleaners['htmlarea'] = self.cleanHTMLArea

    def setupEarly(self):
        req = self.request()
        name = req.extraURLPath().strip('/')
        if not name:
            self.forward('/frontpage')
        name, ext = self.splitExtension(name)
        if name in self.wiki.globalWiki.specialNames:
            # We got the .html ending or somesuch, and we shouldn't
            # have, so we'll redirect
            self.sendRedirectAndEnd(self.servletLink(name))
            return
        version = self.getVersion()
        self.page = self.wiki.page(name, version=version)
        if name != self.page.urlName:
            link = self.page.link
            if '?' in link:
                link += '&'
            else:
                link += '?'
            link += self.encodeArgs()
            self.sendRedirectAndEnd(link)
        self.titlePrefix = ''
        if ext == '.thumb.jpg':
            req.setField('_action_', 'thumbnail')
        elif ext != '.html':
            req.setField('_action_', 'source')

    def sleep(self, transaction):
        SitePage.sleep(self, transaction)
        self.page = None

    def respondToPut(self, transaction):
        self.webdav()

    respondToLock = respondToUnlock = respondToPut

    def actions(self):
        return ['edit', 'preview', 'save', 'cancel', 'history',
                'externalEdit', 'webdav', 'backlinks', 'diff',
                'changeMimeType', 'simple', 'source', 'comment',
                'thumbnail', 'attach']

    def pageClass(self):
        if (not self.page.exists()
            and self.request().field('commenting', None)):
            return 'comment'
        return self.page.pageClass

    def authorUser(self):
        return self.page.authorUser

    def writeGoogleAds(self):
        if self.view() not in ('writeEdit', 'writePreview', 'writeChangeMimeType'):
            SitePage.writeGoogleAds(self)

    ########################################
    ## Utility methods
    ########################################

    def splitExtension(self, name):
        if name.endswith('.thumb.jpg'):
            ext = '.thumb.jpg'
            name = name[:-len('.thumb.jpg')]
        elif '.' in name:
            name, ext = os.path.splitext(name)
        else:
            ext = '.html'
        return name, ext

    def getVersion(self):
        version = self.request().field('version', None) or None
        if isinstance(version, (list, tuple)):
            version = version[0]
        try:
            version = int(version)
            if version < 1:
                raise ValueError
        except:
            version = None
        return version

    def cleanInput(self, inputType, text):
        if text.startswith('base64,'):
            text = text[7:].decode('base64')
        text = self._inputTypeCleaners.get(inputType, lambda x: x)(text)
        return text

    def assertEdit(self):
        if self.page.exists():
            self.assertPermission('edit')
        else:
            self.assertPermission(['create', 'edit'])

    ########################################
    ## Edit
    ########################################

    def edit(self):
        self.assertEdit()
        req = self.request()
        self.titlePrefix = 'Edit: '
        mimeType = req.field('mimeType', self.page.mimeType)
        if mimeType != self.page.mimeType and self.page.exists():
            assert 0, "Content conversion has not yet been implemented"
        self._setPageClass = 'posting'
        self.commenting = req.field('commenting', 0)
        if self.commenting:
            self._setPageClass = 'comment'
        self.attaching = req.field('attaching', 0)
        if self.attaching:
            self._setPageClass = 'attachment'
        assert not self.commenting or not self.attaching
        if self.commenting:
            self.orig = self.wiki.page(self.commenting)
            if (not req.hasField('title')
                and not self.orig.title.lower().startswith('re:')):
                req.setField('title', 'Re: %s' % self.orig.title)
        if self.attaching:
            self.orig = self.wiki.page(self.attaching)
            if not req.hasField('title'):
                req.setField('title', 'Attachment to: %s' % self.orig.title)
            if not req.hasField('mimeType'):
                req.setField('mimeType', 'application/*')
        self.setView('writeEdit')
        self.writeHTML()

    _comment_name_re = re.compile(r'-*comment-?\d+$')
    def comment(self):
        if self._comment_name_re.search(self.page.urlName):
            newName = self._comment_name_re.sub('', self.page.urlName)
        else:
            newName = self.page.urlName
        p = self.wiki.page(newName + '-comment-000')
        raise HTTPTemporaryRedirect(
            p.link +
            '?_action_=edit&commenting=%s'
            % self.urlEncode(self.page.name))

    def attach(self):
        p = self.wiki.page(self.page.name + 'attach-000')
        raise HTTPTemporaryRedirect(
            p.link +
            '?_action_=edit&attaching=%s'
            % self.urlEncode(self.page.name))

    def preview(self):
        self.saveCookieAuthorInfoFromRequest()
        self.setView('writePreview')
        self.titlePrefix = 'Preview: '
        req = self.request()
        self.writeHTML()

    def save(self):
        self.assertEdit()
        req = self.request()
        self.saveCookieAuthorInfoFromRequest()
        if self.page.name.endswith('000'):
            # This means we have to create a new page name that is
            # uniquely numbered.  @@: This isn't actually safe,
            # since instantiating the page won't make it "exist",
            # and another thread could still use the same number
            name = self.page.name[:-3]
            n = 1
            while 1:
                if not self.wiki.page('%s%i' % (name, n)).exists():
                    break
                n += 1
            oldPage = self.page
            self.page = self.wiki.page('%s%i' % (name, n))
            self.page.urlName = oldPage.urlName[:-3] + str(n)
            self.page.title = req.field('title')
            if self.page.title.find('000') != -1:
                self.page.title = self.page.title.replace('000', str(n))
        else:
            self.page.title = req.field('title')
        inputType = req.field('inputType')
        text = req.field('text', '')
        textUpload = req.field('textUpload', '')
        mimeType = req.field('mimeType')
        try:
            filename = textUpload.filename
            if mimeType.startswith('application/'):
                mt, encoding = mimetypes.guess_type(filename)
                if mt:
                    mimeType = mt
            textUpload = textUpload.value
            self.page.originalFilename = filename
        except AttributeError:
            pass
        if textUpload:
            text = textUpload
        text = self.cleanInput(inputType, text)
        self.page.mimeType = mimeType
        self.page.title = req.field('title')
        if req.field('hidden', None):
            self.assertPermission('hide')
        self.page.hidden = req.field('hidden', '')
        if req.hasField('comments'):
            self.page.comments = req.field('comments')
        self.page.lastChangeLog = req.field('changeLog', '')
        if self.user():
            self.page.lastChangeUser = self.user().username()
        else:
            self.page.lastChangeUser = 'anonymous'
        if req.field('authorName', None):
            self.page.authorName = req.field('authorName')
        if req.field('authorURL', None):
            self.page.authorURL = req.field('authorURL')
        if req.field('authorEmail', None):
            self.page.authorEmail = req.field('authorEmail')
        if self.user():
            self.page.authorUser = self.user()
        if text or not self.page.text:
            self.page.text = text or ''
        self.page.distributionOriginal = False
        pageClass = req.field('pageClass', None)
        if req.field('commenting', None):
            parentPage = self.wiki.page(req.field('commenting'))
            self.page.connections += [(parentPage, 'comment')]
            if pageClass is None:
                pageClass = 'comment'
        if req.field('attaching', None):
            parentPage = self.wiki.page(req.field('attaching'))
            self.page.connections += [(parentPage, 'attachment')]
            if pageClass is None:
                pageClass = 'attachment'
        if pageClass is None:
            pageClass = 'posting'
        self.page.pageClass = pageClass
        self.page.save()
        self.message('Changes saved')
        self.sendRedirectAndEnd(self.link(unversioned=True))

    def cancel(self):
        self.message('Edit cancelled')
        self.sendRedirectAndEnd(self.link(unversioned=True))

    def history(self):
        self.assertPermission(['history', 'view'])
        self.setView('writeHistory')
        self.titlePrefix = 'History of: '
        self.writeHTML()

    def backlinks(self):
        self.assertPermission(['navigation', 'view'])
        self.setView('writeBacklinks')
        self.titlePrefix = 'Backlinks to: '
        self.writeHTML()

    def diff(self):
        if self.request().field('delete', None):
            self.history()
        else:
            self.assertPermission(['diff', 'history', 'view'])
            firstVersion = self.request().field('firstVersion', None) or None
            self.firstPage = self.wiki.page(self.page.name, version=firstVersion)
            otherVersion = self.request().field('otherVersion', None) or None
            self.otherPage = self.wiki.page(self.page.name, version=otherVersion)
            self.setView('writeDiff')
            self.titlePrefix = ('Diff %s to %s of:' %
                (firstVersion or 'Current', otherVersion or 'Current'))
            self.writeHTML()

    def externalEdit(self):
        self.assertEdit()
        self.setView(None)
        res = self.response()
        req = self.request()
        if not req.hasCookie('_SID_'):
            raise HTTPBadRequest(
                "Your browser must support cookies to use the external "
                "editor.")
        res.setHeader('content-type', 'application/x-zope-edit')
        self.write('url:http://%s%s\n'
                   % (req.environ()['HTTP_HOST'],
                      self.link(action='webdav')))
        self.write('meta_type:Wiki\n')
        # no HTTP or cookie authentication required:
        self.write('auth:\n')
        self.write('cookie: _SID_=%s\n'
                   % (req.cookie('_SID_')))
        self.write('\n')
        self.write('## title=%s\n' % self.page.title)
        self.write('## class=%s\n' % (self.page.pageClass or 'posting'))
        self.write('## log=\n')
        self.write('\n')
        self.write(self.page.text.replace('\r', ''))

    def webdav(self):
        self.assertEdit()
        # @@: Really, this should make sure that we send a real
        # 401, not an HTML login form.  But that's not easy at the
        # moment :(  HTTPForbidden instead?
        self.setView(None)
        req = self.request()
        method = req.environ()['REQUEST_METHOD'].upper()
        metavars = {'user': 'lastChangeUser',
                    'log': 'lastChangeLog',
                    'title': 'title',
                    'class': 'pageClass'}

        if method in ('LOCK', 'UNLOCK'):
            # We don't support these now
            return

        if method == 'GET':
            self.write(self.page.text)
            return

        if method == 'PUT':
            f = req.rawInput(rewind=1)
            text = f.read()
            lines = text.splitlines()
            metadata = {}
            while 1:
                if not lines:
                    break
                line = lines[0].strip()
                if not line:
                    lines.pop(0)
                    continue
                if not line.startswith('##'):
                    break
                if '=' not in line:
                    break
                lines.pop(0)
                line = line[2:]
                name, value = line.split('=', 1)
                name = name.strip().lower()
                value = value.strip()
                metadata[name] = value

            for name, value in metadata.items():
                assert metavars.has_key(name), "Bad name %r (must be one of %s)" % (name, ', '.join(metavars.keys()))
                setattr(self.page, metavars[name], value)
            # @@: this won't work for binary pages
            self.page.text = '\n'.join(lines)
            self.page.save()

    def changeMimeType(self):
        self.assertEdit()
        self.setView('writeChangeMimeType')
        self.writeHTML()

    def simple(self):
        self.suppressFooter = True
        self.writeHTML()

    def source(self):
        mimeType = self.page.mimeType
        if mimeType in ['text/x-restructured-text', 'text/x-python']:
            mimeType = 'text/plain'
        self.response().setHeader('content-type', mimeType)
        self.write(self.page.text)

    def thumbnail(self):
        thumbnail = self.page.thumbnail
        if not thumbnail:
            raise HTTPNotFound
        self.response().setHeader('content-type', 'image/jpeg')
        self.write(self.page.thumbnail)

    ########################################
    ## Views
    ########################################

    def title(self):
        if self.page.version:
            title = '%s version %s' % (self.page.title, self.page.version)
        else:
            title = self.page.title
        return self.titlePrefix + title

    def writeHeader(self):
        if self.page.name.find('sandbox') != -1:
            self.write('<meta name="robots" content="noindex,nofollow">\n')
        SitePage.writeHeader(self)

    def link(self, action=None, unversioned=False, **kw):
        if action:
            kw['_action_'] = action
        if unversioned:
            link = self.page.wiki.linkTo(self.page.name)
        else:
            link = self.page.link
        if not kw:
            return link
        if '?' in link:
            link += '&'
        else:
            link += '?'
        link += '&'.join(['%s=%s' % (n, self.urlEncode(v))
                          for n, v in kw.items()])
        return link

    def writeContent(self):
        if self.page.hidden:
            self.assertPermission('viewhidden')
        self.write(self.page.html)
        creation = self.page.config.getbool('displaycreationdate', False)
        modified = self.page.config.getbool('displaymodifieddate', False)
        self.write('<div class="dates" align="right">\n')
        data = []
        if creation and self.page.creationDate:
            data.append(
                'Created %s'
                % format_date_relative(self.page.creationDate))
        if (modified
            and self.page.modifiedDate
            and (self.page.creationDate != self.page.modifiedDate
                 or not creation)):
            if creation and self.page.creationDate:
                data.append(
                    'Modified %s'
                    % format_date_relative(self.page.modifiedDate))
            else:
                data.append(format_date_relative(self.page.modifiedDate))

        for page, type in self.page.connections:
            desc = {'comment': 'Comment on %s',
                    'attachment': 'Attachment to %s',
                    }.get(type, '%s to %%s' % type)
            data.append(
                desc % ('<a href="%s">%s</a>' % (page.link, page.title)))
        if self.page.config.getbool('showauthor', False):
            if self.page.authorUser:
                data.append('by %s' % self.page.authorUser.signature())
            elif self.page.authorName:
                author = self.page.authorName
                if self.page.authorURL:
                    author = '<a href="%s">%s</a>' % (
                        self.page.authorURL, author)
                data.append('by %s' % author)
        if self.checkPermission(['create', 'edit'], pageClass='comment'):
            data.append('<a href="%s">Add comment</a>'
                        % self.link('comment'))
        self.write('<br>\n'.join(data).encode('UTF-8'))
        self.write('</div>\n')
        if self.page.commentPages:
            self.write('<hr noshade><h3 id="comments">Comments:</h3>\n')
            self.displayComments(self.page)

    def displayComments(self, page):
        comments = page.commentPages
        if not comments:
            return
        self.write('<blockquote>\n')
        comments.sort(lambda a, b: cmp(a.creationDate, b.creationDate))
        for comment in comments:
            self.write(comment.html)
            authorName = comment.authorName or comment.lastChangeUser
            authorName = self.htmlEncode(authorName)
            if comment.authorURL:
                authorName = '<a href="%s">%s</a>' % (
                    self.htmlEncode(comment.authorURL), authorName or 'URL')
            if comment.authorUser:
                authorName = comment.authorUser.signature()
            data = []
            if authorName:
                data = [authorName]
            showCreate = None
            if comment.config.getbool('displaycreationdate', False):
                showCreate = comment.creationDate
                data.append(format_date_relative(comment.creationDate))
            if (comment.config.getbool('displaymodifieddate', False)
                and comment.modifiedDate != showCreate):
                data.append(
                    'Modified: %s' %
                    format_date_relative(comment.modifiedDate))
            if self.checkPermission(['create', 'edit'],
                                    pageClass='comment'):
                link = comment.link + '?_action_=comment'
                data.append('<a href="%s">Reply</a>' % self.htmlEncode(link))
            perm_link = '<a href="%s">#</a>' % self.htmlEncode(comment.link)
            if data:
                data[0] = perm_link + ' ' + data[0]
            else:
                data = [perm_link]
            if data:
                self.write('<div align="right">%s</div>'
                           % '<br>\n'.join(data))
            self.write('<hr noshade>\n')
            self.displayComments(comment)
        self.write('</blockquote>\n')

    def menus(self):
        menu = SitePage.menus(self)
        menu.insert(2, 'Page')
        if not self.page.readOnly:
           menu.insert(3, 'Edit')
        return menu

    def menuPage(self):
        menu_title = self.page.title
        if len(menu_title) > 15:
            menu_title = menu_title[:14] + '&#8230;'
        menu = ('<b>%s</b>' % menu_title, [
            ('View', self.link(unversioned=True)),
            ('Source', self.page.sourceLink),
            ('Backlinks', self.link(action='backlinks', unversioned=True)),
            ('History', self.link(action='history', unversioned=True))])
        return menu

    def menuEdit(self):
        menu = []
        if self.checkPermission('edit'):
            menu = [
                ('Edit this page', self.link(action='edit')),
                ('External editor <img src="%s" width=10 height=10 border=0>'
                 % self.wiki.linkTo('edit_icon.gif'),
                 self.link(action='externalEdit'))]
        if (self.page.exists()
            and self.checkPermission(['create', 'edit'], pageClass='comment')):
            menu.append(
                ('Add comment', self.link(action='comment')))
        if (self.page.pageClass != 'attachment' and self.page.exists()
            and self.checkPermission(['create', 'edit'], pageClass='attachment')):
            menu.append(
                ('Attach file', self.link(action='attach')))
        if not menu:
            return (menubar.Literal, '')
        return ('Edit', menu)

    ## @@: CONTINUE

    def writeEdit(self):
        req = self.request()
        text = req.field('text', self.page.text)
        title = req.field('title', self.page.title)
        if not self.page.exists() and not req.hasField('title'):
            title = title.capitalize()
        htmlTitle = self.htmlEncode(title)
        log = req.field('changeLog', '')
        htmlLog = self.htmlEncode(log)
        mimeType = req.field('mimeType', self.page.mimeType)
        editField = self.editFieldFor(self.page, mimeType)
        quickFindLink = self.servletLink('quickfind', args={'callParent': 'alert'})
        if self.page.exists():
            changeLink = ''
        else:
            changeLink = '<a href="%s" class="button">change...</a>' % \
                self.pageLink(self.page.name + ".html", action='changeMimeType',
                args={'commenting': req.field('commenting', None)})
        if self.canPreview(self.page, mimeType):
            previewButton = '<input type="submit" name="_action_preview" value="Preview">'
        else:
            previewButton = ''
        if req.field('commenting', ''):
            commenting = ('<input type="hidden" name="commenting" value="%s">'
                          % self.htmlEncode(req.field('commenting')))
        else:
            commenting = ''

        if req.field('attaching', ''):
            attaching = ('<input type="hidden" name="attaching" value="%s">'
                         % self.htmlEncode(req.field('attaching')))
        else:
            attaching = ''
        mimeHelpLink = self.helpLink('mimetypes', 'Help on MIME types')
        relatedAdd = self.popupLink('quickfind?callParent=relatedAdd', 'Add...')
        relatedHelpLink = self.helpLink('relatedterms', 'Help on related terms')
        if self.checkPermission('hide'):
            if (self.page.hidden
                or req.field('hidden', '')
                or not self.page.exists()
                and self.wiki.config.getbool('starthidden', False)):
                hiddenChecked = ' checked'
            else:
                hiddenChecked = ''
            hidden = ('<label for="hide_check">&nbsp; Hide: '
                '<input type="checkbox" name="hidden" id="hide_check"%s>'
                '%s</label>' % (hiddenChecked,
                self.helpLink('hiddenpages', 'Help on hidden pages')))
        else:
            hidden = ''
        action = self.link()

        if not self.user():
            name, email, url = map(self.htmlEncode, self.cookieAuthorInfo())
            metaFields = dedent('''\
                <table>
                <tr><td><label for="authorName">Your name:</label></td>
                <td><input type="text" name="authorName" value="%s" size=20
                id="authorName">
                </td></tr>
                <tr><td><label for="authorEmail">Your email:</label></td>
                <td><input type="text" name="authorEmail" value="%s" size=20
                id="authorEmail">
                <small><i>(will not be displayed)</i></small>
                </td></tr>
                <tr><td><label for="authorURL">URL:</label></td>
                <td><input type="text" name="authorURL" value="%s" size=30
                id="authorURL">
                </td></tr>
                </table>''' % (name, email, url))
        else:
            metaFields = ''
        if self.page.exists():
            describe = dedent('''\
                Describe your changes:<br>
                <input type="text" name="changeLog" size=30
                style="width: 100%%" value="%(htmlLog)s"><br>
                ''' % locals())
        else:
            describe = ''
        self.write(dedent('''\
            <form action="%(action)s" method="POST" enctype="multipart/form-data" name="f">
            <input type="text" name="title" value="%(htmlTitle)s" size=30 style="font-size: large">
            <input type="hidden" name="mimeType" value="%(mimeType)s">
            %(commenting)s
            %(attaching)s
            MIME type:
            <tt>%(mimeType)s</tt>
            %(changeLink)s
            %(mimeHelpLink)s
            <br>

            %(editField)s
            <br>

            %(describe)s

            <script type="text/javascript">
            function relatedAdd(name, mimeType, title) {
                var field = document.forms.f.elements.keywords;
                if (field.value) {
                    field.value += ", ";
                }
                field.value += name;
            }
            </script>

            %(hidden)s<br>
            %(metaFields)s
            ''' % locals()))
        self.write(dedent('''\
            <input type="submit" name="_action_save" value="Save">
            %(previewButton)s
            <input type="submit" name="_action_cancel" value="Cancel">
            </form>
            ''' % locals()))
        if req.field('commenting', None):
            commentPage = self.wiki.page(req.field('commenting'))
            self.write('<h2>Commenting on:</h2>\n')
            self.write(commentPage.html)

    def cookieAuthorInfo(self):
        req = self.request()
        savedData = req.cookies().get('userinfo')
        if savedData:
            savedData = savedData.decode('base64')
            name, email, url = savedData.split('|')
        else:
            name = email = url = ''
        name = req.field('authorName', name)
        email = req.field('authorEmail', email)
        url = req.field('authorURL', url)
        return name, email, url

    def saveCookieAuthorInfoFromRequest(self):
        req = self.request()
        name = req.field('authorName', '')
        email = req.field('authorEmail', '')
        url = req.field('authorURL', '')
        self.saveCookieAuthorInfo(name, email, url)

    def saveCookieAuthorInfo(self, name, email, url):
        name = name.replace('|', '')
        email = email.replace('|', '')
        url = url.replace('|', '')
        if (not url.startswith('http://')
            and not url.startswith('https://')):
            url = 'http://' + url
        value = '%s|%s|%s' % (name, email, url)
        value = value.encode('base64')
        self.response().setCookie('userinfo', value, expires='NEVER')

    def writeEditRelated(self):
        p = self.page
        if p.relatedDateLimit:
            relatedDateLimit = p.relatedDateLimit.seconds / 60 / 60 / 24
        else:
            relatedDateLimit = ''
        self.write(dedent('''\
            <b>Summarizing options:</b> %(summarizingHelp)s<br>
            <input type="hidden" name="relatedOptions" value="yes">
            <label for="relatedSummaries">Summaries only:
            <input type="checkbox" id="relatedSummaries"
            name="relatedSummaries"%(relatedSummariesCheck)s>
            </label>
            &nbsp;
            <label for="relatedShowDates">Show dates on entries:
            <input type="checkbox" id="relatedShowDates"
            name="relatedShowDates"%(relatedShowDatesCheck)s>
            </label>
            &nbsp;
            Use date:
            <select name="relatedSortField">
            <option value="creationDate"%(creationDateSelected)s>Creation date</option>
            <option value="modifiedDate"%(modifiedDateSelected)s>Modified date</option>
            </select>
            <br>

            Date limit:
            <input type="text" name="relatedDateLimitDays" value="%(relatedDateLimit)s" size=3>
            <i style="font-size: small">days</i>
            &nbsp;
            Item limit:
            <input type="text" name="relatedEntryLimit" value="%(relatedEntryLimit)s" size=3><br>
            ''' % {
                'summarizingHelp': self.helpLink('wikisummarizing', 'Help on the Wiki\'s summarizing'),
                'relatedSummariesCheck': self.test(p.relatedSummaries, ' checked', ''),
                'relatedShowDatesCheck': self.test(p.relatedShowDates, ' checked', ''),
                'creationDateSelected': self.test(p.relatedSortField == 'creationDate', ' selected', ''),
                'modifiedDateSelected': self.test(p.relatedSortField == 'modifiedDate', ' selected', ''),
                'relatedDateLimit': relatedDateLimit,
                'relatedEntryLimit': p.relatedEntryLimit or '',
                }))

    def canPreview(self, page, mimeType):
        return mimeType.startswith('text/')

    def editFieldFor(self, page, mimeType):
        if mimeType == 'text/html':
            return self.editFieldHTML(page)
        elif mimeType == 'text/x-restructured-text':
            return self.editFieldRest(page)
        elif mimeType.startswith('text/'):
            return self.editFieldText(page)
        else:
            return self.editFieldBinary(page, mimeType)

    def editFieldText(self, page):
        req = self.request()
        text = req.field('text', page.text)
        return ('<textarea name="text" rows=20 cols=50 '
                'style="width: 100%%">%s</textarea>\n'
                '<input type="hidden" name="inputType" value="textarea">'
                % self.htmlEncode(text))

    def editFieldRest(self, page):
        req = self.request()
        text = req.field('text', page.text)
        # Code for selection from:
        # http://www.alexking.org/blog/2003/06/02/inserting-at-the-cursor-using-javascript/
        text = self.htmlEncode(text)
        markupHelpLink = str(self.helpLink('quickresthelp',
            '   help on markup', useImage=False))
        insertLink = self.popupLink('quickfind?callParent=restlink',
            'Insert wiki link')
        return dedent('''\n
            <textarea name="text" id="text" rows=20 cols=50
             style="width: 100%%">%(text)s</textarea>
            <input type="hidden" name="inputType" value="restTextarea"><br>
            <span style="font-size: small">%(insertLink)s | %(markupHelpLink)s <i>(note:
            no HTML tags allowed)</i></span><br>
            <script type="text/javascript">
            function insertAtCursor(field, text) {
                // IE:
                if (document.selection) {
                    field.focus();
                    var sel = document.selection.createRange();
                    sel.text = text;
                }
                // Mozilla:
                else if (field.selectionStart
                         || field.selectionStart == "0") {
                    var startPos = field.selectionStart;
                    var endPos = field.selectionEnd;
                    field.value = field.value.substring(0, startPos)
                        + text
                        + field.value.substring(endPos, field.value.length);
                } else {
                    field.value += text;
                }
            }
            function restlink(name, mimeType, title) {
                var textarea = document.getElementById("text");
                var link;
                if (title.indexOf(" ") == -1) {
                    link = title + "_";
                } else {
                    link = "`" + title + "`_";
                }
                insertAtCursor(textarea, link);
            }
            </script>
            ''' % locals())

    def editFieldHTML(self, page):
        req = self.request()
        text = req.field('text', page.text)
        #if req.field('commenting', '') and not text:
        #    text = ('<br>-- <a href="%s.html">%s</a> %s\n'
        #            % (wikipage.canonicalName(self.user().name()),
        #               self.user().name(),
        #               datetime.datetime.now().strftime('%d %b \'%y')))
        return dedent('''\n
            <script type="text/javascript">
                _editor_url = '/htmlarea';
                _editor_lang = 'en';
            </script>
            <script type="text/javascript" src="htmlarea.js"></script>
            <script type="text/javascript" src="lang/en.js"></script>
            <script type="text/javascript" src="dialog.js"></script>
            <style type="text/css">
                @import url(htmlarea.css);
            </style>
            <script type="text/javascript">
                var editor = null;
                function initEditor() {
                    editor = new HTMLArea("text");
                    var cfg = editor.config;
                    cfg.registerButton({
                      id: "wikilink",
                      tooltip: "link to a wiki page",
                      image: "images/ed_wikilink.gif",
                      textMode: false,
                      action: function (editor) {
                        window.open("quickfind?callParent=wikilink", "blank_",
                            "width=400,height=500,location=yes,menubar=no,resizable=yes,scrollbars=yes,status=no,toolbar=no");
                      },
                      context: ""
                    });
                    cfg.toolbar = [
                      ["fontname", "fontsize", "formatblock", "space",
                       "bold", "italic", "separator",
                       "copy", "cut", "paste", "space",
                       "undo", "redo"],
                      ["justifyleft", "justifycenter", "justifyright", "separator",
                       "insertorderedlist", "insertunorderedlist", "outdent", "indent", "separator",
                       "forecolor", "hilitecolor", "textindicator", "separator",
                       "inserthorizontalrule", "createlink", "wikilink", "insertimage", "inserttable", "htmlmode", "separator",
                       "popupeditor", "separator",
                       "showhelp", "about"]
                    ];
                    //cfg.toolbar.push(["linebreak", "wikilink"]);
                    //cfg.imgURL = "htmlarea/images/";
                    //cfg.popupURL = "htmlarea/popups/";
                    editor.generate();
                }
                function wikilink(name, mimeType, title) {
                    editor.insertHTML(\'<a href="\' + name + \'.html">\'
                                      + title + "</a>");
                }
            </script>
            <textarea name="text" id="text" rows=30 cols=50 style="width: 100%%">%s</textarea>
            <input type="hidden" name="inputType" value="htmlarea">
            <script type="text/javascript">
                initEditor();
            </script>
            ''' % self.htmlEncode(text))

    def editFieldBinary(self, page, mimeType):
        text = self.request().field('text', page.text)
        if text != page.text:
            saveText = text
        else:
            saveText = ''
        src = ''
        if saveText:
            src += ('<input type="hidden" name="text" value="base64,%s">'
                    % (saveText.encode('base64')))
        return dedent('''\
            %s
            Upload: <input type="file" name="textUpload">
            <input type="hidden" name="inputType" value="upload"><br>
            Comments:<br>
            <textarea name="comments" style="width: 100%%" rows=3 cols=60 wrap="SOFT">%s</textarea>
            ''' % (src, self.htmlEncode(page.comments)))

    def writePreview(self):
        req = self.request()
        text = req.field('text', '')
        if req.hasField('text_upload'):
            uploaded = req.field('text_upload')
            try:
                uploaded = uploaded.file.read()
            except AttributeError:
                pass
            if uploaded:
                text = uploaded
        if req.hasField('old_upload') and not text:
            filename = self.getSecureHidden('old_upload')
            # @@: continue
        mimeType = req.field('mimeType')
        inputType = req.field('inputType')
        text = self._inputTypeCleaners.get(inputType, lambda x:x)(text)
        self.write(self.page.preview(text, mimeType))
        self.write('<hr noshade>\n')
        self.writeEdit()

    def writeHistory(self):
        if self.request().field('delete', None):
            versions = self.request().field('deleteVersion', None)
            if isinstance(versions, (str, unicode)):
                versions = (versions,)
            elif isinstance(versions, list):
                versions = tuple(versions)
            try:
                versions = map(int, versions)
            except:
                versions = None
            if versions:
                for page in self.page.versions():
                    if page.version in versions:
                        self.assertPermission('delete', page=page)
                delete = self.request().field('deleteUsers', None)
                if delete:
                    self.assertPermission('deleteuser')
                users = self.page.delete(versions)
                self.write('<p>Selected versions deleted.</p>')
                myusername = self.user() and self.user().username()
                if delete and users:
                    deleted = []
                    for username in users:
                        if username != myusername:
                            try:
                                user = self.userManager().userForUsername(username)
                                self.userManager().deleteUser(user)
                                deleted.append(username)
                            except:
                                pass
                    if deleted:
                        msg = 'Users deleted: ' + ', '.join(deleted)
                        # @@ we should change ownership of all remaining pages of users
                    elif myusername in users:
                        msg = 'No hara-kiri allowed.'
                    else:
                        msg = 'Users were already deleted.'
                    self.write('<p>%s</p>' % msg)
        versions = self.page.versions()
        if not versions:
            self.write('<p>There are no archived versions available.</p>')
            return
        delete = False
        for page in versions:
            if self.checkPermission('delete', page=page):
                delete = True
                break
        self.write('<form action="%s" method="GET">'
            % (self.link(unversioned=True)))
        self.write('<input type="hidden" name="_action_" value="diff">\n')
        header = ['Version', 'Created on', 'Log', 'User', 'Compare']
        if delete:
            header.append('Delete')
        header = ''.join(['<th>%s</th>' % h for h in header])
        self.write('<table><tr class="header">%s</tr>\n' % header)
        firstIndex = len(versions)-2
        otherIndex = firstIndex+1
        for index, page in enumerate(versions):
            self.write('<tr class="%s">\n' %
                       ['odd', 'even'][index%2])
            self.write('<td style="text-align: center">'
                '<a class="version" href="%s">%s</a></td>\n'
                % (page.link, page.version or 'current'))
            self.write('<td>%s</td>\n' % self.format_date(page.modifiedDate, nonbreaking=True))
            self.write('<td>%s</td>\n'
                % self.htmlEncode(page.lastChangeLog or ''))
            self.write('<td>%s</td>\n'
                % self.htmlEncode(page.lastChangeUser or ''))
            self.write('<td style="text-align: center">'
                '<input type="radio" name="firstVersion" value="%s"%s>'
                '<input type="radio" name="otherVersion" value="%s"%s></td>\n'
                % (page.version, test(index==firstIndex, ' checked'),
                    page.version, test(index==otherIndex, ' checked')))
            if delete:
                if self.checkPermission('delete', page=page):
                    self.write('<td style="text-align: center">'
                        '<input type="checkbox" name="deleteVersion" value="%s">' % page.version)
                else:
                    self.write('<td>&nbsp;</td>')
            self.write('</tr>\n')
        if delete and self.checkPermission('deleteuser'):
            self.write('<tr><td colspan="5" style="text-align: right">'
                'Check this if you want to delete the user accounts as well:'
                '</td><td style="text-align: center">'
                '<input type="checkbox" name="deleteUsers" value="yes"></td></tr>')
        self.write('</table>')
        self.write('<input type="submit" name="compare_brief" value="Compare content">\n')
        self.write('<input type="submit" name="compare_thorough" value="Compare complete">\n')
        self.write('<input type="submit" name="compare_source" value="Compare source">\n')
        if delete:
            self.write('<input type="submit" name="delete" value="Delete">\n')
        self.write('</form>\n')

    def writeBacklinks(self):
        self.write('<table>\n')
        for index, page in enumerate(self.page.backlinks):
            self.write('<tr class="%s"><td><a href="%s">%s</a>'
                       '</td></tr>\n'
                       % (['odd', 'even'][index%2],
                          page.link,
                          page.title))
        self.write('</table>\n')

    def writeDiff(self):
        compType = 'thorough'
        for name in self.request().fields().keys():
            if name.startswith('compare_'):
                compType = name[len('compare_'):]
        if compType == 'thorough':
            Matcher = htmldiff.HTMLMatcher
            source1 = self.firstPage.html
            source2 = self.otherPage.html
        elif compType == 'brief':
            Matcher = htmldiff.NoTagHTMLMatcher
            source1 = self.firstPage.html
            source2 = self.otherPage.html
        elif compType == 'source':
            Matcher = htmldiff.TextMatcher
            source1 = self.firstPage.text
            source2 = self.otherPage.text
        else:
            assert 0, "Unknown comparison type: %r" % compType
        matcher = Matcher(source1, source2)
        diff = matcher.htmlDiff()
        start = 'version %s' % (self.firstPage.version or 'Current')
        end = 'version %s' % (self.otherPage.version or 'Current')
        self.write('<p><span class="insert">Added to %s (present in %s)</span><br>'
            '<span class="delete">Deleted from %s (present in %s)</span></p>\n'
            % (start, end, end, start))
        self.write(diff)

    def writeChangeMimeType(self):
        req = self.request()
        self.write('<p>Current MIME type: <tt>%s</tt>\n%s</p>\n'
            % (self.page.mimeType,
               self.helpLink('mimetypes', 'Help on MIME types')))
        self.write('<p>Edit with a different MIME type:</p>\n')
        allTypes = [t for t in self.wiki.availableMimeTypes
                    if not t.startswith('image/')]
        allTypes.append('image/*')
        for mimeType in allTypes:
            self.write('<a href="%s" class="menu">%s</a>\n'
                       % (self.pageLink(self.page.name,
                                        action='edit',
                                        args={'mimeType': mimeType,
                                              'commenting': req.field('commenting', None)}),
                          mimeType))

    _linkRE = re.compile('href\s*=\s*"(.*?)"', re.I+re.S)
    def cleanHTMLArea(self, text):
        if tidy:
            text = tidy.parseString(
                text,
                break_before_br=True,
                show_body_only=True,
                char_encoding='utf8')
        text = self._linkRE.sub(self._urlSubber, str(text))
        return text

    def _urlSubber(self, match):
        url = match.group(1)
        baseLink = self.servletLink('', absolute=True)
        if url.startswith(baseLink):
            url = url[len(baseLink):]
        return 'href="%s"' % url
