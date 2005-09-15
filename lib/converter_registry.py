_registry = {}

def register(func, mime_type):
    assert mime_type not in _registry, (
        "Registry duplicate for mime type %s"
        % mime_type)
    _registry[mime_type] = func

def convert(page, text, mime_type):
    possible = [mime_type, mime_type.split('/')[0] + '/*', '*']
    for mtype in possible:
        if mtype in _registry:
            return _registry[mtype](page, text, mime_type)
    raise ValueError, (
        "No converter registered for type %s"
        % mime_type)
