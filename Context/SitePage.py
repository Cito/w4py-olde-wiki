from Component import CPage
import sys
sys.path.append('/home/ianb/w4py.org/home/ianb/Wiki')
from lib import wiki
from lib import wikiconfig
from lib.formatdate import format_date
import os
import datetime
from Component.notify import NotifyComponent
from LoginKit.rfc822usermanager import RFC822UserManager
from LoginKit import UserComponent
from lib import user
from lib.securehidden import SecureSigner
from WebKit.ImportSpy import modloader
from WebKit import AppServer
import shutil
from TaskKit.Task import Task
from TaskKit.Scheduler import Scheduler
import time
from lib import menubar
from lib.common import pprint, dprint, dedent
from WebKit.HTTPExceptions import *

__all__ = ['SitePage', 'pprint', 'dprint']

class SitePage(CPage):

    components = [NotifyComponent()]
    _adsenseID = None

    def awake(self, transaction):
        CPage.awake(self, transaction)
        domain = self.request().environ().get('HTTP_HOST', 'SERVER_NAME')
        if ':' in domain:
            domain = domain.split(':')[0]
        self.wiki = self.TheGlobalWiki.site(domain=domain)
        self.wiki.basehref = self.request().adapterName() + '/'
        self.suppressFooter = False
        self.response().setHeader(
            'content-type', 'text/html; charset=utf-8')
        self.setupEarly()
        self.config = self.wiki.config.merge_page_class(self.pageClass())
        if self._adsenseID is None:
            SitePage._adsenseID = self.config.get('googleadsenseid', '')
        self.assertPermission('view', self.pageClass())
        self.setup()

    def setupEarly(self):
        """
        This is called before setup(), and before we resolve .pageClass()
        (which gets used to create the config).  Most pages should
        override seutp() instead.
        """
        pass

    def setup(self):
        pass

    def checkPermission(self, *args, **kw):
        try:
            self.assertPermission(*args, **kw)
            return True
        except (HTTPAuthenticationRequired, HTTPForbidden):
            return False

    _cachedPermissions = {}

    def assertPermission(self, action='view', pageClass=None, page=None):
        if isinstance(action, (str, unicode)):
            action = (action,)
        elif isinstance(action, list):
            action = tuple(action)

        userID = self.user() and self.user().userID()
        if not page:
            cacheKey = (userID, action, pageClass)
            try:
                result = self._cachedPermissions[cacheKey]
                if result == 'auth':
                    raise HTTPAuthenticationRequired
                elif result:
                    raise HTTPForbidden(result)
                else:
                    return
            except KeyError:
                pass

        if pageClass is not None and pageClass != self.pageClass():
            config = self.wiki.config.merge_page_class(pageClass)
        else:
            config = self.config
        config_section = None
        for actual_action in action:
            config_section = config.get(actual_action)
            if config_section:
                break
        if not config_section:
            msg = ("You must configure the roles to %s this page"
                   % actual_action)
            if not page:
                self._cachedPermissions[cacheKey] = msg
            raise HTTPForbidden(msg)
        role = config_section.get('requiredrole', 'none').strip().lower()
        role = filter(None, role.split())
        if not role or role == ['none']:
            if not page:
                self._cachedPermissions[cacheKey] = None
            return
        if not self.user():
            if not page:
                self._cachedPermissions[cacheKey] = 'auth'
            raise HTTPAuthenticationRequired
        if 'user' in role:
            if not page:
                self._cachedPermissions[cacheKey] = None
            return
        user_roles = self.user().roles()
        if userID:
            if page:
                authorID = page.authorUser and page.authorUser.userID()
            else:
                authorID = self.authorUser() and self.authorUser().userID()
            if userID == authorID:
                user_roles.append('author')
        for has_role in user_roles:
            if has_role in role:
                if not page:
                    self._cachedPermissions[cacheKey] = None
                return
        msg = ("You must have the role <b>%s</b> to %s this page"
               % (' or '.join(role), actual_action))
        if not page:
            self._cachedPermissions[cacheKey] = msg
        raise HTTPForbidden(msg)

    ########################################
    ## Utility methods
    ########################################

    def loginRequired(self):
        return False

    def pageClass(self):
        return 'posting'

    def authorUser(self):
        return None

    def writeSimplePageList(self, pages):
        self.write('<table>')
        for index, page in enumerate(pages):
            self.write('<tr class="%s"><td><a href="%s">%s</a></td></tr>\n'
                       % (['even', 'odd'][index%2],
                          page.link,
                          page.title))
        self.write('</table>\n')

    def test(self, op, t, f):
        if op:
            return t
        else:
            return f

    def encodeArgs(self, args=None):
        q = self.urlEncode
        if args is None:
            args = self.request().fields()
        if isinstance(args, dict):
            args = args.items()
        all = []
        for name, value in args:
            if isinstance(value, str):
                all.append((name, value))
            else:
                for v in value:
                    all.append((name, v))
        return '&'.join([
            '%s=%s' % (q(name), q(value))
            for name, value in all])

    ########################################
    ## Page layout
    ########################################

    def writeHeadParts(self):
        CPage.writeHeadParts(self)
        self.writeRelatedLinks()
        self.writeJavascript()

    def writeRelatedLinks(self):
        self.write('<link rel="alternate" type="application/rss+xml" title="Recent Changes" href="%s">\n'
                   % self.wiki.linkTo('feeds/recent_changes.xml'))
        self.write('<link rel="alternate" type="application/rss+xml" title="New Posts" href="%s">\n'
                   % self.wiki.linkTo('feeds/new_pages.xml'))

    def writeStyleSheet(self):
        self.write('<link rel="stylesheet" href="%s/wiki.css" type="text/css">\n'
                   % self.request().adapterName())

    def writeJavascript(self):
        self.write('<script type="text/javascript" src="%s/menubar.js"></script>\n'
                   % self.request().adapterName())

    def writeBodyParts(self):
        self.writeHeader()
        self.writeMessages()
        self.viewMethod()()
        self.writeFooter()

    def writeHeader(self):
        menu = [getattr(self, 'menu' + name)() for name in self.menus()]
        bar, parts = menubar.menubarHTML(menu)
        self.write(parts)
        self.write('<form action="search" method="GET">')
        self.write(bar)
        self.write('</form>')
        #self.write('<br clear="all">\n')
        self.writeGoogleAds()
        if self.htTitle():
            self.write('<h1>%s</h1>\n' % self.htTitle())

    def writeGoogleAds(self):
        if not self._adsenseID:
            return
        self.write(dedent('''\
            <script type="text/javascript"><!--
            google_ad_client = "%s";
            google_ad_width = 120;
            google_ad_height = 600;
            google_ad_format = "120x600_as";
            google_ad_channel ="";
            google_color_border = "336699";
            google_color_bg = "FFFFFF";
            google_color_link = "0000FF";
            google_color_url = "008000";
            google_color_text = "000000";
            //--></script><table align="right" cellspacing=0 border=0 cellpadding=0><tr><td>
            <script type="text/javascript"
              src="http://pagead2.googlesyndication.com/pagead/show_ads.js">
            </script></td></tr></table>''' % self._adsenseID))

    def menus(self):
        return ['User', 'Title', 'Goto', 'Help', 'Search']

    def menuUser(self):
        name = self.user() and self.user().username()
        if name:
            name = '<span class="menuUser">%s</span>' % name
        else:
            name = ''
        return (menubar.Literal, name)

    def menuTitle(self):
        return (menubar.Literal, '<span class="menuTitle">%s:</span>'
            % (self.wiki.config.getbool('blog', False) and 'Blog' or 'Wiki'))

    def menuGoto(self):
        menu = [
            ('Home', self.wiki.basehref),
            ('Recent Changes', self.wiki.basehref + 'recentchanges'),
            ('Orphaned Pages', self.wiki.basehref + 'orphans'),
            ('Wanted Pages', self.wiki.basehref + 'wanted'),
            ]
        if self.checkPermission(action='edit',
                pageClass='posting'):
            menu.append(('Create %s' % (self.wiki.config.getbool('blog',
                'False') and 'Post' or 'Page'),
                "javascript:window.location='%s/' + "
                "escape(window.prompt('Enter the name "
                "for the new page').replace(/ /g, '-')) + "
                "'?_action_=edit'"
                % self.request().adapterName()))
        if self.user() and 'admin' in self.user().roles():
            menu.append(('Administration', self.wiki.basehref + 'admin'))
        menu.append((menubar.Separator, ''))
        if self.user():
            menu.append(('Logout', '?_actionLogout=yes'))
        else:
            menu.append(('Login', self.wiki.basehref + 'login?returnTo=%s'
                % self.request().environ()['REQUEST_URI'].split('?')[0]))
        return ('Goto', menu)

    def menuHelp(self):
        return ('Help', [
            ('About this wiki', self.wiki.basehref + 'thiswiki.html'),
            ('Help with markup', self.wiki.basehref + 'quickresthelp.html'),
            (menubar.Separator, ''),
            ('Related terms', self.wiki.basehref  + 'relatedterms.html'),
            ])

    def menuSearch(self):
        return (menubar.Literal,
                 '&nbsp; &nbsp; <input type="text" class="menuSearch" '
                 'name="search" value="click to search..." '
                 'onFocus="if (this.value == \'click to search...\') '
                 '{this.value = \'\'; this.style.color = \'#000000\';}" '
                 'style="color: #666666">')

    def sendRedirectAndEnd(self, url):
        """
        This alternate version of sendRedirectAndEnd checks if we are
        setting any cookies, and if so and the user is also using
        Internet Explorer, then we do the redirect with Javascript
        instead of with HTTP headers.
        """
        if not self.response().cookies():
            # If there aren't any cookies, then we always do the
            # full redirect
            return CPage.sendRedirectAndEnd(self, url)
        req = self.request()
        agent = req.environ().get('HTTP_USER_AGENT')
        if not agent or agent.find('MSIE') == -1:
            return CPage.sendRedirectAndEnd(self, url)
        # Otherwise we're dealing with MSIE, which has problems
        # with setting cookies and then immediately redirecting.
        self.write('<html><head><meta http-equiv="refresh" '
                   'content="1; %s"><title>Redirecting</title>'
                   % self.htmlEncode(url))
        self.write('<script language="JavaScript"><!--\n')
        self.write('document.location.replace(%r);\n//--></script>'
                   % url)
        self.write('</head><body><h1>Redirecting...</h1>')
        self.write('Redirecting to <a href="%s">%s</a>...'
                   % (self.htmlEncode(url), url))
        self.write('</body></html>')
        self.endResponse()

    def format_date(self, date, nonbreaking=False):
        return format_date(date, nonbreaking=nonbreaking)

    def popupLink(self, link, text):
        return ('<a href="%s" onClick="'
            "window.open('%s','"
            'width="400",height="500",location=yes,menubar=no,'
            'resizable=yes,scrollbars=yes,status=no,toolbar=no'
            "'); return false"
            '">%s</a>' % (link, link, text))

    def helpLink(self, dest, text, useImage=True):
        if useImage:
            text = ('<img src="question_icon.gif" alt="help" title="%s"'
                ' width="15" height="15" border="0">' % text)
        link = self.wiki.page(dest).link
        return self.popupLink(link, text)

    def pageLink(self, name, action=None, args=None):
        args = args or {}
        if action:
            args['_action_'] = action
        argsRendered = ['%s=%s' % (self.urlEncode(n), self.urlEncode(v))
                        for (n, v) in args.items()
                        if v is not None]
        url = self.request().adapterName() + '/' + name
        if argsRendered:
            if '?' in url:
                url = url + '&'
            else:
                url = url + '?'
            url = url + '&'.join(argsRendered)
        return url

    def secureHidden(self, name, value, timeout=None):
        return ('<input type="hidden" name="%s" value="%s">' %
            (name,
             self.htmlEncode(self._secureSigner.secureValue(value, timeout=timeout))))

    def getSecureHidden(self, name):
        return self._secureSigner.parseSecure(self.request().field(name))

    def htmlEncode(self, s):
        if isinstance(s, unicode):
            s = s.encode('UTF-8')
        return CPage.htmlEncode(self, s)

    def write(self, s):
        try:
            CPage.write(self, s)
        except UnicodeDecodeError:
            CPage.write(self, s.encode('UTF-8'))

