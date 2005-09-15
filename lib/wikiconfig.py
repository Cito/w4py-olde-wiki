from wsgikit.config.lazyloader import LazyLoader

__all__ = ['WikiConfig']

class NoDefault:
    pass

class WikiConfig(LazyLoader):
    
    def __init__(self, *args, **kw):
        self._merged_page_classes = {}
        LazyLoader.__init__(self, *args, **kw)

    def getbool(self, key, default=NoDefault):
        try:
            return self.convert(key, converter=self.convertbool)
        except KeyError:
            if default is NoDefault:
                raise
            return default

    def convertbool(self, value):
        value = value.strip().lower()
        if value in ('1', 'true', 'yes', 'on'):
            return True
        elif value in ('0', 'false', 'no', 'off'):
            return False
        else:
            raise ValueError(
                "Boolean expected (true/false)")

    def merge_page_class(self, page_class):
        try:
            return self._merged_page_classes[page_class] or self
        except KeyError:
            pass
        values = self.getlist('pageclass')
        to_add = []
        for value in values:
            if value.has_key(page_class):
                to_add.append(value[page_class])
        if to_add:
            new = self.clone()
            for item in to_add:
                new.merge(item)
            self._merged_page_classes[page_class] = new
            return new
        else:
            self._merged_page_classes[page_class] = None
            return self
                    
