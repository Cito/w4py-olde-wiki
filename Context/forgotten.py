from LoginKit.forgotten import ForgottenPasswordComponent
from SitePage import *

class forgotten(SitePage):

    components = SitePage.components + [ForgottenPasswordComponent()]

    def defaultAction(self):
        self.forgottenPasswordForm()
        
