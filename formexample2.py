"""Demo for using FormEncode with Webware."""

# Tested with Webware 1.1 and FormEncode 1.2.3

from formencode import compound, Invalid, htmlfill, Schema, validators
from formencode.htmlfill_schemabuilder import parse_schema
from WebKit.Examples.ExamplePage import ExamplePage


form_template = '''<h2>Tell me about yourself</h2>

<form action="FormExample2" method="POST">

<p><label for="name">Your name:</label><br>
<form:error name="name">
<input type="text" id="name" name="name"
 form:validate="string" form:required="true"></p>

<p><label for="age">Your age:</label><br>
<form:error name="age">
<input type="text" id="age" name="age"
 form:validate="int"></p>

<p>Your favorite color:<br>
<form:error name="color">
<input type="checkbox" value="red" name="color"
 form:validate="string"> Red &nbsp;
<input type="checkbox" value="blue" name="color"> Blue &nbsp;
<input type="checkbox" value="black" name="color"> Black &nbsp;
<input type="checkbox" value="green" name="color"> Green</p>

<p><input type="submit" value="Submit"></p>
</form>'''


class FormExample2(ExamplePage):
    """Demo for using FormEncode with Webware."""

    schema = parse_schema(form_template)

    def getDefaults(self):
        return dict(age='enter your age', color=['blue'])

    def writeStyleSheet(self):
        ExamplePage.writeStyleSheet(self)
        self.writeln('''<style type="text/css">
.error {background-color: #fdd}
.error-message {color:#a00}
</style>''')

    def awake(self, trans):
        ExamplePage.awake(self, trans)
        if self.request().hasField('name'):
            fields = self.request().fields()
            try:
                fields = self.schema.to_python(fields, self)
            except Invalid, e:
                errors = dict((k, v.encode('utf-8'))
                    for k, v in e.unpack_errors().iteritems())
            else:
                errors = None
        else:
            fields = self.getDefaults()
            errors = None
        self.rendered_form = htmlfill.render(form_template,
            defaults=fields, errors=errors)

    def writeContent(self):
        self.write(self.rendered_form)
