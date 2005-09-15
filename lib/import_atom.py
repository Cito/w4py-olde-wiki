import feedparser
from common import htmlEncode, canonicalName, guessURLName
from datetime import datetime, timedelta
import time

def import_atom(wiki, atom_file, logger):
    feed = feedparser.parse(atom_file)
    logger('Importing feed titled <a href="%s">%s</a>'
           % (feed.feed.get('link', '(unknown)'), htmlEncode(feed.feed.title)))
    redirects = []
    for entry in feed.entries:
        import_entry(wiki, entry, logger, redirects)
    return redirects

def import_entry(wiki, entry, logger, redirects):
    title = entry.title
    name = guessURLName(title)
    base = ''
    while wiki.exists(name + str(base)):
        if not base:
            base = 1
        else:
            base += 1
    name = name + str(base)
    page = wiki.page(name)
    page.title = title
    if entry.get('modified_parsed'):
        modified_date = datetime(*entry.modified_parsed[:7])
        page.createdDate = modified_date
    id = entry.get('id')
    if id:
        try:
            page.atomID = id
        except ValueError, e:
            logger("Could not set ATOM ID to %r for page %s; error: %s"
                   % (id, name, e))
    ## @@: currently summary is not persistent
    # summary = entry.summary
    contents = entry.content
    page.mimeType = str(contents[0]['type'])
    page.text = '\n'.join([c['value'] for c in contents])
    page.pageClass = 'posting'
    page.creationDate = time.mktime(convert_date(entry.issued).timetuple())
    author = entry.get('author_detail')
    if author and author.get('name'):
        author_name = author['name']
        if author.get('name'):
            page.authorName = author.name
        if author.get('email'):
            page.authorEmail = author.email
        if author.get('url') and author.url.lower().strip() != 'http://':
            page.authorURL = author.url
        if author.get('email'):
            author_name = '%s <%s>' % (author_name, author['email'])
        page.lastChangeUser = author_name
    parents = [link for link in entry.links if link.rel == 'parent']
    if parents:
        page.pageClass = 'comment'
        for parent in parents:
            parentPage = wiki.pageByAtomID(parent.href)
            if not parentPage:
                logger('Parent page not found: %r' % parent.href)
                print "Not found: %r" % parent.href
                continue
            page.connections += [(parentPage, 'comment')]
            logger('%s a comment on %s'
                   % (title, parentPage.name))
            print "%s -> %s" % (title, parentPage.name)
    page.save()
    logger("Saved page %s as %s"
           % (title, name))
    print "Imported %s" % name
    if entry.has_key('link'):
        redirects.append((entry.link, page.link))
    
def convert_date(isodate):
    date, time_part = isodate.split('T', 1)
    year, month, day = date.split('-', 2)
    if '-' in time_part:
        pos = time_part.find('-')
    elif '+' in time_part:
        pos = time_part.find('+')
    else:
        pos = -1
    if pos != -1:
        time_part, tz = time_part[:pos], time_part[pos:]
    else:
        tz = ''
    hour, minute, second = time_part.split(':', 2)
    result = datetime(
        int(year), int(month), int(day),
        int(hour), int(minute), int(second))
    if tz:
        plus_minus = tz[0]
        if plus_minus == '-':
            mult = -1
        else:
            mult = 1
        hour_offset, minute_offset = tz[1:].split(':', 1)
        delta = timedelta(hours=mult*int(minute_offset),
                          minutes=mult*int(hour_offset))
        result += delta
    return result
        
