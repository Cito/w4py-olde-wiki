from LoginKit.simpleuser import SimpleUser


class WikiUser(SimpleUser):

    def __init__(self, manager):
        SimpleUser.__init__(self, manager)
        self._name = None
        self._email = None
        self._website = None
        self._roles = []
        self._url = None

    def email(self):
        return self._email

    def setEmail(self, value):
        self._email = value
        self.changed()

    def website(self):
        return self._website

    def setWebsite(self, value):
        self._website = value
        self.changed()

    def roles(self):
        return self._roles

    def setRoles(self, roles):
        self._roles = roles
        self.changed()

    def url(self):
        return self._url or None

    def setURL(self, value):
        self._url = url
        self.changed()

    def signature(self):
        if self.url():
            return '<a href="%s">%s</a>' % (self.url(), self.name())
        else:
            return self.name()

    def simpleFields(self):
        fields = SimpleUser.simpleFields(self)
        fields['roles'] = ', '.join(self.roles())
        fields['url'] = self.url()
        return fields

    def setSimpleFields(self, fields):
        SimpleUser.setSimpleFields(self, fields)
        self._roles = [
            r.strip() for r in fields.get('roles', '').split(',')
            if r.strip()]
        self._url = fields.get('url', '')
    
