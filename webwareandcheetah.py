from WebKit.Page import Page
from Cheetah.Template import Template
import threading

debug = True

class SafeCheetah(Page):
    
    def __init__(self):
        Page.__init__(self)
        self.__safe = threading.local()
        self.tmpl_file = 'MyTemplate.tmpl'
        
    def awake(self, trans):
        Page.awake(self, trans)
        current_thread = threading.currentThread()
        try:
            # If you compiled cheetah file, you can import pure Python code here
            import MyTemplate
            self.__safe.tmpl = MyTemplate()
        except ImportError:
            # otherwise you have to parse the template file
            print "I have to parse template %s" % self.tmpl_file
            try:
                self.__safe.tmpl
                if debug:
                    print "The thread %s is already filled, cool!\n" % current_thread 
            except AttributeError:
                if debug:
                    print "I have to parse template for thread %s\n" % current_thread
                self.__safe.tmpl = Template(file='default/'+self.tmpl_file)
        # I can fill my template with some values
        self.__safe.tmpl.title = "Logo"
        self.__safe.tmpl.image = "ruby.jpg"

        
    def writeHTML(self):
        self.write(self.__safe.tmpl.respond())

# Contents of MyTemplate.tmpl: $title<br /><img src="/images/$image" alt="" />
