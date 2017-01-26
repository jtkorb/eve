def test_one(a, b):
    '''

    >>> test_one(3, 5)
    8
    '''
    return a + b

def test_two(a, b):
    '''
    >>> test_two(4, 6)
    9
    '''
    return 0

def doit():
    mail.send(to=['jtkorb@bikmort.com'],
              subject='another message',
              message='hi there.  looking for a good from line')
