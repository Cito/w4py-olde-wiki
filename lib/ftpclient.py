"""
A simple FTP client; See also sshclient
"""

import ftplib
import os

__all__ = ['upload_files']

def upload_files(hostname, fileList, username=None,
                 password=''):
    if username is None:
        username = os.environ['USER']
    ftp = ftplib.FTP(hostname, username, password)
    for source, dest in fileList:
        f = open(source)
        dir = os.path.dirname(dest)
        while 1:
            try:
                ftp.storbinary('STOR %s' % dest, f)
            except ftplib.error_perm:
                pass
            else:
                break
            ftp_makedirs(ftp, dir)
        f.close()
    ftp.close()

def ftp_makedirs(ftp, dir):
    """
    Makes the directories for dir, creating any directories as
    necessary.
    """
    tryDir = dir
    while 1:
        try:
            ftp.mkd(tryDir)
        except ftplib.error_perm:
            tryDir = os.path.dirname(tryDir)
        else:
            if tryDir == dir:
                return
            tryDir = dir

if __name__ == '__main__':
    import sys
    upload_files(sys.argv[1], [p.split(':', 1) for p in sys.argv[3:]],
                password=sys.argv[2])
