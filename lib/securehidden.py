import sha
import urllib
import os
import threading
import random
import time

class SignatureError(Exception):
    pass

class SecureSigner(object):

    """
    This will sign fields, and pack the value and signature into a
    single hidden field.  You may also make the field expirable.
    """

    def __init__(self, secretFilename):
        self.secretFilename = secretFilename
        self._secret = None
        self.secretLock = threading.Lock()

    def secret(self):
        if self._secret is not None:
            return self._secret
        self.secretLock.acquire()
        try:
            if self._secret is None:
                self._generateSecret()
        finally:
            self.secretLock.release()
        return self._secret

    def _generateSecret(self):
        if not os.path.exists(self.secretFilename):
            self._secret = ''
            for i in range(4):
                self._secret += hex(random.randrange(0xffff))[2:]
            f = open(self.secretFilename, 'w')
            f.write(self._secret)
            f.write('\n')
            f.close()
        else:
            f = open(self.secretFilename)
            self._secret = f.read().strip()
            f.close()

    def secureValue(self, value, timeout=None):
        """
        The value, signed and potentially with a timeout.  The timeout
        should be in seconds, e.g., 3600 for an hour.
        """
        pieces = []
        if timeout:
            expire = str(int(time.time()) + timeout)
        else:
            expire = '0'
        digest = sha.new()
        digest.update(value)
        digest.update(expire)
        digest.update(self.secret())
        pieces.append(expire)
        pieces.append(digest.hexdigest())
        pieces.append(value)
        return ' '.join(pieces)

    def parseSecure(self, input):
        """
        Take the value as produced by .secureValue(), unpack it, confirm
        the signature and expiration, and return the original value.  If
        something has happened -- the signature doesn't match, or it has
        expired -- a SignatureError will be raised.
        """
        expire, signature, value = input.split(' ', 2)
        digest = sha.new()
        digest.update(value)
        digest.update(expire)
        digest.update(self.secret())
        if not digest.hexdigest() == signature:
            raise SignatureError, "Bad signature: %r" % signature
        expire = int(expire)
        if expire and time.time() > expire:
            raise SignatureError(
                "Signature expired on %s (now is %s)"
                % (expire, time.time()))
        return value

