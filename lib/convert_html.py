from common import htmlEncode
#import py2html, PyFontify
import PySourceColor
import converter_registry

def convert_html(page, text, mime_type):
    return text

converter_registry.register(convert_html, 'text/html')

def convert_text(page, text, mime_type):
    return '''
    <div align=right><a href="%s">source</a></div>
    <pre>%s</pre>''' % (page.sourceLinkForMimeType(mime_type),
                        htmlEncode(text))

converter_registry.register(convert_text, 'text/*')

def convert_application(page, text, mime_type):
    return '''
    <a href="%s">View file (%s)</a>
    ''' % (page.sourceLinkForMimeType(mime_type), mime_type)

converter_registry.register(convert_application, 'application/*')

def convert_image(page, text, mime_type):
    attrs = ''
    if page.width:
        attrs += ' width="%i"' % page.width
    if page.height:
        attrs += ' height="%i"' % page.height
    return '<img src="%s"%s>' % (
        page.sourceLinkForMimeType(mime_type),
        attrs)

converter_registry.register(convert_image, 'image/*')

def convert_generic(page, text, mime_type):
    return text

converter_registry.register(convert_generic, '*')

def convert_python(page, text, mime_type):
    
    #pp = py2html.PrettyPrint(format='rawhtml', mode='color',
    #                         tagfct=PyFontify.fontify)
    #html = pp.filter(text)
    html = PySourceColor.str2html(text, PySourceColor.dark)
    return '''
    <div class="source-code">
    <a href="%s" class="source-link button">source</a>
    %s</div>''' % (page.sourceLinkForMimeType(mime_type), html)

converter_registry.register(convert_python, 'text/x-python')
