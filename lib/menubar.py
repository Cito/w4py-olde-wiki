"""
Functions to generate HTML for the menubar.
"""

__all__ = ['Literal', 'Separator', 'menubarHTML']

class Literal:
    pass

class Separator:
    pass

class Namespace:

    def __init__(self, prefix):
        self.prefix = prefix
        self.id = 1

    def get(self):
        this, self.id = self.id, self.id+1
        return '%s_%i' % (self.prefix, this)

def menubarHTML(lst, namespace="menu"):
    """
    Converts a list into the HTML for use with the menubar.js
    code (see also http://www.brainjar.com/dhtml/menubar/)

    Each link is a tuple of (title, href).  Or, href can itself be a
    list of tuples.  So a nested list looks like::

        [('File', [('Open', '...'), ...])]

    If you want to include a non-menu element (particularly in the
    top-level bar) use a title of Literal (which is a symbol in this
    module).

    This returns a tuple of (menubar, subelements).  The menubar
    should be put wherever you want it to show up on the page, while
    the subelements should go directly after <body> or just before
    </body>.

    Pages that use this should also include ``menubar.js`` and the
    necessary CSS.
    """

    menubar = []
    subToRender = {}
    subelements = []
    ns = Namespace(namespace)

    menubar.append('<div class="menuBar">\n')
    
    for title, args in lst:
        if title is Literal:
            menubar.append(args)
        elif isinstance(args, list):
            name = ns.get()
            menubar.append(
                '<a class="menuButton" href="" '
                'onclick="return buttonClick(event, \'%s\')" '
                'onmouseover="buttonMouseover(event, \'%s\')">%s</a>\n'
                % (name, name, title))
            subToRender[(title, name)] = args
        else:
            menubar.append(
                '<a class="menuButton" href="%s" '
                'onmouseover="buttonMouseover(event, \'\')">%s</a>\n'
                % (args, title))

    menubar.append('</div>')

    while subToRender:
        (parentTitle, name), args = subToRender.popitem()
        subelements.append('<!-- %s menus: -->\n' % parentTitle)
        subelements.append(
            '<div id="%s" class="menu" onmouseover="menuMouseover(event)">\n'
            % name)
        for title, subargs in args:
            if title is Literal:
                subelements.append(subargs)
            elif title is Separator:
                subelements.append('<div class="menuItemSep"></div>\n')
            elif isinstance(subargs, list):
                name = ns.get()
                subelements.append(
                    '<a class="menuItem" href="" onclick="return false;" '
                    'onmouseover="menuItemMouseover(event, \'%s\');">'
                    '<span class="menuItemText">%s</span>'
                    '<span class="menuItemArrow">&#9454;</span></a>\n'
                    % (name, title))
                subToRender[(title, name)] = subargs
            else:
                subelements.append(
                    '<a class="menuItem" href="%s">%s</a>\n'
                    % (subargs, title))
        subelements.append('</div>\n')
        
    return ''.join(menubar), ''.join(subelements)

__test__ = {
    'simple': r"""
    >>> def t(v):
    ...     a, b = menubarHTML(v)
    ...     print a.strip(), '\n', b.strip()
    >>> t([('File', 'open.html')])
    <div class="menubar">
    <a class="menuButton" href="open.html" onmouseover="buttonMouseover(event, '')">
    </div>
    >>> t([('File', [('Open', 'open.html'), ('Close', 'close.html')])])
    <div class="menubar">
    <a class="menuButton" href="" onclick="return buttonClick(event, 'menu_1')" onmouseover="buttonMouseover(event, 'menu_1')">
    </div> <!-- File menus: -->
    <div id="menu_1" class="menu" onmouseover="menuMouseover(event)">
    <a class="menuItem" href="open.html">Open</a>
    <a class="menuItem" href="close.html">Close</a>
    </div>
    """,
    }

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
