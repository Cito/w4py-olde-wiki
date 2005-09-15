import os
import filequeue
import py

def runner(func):
    if os.path.exists('tmp.queue'):
        os.unlink('tmp.queue')
    q = filequeue.FileQueue('tmp.queue')
    func(q)
    os.unlink('tmp.queue')

def test_queue(q):
    assert q.pop() is None
    assert q.popall() == []
    assert q.popmany(10) == []
    q.append('1')
    assert q.pop() == '1'
    assert q.pop() is None
    q.append('2')
    assert q.popall() == ['2']
    q.extend(['1', '2', '3'])
    assert q.popmany(2) == ['1', '2']
    q.set('5')
    q.set('5')
    q.set('3')
    assert q.popall() == ['3', '5']
    py.test.raises(ValueError, q.append, 1)
    py.test.raises(ValueError, q.append, 'test\n')

test_queue = runner(test_queue)
