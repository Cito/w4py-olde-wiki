"""
Parses HTML to find an 'abstract', i.e., a summary of the page.
"""

import re

tagRE = re.compile(r'<(/?[a-zA-Z0-9\-_]+)([^>]*)>')
classRE = re.compile(r'class="(.*?)"', re.I)

def find_abstract(html):
    """
    Search for something with the class 'abstract', or if nothing has
    such an attribute, a the first <p> or <div> tag we can find, or
    if there's not even that, the entire document.
    """
    fullHTML = html
    while 1:
        match = tagRE.search(html)
        if not match:
            return guess_abstract(fullHTML)
        html = html[match.end():]
        tag = match.group(1)
        attrs = match.group(2)
        classMatch = classRE.search(attrs)
        if not classMatch:
            continue
        classes = classMatch.group(1).lower().split()
        if 'abstract' in classes:
            return find_match_tag(html, tag.lower())

def find_match_tag(html, tagStart):
    """
    Give all the html that comes after, say, a <p> tag, find all
    the html up to the </p> tag, allowing for nested tags.
    """
    fullHTML = html
    tagNest = 0
    while 1:
        match = tagRE.search(html)
        if not match:
            return fullHTML
        tag = match.group(1).lower()
        if tag == tagStart:
            tagNest += 1
        elif tag == '/' + tagStart:
            if not tagNest:
                return fullHTML[:-(len(html)-match.start())]
            tagNest -= 1
        html = html[match.end():]
    
def guess_abstract(html):
    """
    Finds the first <p> tag, and we consider it to be the
    abstract.
    """
    fullHTML = html
    while 1:
        match = tagRE.search(html)
        if not match:
            return fullHTML
        html = html[match.end():]
        tag = match.group(1).lower()
        if tag == 'p':
            return find_match_tag(html, tag)
