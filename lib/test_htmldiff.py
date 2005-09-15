"""
datatest.util.htmldiff

Compares two HTML strings and provides intelligent feedback on how
they differ.

htmlcompare() and htmlcompareError() are the most useful functions.
They compare source HTML to a 'pattern' HTML (which can contain
wildcards).  The two strings are compared for semantic equivalence,
not exact equality -- whitespace in text is normalized, tag case is
normalized, and attribute order is ignored.

These wildcards are allowed:

``*`` *alone* in text will match any text or tags.  (Note, you cannot
use ``*text`` to match ``some text``) It will consume the source until
a matching tag is found (even if by consuming more it could have
caused a match).

The ``<any>`` tag will match any tag (start or end), or any single
piece of text.

A tag with the any attribute (like ``<a any>``) will match any
attributes (though the tag itself must match).  If you include the any
attribute and other attributes, those other attributes must match (but
extra attributes will be ignored).

An attribute like ``any-href`` will allow the source to include any
value for ``href``, or to exclude it altogether.  ``href=\"*\"`` will
match any value for the ``href`` attribute, but will require that the
attribute exists in the source.

Usage:

    >>> from datatest.util.htmldiff import htmlcompareError
    >>> from datatest.util.doctestprinter import printer
    >>> printer(htmlcompareError('<a href=\"something\">', '<a href=\"*\">'))
    None
    >>> printer(htmlcompareError('<a href=\"something\">a tag</a>', '<a href=\"something\">different tag</a>'))
    Error: 'a tag' does not match 'different tag'
    ============================================================
    Source(1:20):
    .
    <a href=\"something\">((|))a tag</a>
    ------------------------------------------------------------
    Pattern(1:20):
    .
    <a href=\"something\">((|))different tag</a>

"""

from HTMLParser import HTMLParser, HTMLParseError
import cgi, re
from cStringIO import StringIO
import os

def simplify(html):
    """
    Tokenizes an HTML string, using HTMLSimplifier.
    """
    s = HTMLSimplifier()
    try:
        s.feed(html)
    except HTMLParseError, e:
        raise HTMLParseError, "%s in %s" % (e, html)
    s.close()
    return s.data()

class HTMLSimplifier(HTMLParser):

    """
    HTML tokenizer; tokenizes HTML into a stream of text and tags.
    Does not parse the structure of the text, just the stream of
    symbols.

    The output is a list of three-tuples, where the first item is the
    tag name (or 'comment' for comments, or 'text' for text), the
    second item is the data -- a dictionary of attributes, None for
    end tags, and the text for comments and text.  The third item is
    the position in the text.

    Text is normalized -- whitespace is collapsed into a single space,
    and leading and trailing whitespace is removed.
    """

    def reset(self):
        self.tags = []
        HTMLParser.reset(self)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs), self.getpos()))

    def handle_endtag(self, tag):
        self.tags.append((tag, None, self.getpos()))

    def handle_comment(self, data):
        # @@: For some reason, comments are being treated like text.
        self.tags.append(('comment', data, self.getpos()))

    def handle_data(self, data):
        if self.tags and self.tags[-1][0] == 'text':
            self.tags[-1][1] += data
        else:
            self.tags.append(['text', data, self.getpos()])

    def data(self):
        result = []
        for tag in self.tags:
            if tag[0] == 'text':
                text = self.normalizeText(tag[1])
                if text:
                    result.append(('text', text, tag[2]))
            else:
                result.append(tag)
        return result

    def normalizeText(self, html):
        html = re.sub(r'[ \n\t\r]+', ' ', html)
        return html.strip()

def htmlcompare(source, pattern, wildcard='*'):
    """
    Compare source and pattern HTML.

    Both source and pattern are expected to be strings.  Both will be
    simplified (using `simplify`) and run through `compareTags`.  If
    the two match None is returned (because matches are boring),
    otherwise (description, sourcePos, patternPos) is returned, where
    description describes, in English, the problem, and sourcePos and
    patternPos point to the last place where the two strings matched.
    """
    source = simplify(source)
    pattern = simplify(pattern)
    v = ([], [])
    try:
        while source and pattern:
            v[0].append(source)
            v[0].append(pattern)
            source, pattern = compareTags(source, pattern,
                                          wildcard=wildcard)
    except MismatchError, e:
        return (e.mismatch, e.sourcePos, e.patternPos)
    return None
    
def htmlcompareError(source, pattern, wildcard='*'):
    """
    Compares the source and pattern, returning None if they match, or a
    helpful (string) error message if they do not.

    The error message describes the difference, and displays the
    source and pattern text with '((|))' where they start to differ.
    """
    val = htmlcompare(source, pattern, wildcard=wildcard)
    if not val:
        return None
    msg, spos, dpos = val
    out = StringIO()
    out.write("Error: %s\n" % msg)
    out.write('='*60+'\n')
    if spos:
        out.write("Source(%i:%i):\n" % spos)
        before, after = cutString(source, spos)
        out.write(before)
        out.write(errorMarker())
        out.write(after.rstrip())
        out.write('\n')
    else:
        out.write('Source:\n')
        out.write(source + "\n")
    out.write('-' * 60 + "\n")
    if dpos:
        out.write('Pattern(%i:%i):\n' % dpos)
        before, after = cutString(pattern, dpos)
        out.write(before)
        out.write(errorMarker())
        out.write(after.rstrip())
        out.write('\n')
    else:
        out.write('Pattern:\n')
        out.write(pattern + "\n")
    return out.getvalue()


