"""music - a Python captcha for musicians"""

__version__ = "1.0"
__license__ = "Python"
__copyright__ = "Copyright 2005 by Christoph Zwerschke"

from random import randint

class Captcha:
    """A captcha for Python programmers.

    Methods:
    create(width): create the HTML form fields
        width: the length of the input field
    check(input, id): check the input from the user
        input, id: use the result values from the form
    """

    size = (6,4)
    colors = ['black', 'white']
    names = 'do-re-mi-fa-so-la-ti-do-re'.split('-')

    def create(self, width=6, id=None):
        if id:
            notes = map(int, id)
        else:
            notes = []
            for i  in range(width):
                notes.append(randint(0, 8))
            id = ''.join(map(str, notes))
        s = ['<table cellpadding="2" cellspacing="0">'
            '<tr><td colspan="3">']
        s.append('Please enter the melody'
            ' in solfege notation:')
        s.append('</td></tr><tr><td colspan="2"></td><td>')
        s.append('(e.g., "doremiresola")')
        s.append('</td></tr><tr>'
            '<td style="vertical-align:top"'
            ' width="%d" height="%d">'
            % ((width*2+1)*self.size[0], 12*self.size[1]))
        s.append(self.__notes(notes))
        s.append('<br></td><td style="vertical-align:middle">&nbsp;'
            ' = &nbsp;</td><td style="vertical-align:middle">')
        s.append('<input name="captcha_input" type="text"'
            ' size="%d" maxlength="%d">' % ((width*3,)*2))
        s.append('<input name="captcha_id" type="hidden"'
            ' value="%s">' % id)
        s.append('</td></tr></table>')
        return '\n'.join(s)

    def check(self, input, id):
        input = input.lower()
        input = filter(lambda c: c.isalpha(), input)
        solution = self.__solfege(id)
        return input == solution

    def __solfege(self, id):
        if not isinstance(id, str):
            return None
        solfege = []
        for n in id:
            try:
                n = int(n)
            except:
                n = -1
            if not 0 <= n <= 8:
                return None
            solfege.append(self.names[n])
        return ''.join(solfege)

    def __notes(self, notes):
        s = ['<div style="position:relative">']
        for row in range(10):
            col = 0
            for note in notes:
                s.append(self.__note(col, row))
                col += 1
                s.append(self.__note(col, row, row+note-8 in (0,1)))
                col += 1
            s.append(self.__note(col, row))
        # Workaround for MSIE-Bug:
        s.append('<span style="position:absolute;'
            'width:%dpx;top:%dpx;height:0px;'
            'background-color:%s"></span>'
            % ((len(notes)*2+1)*self.size[0],
                10*self.size[1], self.colors[1]))
        s.append('</div>')
        return '\n'.join(s)

    def __note(self, col, row, filled=False):
        s = ['position:absolute',
            'left:%dpx' % (self.size[0]*col),
            'top:%dpx' % (self.size[1]*row),
            'width:%dpx' % self.size[0],
            'height:%dpx' % self.size[1],
            'border-width:1px 0px',
            #'border-color:blue',
            'border-top-color:%s' % self.colors[
                not(row % 2 or filled)],
            'border-bottom-color:%s' % self.colors[
                not(row % 2 or filled) or row==9],
            'border-style:solid',
            'background-color:%s' % self.colors[not filled]]
        s = ';'.join(s)
        s = '<span style="%s"></span>' % s
        return s
