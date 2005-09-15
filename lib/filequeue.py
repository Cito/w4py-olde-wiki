"""
Implements a simple queue, appending values to a file, and reading
them off the front of the file.  Multi-thread but not multi-process
safe.
"""

import threading
import os

__all__ = ['FileQueue']

class FileQueue(object):

    def __init__(self, filename):
        self.filename = filename
        self._lock = threading.Lock()

    def append(self, value):
        """
        Appends a value to the queue.
        """
        if not isinstance(value, str):
            raise ValueError(
                "Only strings may be added to a FileQueue, not %r"
                % value)
        self._lock.acquire()
        try:
            if '\n' in value:
                raise ValueError(
                    "Values cannot have newlines: %r" % value)
            f = open(self.filename, 'a')
            f.write(value + '\n')
            f.close()
        finally:
            self._lock.release()

    def extend(self, values):
        self._lock.acquire()
        try:
            f = open(self.filename, 'a')
            for value in values:
                assert '\n' not in value, (
                    "Values cannot have newlines: %r" % value)
                f.write(value + '\n')
            f.close()
        finally:
            self._lock.release()

    def set(self, value):
        """
        Like append, but only adds the value to the queue if it
        is not already in the queue.
        """
        self._lock.acquire()
        try:
            try:
                f = open(self.filename, 'r')
            except IOError:
                lines = []
            else:
                lines = f.readlines()
                f.close()
            if (value + '\n') in lines:
                return
            f = open(self.filename, 'a')
            f.write(value + '\n')
            f.close()
        finally:
            self._lock.release()
    
    def pop(self):
        """
        Pops the top value off the queue.  Returns None if nothing
        is left on the queue.
        """
        value = self.popmany(1)
        if value:
            return value[0]
        else:
            return None

    def popall(self):
        self._lock.acquire()
        try:
            try:
                f = open(self.filename, 'r')
            except IOError, e:
                if e.errno == 2: # no such file
                    return []
            all = f.readlines()
            f.close()
            f = open(self.filename, 'w')
            f.close()
            return [v[:-1] for v in all]
        finally:
            self._lock.release()

    def popmany(self, n):
        """
        Pops up to n entries at a time.
        """
        self._lock.acquire()
        try:
            try:
                size = os.stat(self.filename).st_size
            except OSError:
                return []
            if not size:
                return []
            f = open(self.filename, 'r')
            all = f.readlines()
            f.close()
            if not all:
                return []
            f = open(self.filename, 'w')
            f.write(''.join(all[n:]))
            f.close()
            return [v[:-1] for v in all[:n]]
        finally:
            self._lock.release()

