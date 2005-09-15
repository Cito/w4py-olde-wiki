"""
Pooled Cheetah templates
"""

from Cheetah.Template import Template as CheetahTemplate

class Template(object):

    _keywords = ['cacheSize', 'searchList']
    cacheSize = 10
    searchList = []

    def __init__(self, *args, **kw):
        for name in self._keywords:
            if kw.has_key(name):
                setattr(self, name, kw[name])
                del kw[name]
        self.args = args
        self.kw = kw
        self.pool = []

    def eval(self, **namespace):
        tmpl = None
        try:
            tmpl, tmplNamespace = self.getTemplate()
            tmplNamespace.clear()
            tmplNamespace.update(namespace)
            result = str(tmpl)
        finally:
            if tmpl:
                self.returnTemplate(tmpl, tmplNamespace)
        return result

    def getTemplate(self):
        try:
            return self.pool.pop()
        except IndexError:
            return self.newTemplate()

    def newTemplate(self):
        namespace = {}
        kw = self.kw.copy()
        kw['searchList'] = self.searchList + [namespace]
        tmpl = CheetahTemplate(*self.args, **kw)
        return tmpl, namespace

    def returnTemplate(self, tmpl, namespace):
        if len(self.pool) >= self.cacheSize:
            # Throw it away
            return
        self.pool.append((tmpl, namespace))