############################################################
## Global setup
############################################################

thisDir = os.path.dirname(__file__)
parentDir = os.path.dirname(thisDir)
configFilename = AppServer.globalAppServer.serverSidePath('Configs/wiki.ini')
if not os.path.exists(configFilename):
    configTemplateFilename = os.path.join(parentDir, 'wiki.ini')
    print "Coping %s -> %s" % (configTemplateFilename, configFilename)
    shutil.copyfile(configTemplateFilename,
                    configFilename)
config = wikiconfig.WikiConfig()
config.load(configFilename)
modloader.watchFile(configFilename)
TheGlobalWiki = wiki.GlobalWiki(config)
for filename in os.listdir(thisDir):
    if filename.endswith('.py'):
        TheGlobalWiki.addSpecialName(filename[:-3])
TheGlobalWiki.addSpecialName('rss')

SitePage.TheGlobalWiki = TheGlobalWiki

user_path = TheGlobalWiki.config.get('userpath')
if user_path is None:
    user_path = os.path.join(TheGlobalWiki.root, 'users')
manager = RFC822UserManager(path=user_path,
                            userClass=user.WikiUser)
user.manager = manager
SitePage.components.append(UserComponent(manager, loginServlet='/login'))
signatureFilename = os.path.join(TheGlobalWiki.root, 'secret.txt')
SitePage._secureSigner = SecureSigner(signatureFilename)

class PublishTask(Task):

    def __init__(self, globalWiki):
        self.globalWiki = globalWiki

    def run(self):
        for wiki in self.globalWiki.cachedWikis.values():
            wiki.publish()

scheduler = Scheduler()
scheduler.start()
scheduler.addPeriodicAction(time.time(), 10, PublishTask(TheGlobalWiki),
                            'PublishTask')

