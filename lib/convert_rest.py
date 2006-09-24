"""
Code for rendering restructured text
"""
import traceback
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from docutils import core
from docutils.utils import SystemMessage
from docutils import nodes
from docutils.readers import standalone
from docutils.transforms import Transform

import converter_registry
from common import canonicalName, guessURLName, htmlEncode


def convert_rest(page, text, mime_type=None):
    if not text.strip():
        # ReST doesn't like empty documents
        return ''
    try:
        html = _clean_html(core.publish_string(
            source=text,
            reader=Reader(),
            parser_name='restructuredtext',
            writer_name='html',
            settings_overrides={'traceback': 1}))
        return html
    except SystemMessage, error:
        return _format_error(error, None)
    except Exception, error:
        print "Error rendering page"
        out = StringIO()
        traceback.print_exc(file=out)
        return _format_error(error, out.getvalue())

converter_registry.register(convert_rest, 'text/x-restructured-text')

def _clean_html(html):
    return html[html.find('<body>')+6:html.find('</body>')]

def _format_error(error, tb):
    if isinstance(error, SystemMessage):
        # We expect a format like col:line: (LEVEL/INT) Message\ntext
        msg = error.args[0]
        col, line, rest = msg.split(':', 2)
        level, rest = rest.split(')', 1)
        level = level.strip()[1:]
        message, text = rest.split('\n', 1)
        return '''<div class="system-message">
        <p class="system-message-title">
        SystemMessage: %s (%s:%s)</p>
        <p>%s</p>
        <pre>%s</pre>
        </div>''' % (htmlEncode(level),
                     col, line,
                     htmlEncode(message),
                     htmlEncode(text))
    else:
        return '''<div class="system-message">
        <p class="system-message-title">
        <p class="system-message-title">%s</p>
        <pre>%s</pre>
        </div>''' % (htmlEncode(str(error)),
                     htmlEncode(tb))


class WikiLinkResolver(nodes.SparseNodeVisitor):

    def visit_reference(self, node):
        if node.resolved or not node.hasattr('refname'):
            return
        refname = node['refname']
        node.resolved = 1
        node['class'] = 'wiki'
        refuri = guessURLName(refname)
        node['refuri'] = refuri
        del node['refname']

class WikiLink(Transform):

    default_priority = 800

    def apply(self):
        visitor = WikiLinkResolver(self.document)
        self.document.walk(visitor)

class Reader(standalone.Reader):

    supported = standalone.Reader.supported + ('wiki',)

    def get_transforms(self):
        transforms = standalone.Reader.get_transforms(self)
        transforms.append(WikiLink)
        return transforms
