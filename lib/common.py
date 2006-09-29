"""
These are routines common to the entire application.
We keep them separate to avoid circular dependencies.
"""

import cgi
import re
import inspect
import pprint as pprint_module
pprint = pprint_module.pprint
import os

__all__ = ['canonicalName', 'htmlEncode', 'guessURLName', 'dprint',
           'pprint', 'guessTitle', 'dedent']

_canonicalNameRE = re.compile(r'[^a-z0-9]')
def canonicalName(name):
    """Turns a wiki name into its canonical form.

    This may only have letters, numbers and hyphens in it.
    """
    return str(_canonicalNameRE.sub('', name.lower()))

_urlNameRE = re.compile(r'[^a-z0-9 ]')
def guessURLName(name):
    name = str(_urlNameRE.sub('', name.lower()))
    return name.replace(' ', '-')

def guessTitle(name):
    """Turns a canonical name into a title."""
    return ' '.join([w.capitalize() for w in name.split('-')])

def htmlEncode(val, cgiEscape=cgi.escape):
    return cgiEscape(val, 1)

def dprint(*args, **kw):
    caller_frame = inspect.stack()[1]
    caller_name = caller_frame[3]
    caller_line = caller_frame[2]
    caller_filename = caller_frame[1]
    caller_module = os.path.splitext(os.path.basename(caller_filename))[0]
    del caller_frame
    print "%s from %s.%s:%s %s" % (
        '-'*10, caller_module, caller_name, caller_line, '-'*10)
    for arg in args:
        if isinstance(arg, (str, unicode)):
            print arg,
        else:
            print pprint_module.pformat(arg)
    items = kw.items()
    items.sort()
    for name, value in items:
        print name, pprint_module.pformat(value)

try:
    from textwrap import dedent
except ImportError: # Fallback for Python < 2.3
    def dedent(t):
        lines = text.expandtabs().split('\n')
        margin = None
        for line in lines:
            content = line.lstrip()
            if not content:
                continue
            indent = len(line) - len(content)
            if margin is None:
                margin = indent
            else:
                margin = min(margin, indent)
        if margin is not None and margin > 0:
            for i in range(len(lines)):
                lines[i] = lines[i][margin:]
        return '\n'.join(lines)