def compareTags(source, pattern, wildcard='*'):
    """
    Compares two lists of tags, as produced by
    simplify/HTMLSimplifier.

    Consumes the first tag, and returns the
    remaining tags.  It may consume more than one tag if wildcards are
    used.  Raises MisMatchError if the source and pattern don't match.

    pattern can have wildcards.  A portion of text that consists of only
    '*' will match any text (but globbing is not supported, i.e.,
    'item*' won't match 'items', or even 'item').  A wildcard will
    match multiple pieces of text or tags until it finds a match for
    the next token.  So '*<b>stuff</b>' will match 'some <i>great</i>
    <b>stuff</b>', but *won't* match 'some <b>bad</b> <b>stuff</b>'
    (because the first <b> will be matched, but 'bad' != 'stuff').

    You'll usually use htmlcompare()
    """
    if not source and not pattern:
        return source, pattern
    if not source:
        raise MismatchError("short source", None, pattern[0][2])
    if not pattern:
        raise MismatchError("source too long", source[0][2], None)
    if pattern[0][0] == 'text' and pattern[0][1] == wildcard:
        pattern = pattern[1:]
        while 1:
            if not pattern:
                return [], []
            if not source:
                return compareTags(source, pattern, wildcard=wildcard)
            if tagMatch(source[0], pattern[0], wildcard=wildcard):
                source = source[1:]
                pattern = pattern[1:]
                break
            source = source[1:]
        return source, pattern
    else:
        if tagMatch(source[0], pattern[0], wildcard=wildcard):
            return (source[1:], pattern[1:])
        else:
            raise MismatchError("%s does not match %s" %
                                (_shorten(formatData(source[0])),
                                 _shorten(formatData(pattern[0]))),
                                source[0][2], pattern[0][2])

def _shorten(v, length=40):
    v = repr(v)
    if len(v) > length:
        v = v[:15] + "..." + v[-15:]
    return v

def tagMatch(source, pattern, wildcard='*'):
    """
    Matches two 'tags', which can be an HTML opening tag, end tag,
    comment, or text.

    pattern can have special signifiers to relax the matching.  <any>
    will match any single tag or piece of text.  If you include an any
    attribute, like <a any=\"\">, then any extra attributes in the
    source will be ignored for the comparison.  If you use * in an
    attribute, like <a href=\"*\">, then any text in that attribute
    will be matched (but the attribute must exist).  If <a
    any-href=\"\"> is found, then href may exist or not (but if it
    exists, then it must match).
    """
    if pattern[0] != 'any' and source[0] != pattern[0]:
        # Tags don't match
        return 0
    if pattern[0] in ['comment', 'text']:
        if pattern[1].strip() == wildcard:
            return 1
        return pattern[1] == source[1]
    if pattern[1] is None:
        if source[1] is None:
            # Both are end tags
            return 1
        else:
            return 0
    elif source[1] is None:
        return 0
    patternd = pattern[1].copy()
    sourced = source[1].copy()
    if patternd.has_key('any'):
        del patternd['any']
        any = 1
    else:
        any = 0
    for key, value in patternd.items():
        if key.startswith('any-'):
            if sourced.has_key(key[4:]):
                del sourced[key[4:]]
            del patternd[key]
        elif value == wildcard:
            del patternd[key]
            if not sourced.has_key(key):
                return 0
            del sourced[key]
        elif any:
            if sourced.has_key(key) and sourced[key] != value:
                return 0
        else:
            if not sourced.has_key(key) or sourced[key] != value:
                return 0
            else:
                del sourced[key]
    if not any and sourced:
        return 0
    return 1

class MismatchError(AssertionError):
    """
    The error produced when HTML doesn't match.
    """
    def __init__(self, mismatch, sourcePos, patternPos, *args):
        self.sourcePos = sourcePos
        self.patternPos = patternPos
        self.mismatch = mismatch
        Exception.__init__(self, *args)

def formatData(data):
    """
    Turns a token (as produced by simplify or HTMLSimplifier) back
    into HTML.
    """
    if data[0] == 'text':
        return cgi.escape(data[1])
    elif data[1] is None:
        return '</%s>' % data[0]
    elif data[0] == 'comment':
        return '<!--%s-->' % data[1]
    else:
        attrs = data[1].items()
        attrs.sort()
        return '<%s%s>' % \
               (data[0], ''.join([' %s="%s"' % (a, v and cgi.escape(v, 1) or '')
                                   for a, v in attrs]))

def cutString(s, pos):
    """
    Takes a source HTML string, and given pos (as returned by
    simplify/HTMLSimplifier, which is a (line, column) tuple) returns
    (before, after) split around the position.
    """
    line, offset = pos
    line -= 1
    lines = s.split('\n')
    before = '\n'.join(lines[:line]) + '\n' + lines[line][:offset]
    after = lines[line][offset:] + '\n' + '\n'.join(lines[line+1:])
    return before, after
            
def errorMarker():
    basic = '((|))'
    if os.environ.get('TERM', '') in ('xterm', 'rxvt', 'vt100'):
        return '\x1b[41;37m%s\x1b[0m' % basic
    else:
        return basic
