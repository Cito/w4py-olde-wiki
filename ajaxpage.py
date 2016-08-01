# AjaxPage.py
#
# Author: John Dickinson
# with help from nevow.org and Apple developer code
# see also ajax.js

import SitePage as ParentClass
import StringIO,traceback,time,random

RESPONSE_TIMEOUT = 100

# PyJavascript and quote_js based on ideas from nevow 0.4.1 (www.nevow.org)
def quote_js(what):
    if isinstance(what, bool):
        ret = str(what).lower()
    elif isinstance(what,(int,long,float,PyJavascript)):
        ret = str(what)
    else:
        ret = "'%s'" % str(what).replace('\\','\\\\').replace('\'','\\\'').replace('\n','\\n')
    return ret

class PyJavascript(object):
    def __init__(self, name):
        self.__name = name

    def __getattr__(self,aname):
        return self.__class__('%s.%s'%(self,aname))

    def __str__(self):
        return self.__name

    def __call__(self,*a,**kw):
        args = ','.join(quote_js(i) for i in a)
        kwargs = ','.join('%s=%s'%(k,quote_js(v)) for k,v in kw.items())
        if args and kwargs:
            allargs = '%s,%s'%(args,kwargs)
        elif not kwargs:
            allargs = args
        elif not args:
            allargs = kwargs
        return self.__class__('%s(%s)'%(self,allargs))

    def __getitem__(self,index):
        return self.__class__('%s[%s]'%(self,quote_js(index)))

    def __repr__(self):
        return self.__str__()

class AjaxPage(ParentClass):
    '''a super class to make coding XMLHttpRequest() applications easier'''

    # class-level variables to help make client code simpler
    document = PyJavascript('document')
    setTag = PyJavascript('ajax_setTag')
    setClass = PyJavascript('ajax_setClass')
    setValue = PyJavascript('ajax_setValue')
    setReadonly = PyJavascript('ajax_setReadonly')
    alert = PyJavascript('alert')
    generic_ajax = PyJavascript('generic_ajax')
    generic_ajax_form = PyJavascript('generic_ajax_form')
    this = PyJavascript('this')
    _responseBucket = {}

    def actions(self):
        return ParentClass.actions(self) + ['ajax_controller','ajax_response']

    def ajax_allowed(self):
        return []
        
    def ajax_clientPollingInterval(self):
        return random.choice(range(3,8)) # make it random to avoid syncronization
        
    def ajax_response(self):
        wait = self.ajax_clientPollingInterval()
        if wait is None:
            # turn off polling
            cmd = 'dying = true;' # tell the client that we are done polling
        else:
            who = self.session().identifier()
            # wait will be the timeout until the next time this function is called by the client
            cmd = 'wait = %s;' % wait # set wait variable here
            if self._responseBucket.get(who,[]):
                cmd += ';'.join(str(val) for req_number,val in self._responseBucket[who]) # add in other commands
                self._responseBucket[who] = []
        self.write(cmd) # write out al least the wait variable

    def ajax_controller(self):
        fields = self.request().fields()
        func = fields.get('f')
        args = fields.get('a',[])
        if type(args) != type([]):
            args = [args]
            
        req_number = args[-1]
        
        start_time = time.time()

        val = self.alert('There was some problem')
        if func in self.ajax_allowed():
            try:
                func_obj = getattr(self,func)
            except AttributeError:
                val = self.alert('%s, although an approved function, was not found' % func)
            else:
                try:
                    val = str(func_obj(*args[:-1])) # pull off sequence number added to "fix" IE
                except:
                    err = StringIO.StringIO()
                    traceback.print_exc(file=err)
                    e = err.getvalue()
                    val = self.alert('%s was called, but encountered an error: %s'%(func,e))
                    err.close()
        else:
            val = self.alert('%s is not an approved function' % func)
            
        if (time.time()-start_time) < RESPONSE_TIMEOUT:
            self.write(val)
        else:
            who = self.session().identifier()
            if not self._responseBucket.has_key(who):
                self._responseBucket[who] = [(req_number,val)]
            else:
                self._responseBucket[who].append((req_number,val))

    def ajax_cmdToClient(self,cmd):
        who = self.session().identifier()
        if not self._responseBucket.has_key(who):
            self._responseBucket[who] = []
        self._responseBucket[who].append((None,cmd))
    
    def preAction(self, action_name):
        if action_name.startswith('ajax_'):
            pass
        else:
            ParentClass.preAction(self,action_name)

    def postAction(self, action_name):
        if action_name.startswith('ajax_'):
            pass
        else:
            ParentClass.postAction(self,action_name)

    def writeJavaScript(self):
        ParentClass.writeJavaScript(self)
        self.writeln('<script type="text/javascript" src="javascripts/ajaxjavascript.js"></script>')
        if self.ajax_clientPollingInterval() is not None:
            self.writeln('<script type="text/javascript" src="javascripts/ajaxjavascriptpolling.js"></script>')
