import os

__all__ = ['upload_files']

def upload_files(hostname, fileList, port=None, username=None,
                 password=None):
    assert not password, "SSH does not support passwords at this time"
    if ':' in hostname:
        hostname, port = hostname.split(':', 1)
        port = int(port)
    if username == os.environ['USER']:
        username = None
    allDirs = {}
    for source, dest in fileList:
        allDirs[os.path.dirname(dest).replace('"', '').replace("'", '')] = 1
    allDirs = allDirs.keys()
    if allDirs:
        cmd = 'ssh'
        cmd += ' ' + hostname
        if port and port != 22:
            cmd += ' -p %i' % port
        if username:
            cmd += ' -l %s' % username
        cmd += ' '
        cmd += '"mkdir -p %s"' % ' '.join(["'%s'" % d for d in allDirs])
        stdin, stdouterr = os.popen4(cmd)
        output = stdouterr.read()
        if output:
            print 'SSH output (%r): %s' % (cmd, output)

    cmd = 'sftp'
    cmd += ' -b -'
    if username:
        cmd += ' %s@%s' % (username, hostname)
    else:
        cmd += ' ' + hostname
    stdin, stdout, stderr = os.popen3(cmd)
    for source, dest in fileList:
        stdin.write('put %s %s\n' % (source, dest))
    stdin.close()
    output = stderr.read()
    output += stdout.read()
    if output:
        print 'SFTP output (%r): %s' % (cmd, output)

if __name__ == '__main__':
    import sys
    upload_files(sys.argv[1], [p.split(':', 1) for p in sys.argv[2:]])
    
