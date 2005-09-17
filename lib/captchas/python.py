"""python - a Python captcha for Python programmers"""

__version__ = "1.0"
__license__ = "Python"
__copyright__ = "Copyright 2005 by Christoph Zwerschke"

from random import randint, choice

class Captcha:
    """A captcha for Python programmers.

    Methods:
    create(width): create the HTML form fields
        width: the length of the input field
    check(input, id): check the input from the user
        input, id: use the result values from the form
    """

    alphabet = 'pythonic'

    def create(self, width=6, id=None):
        if not id:
            code = randint(1, 7)
            word = []
            for i  in range(width):
                word.append(choice(self.alphabet))
            word = ''.join(word)
            id = word + str(code)
        expr = self.__expr(id)
        s = ['<p>Have a look'
            ' at the following expression:</p>']
        s.append('<pre class="py">%s</pre>' % expr)
        s.append('<p>Now please enter the result: ')
        s.append('<input name="captcha_input" type="text"'
            ' size="%d" maxlength="%d"></p>' % ((width,)*2))
        s.append('<input name="captcha_id" type="hidden"'
            ' value="%s">' % id)
        return '\n'.join(s)

    def check(self, input, id):
        expr = self.__expr(id)
        input = input.strip().strip('\'"')
        try:
            solution = eval(expr)
        except:
            solution = None
        return input == solution

    def __expr(self, id):
        if not isinstance(id, str):
            return None
        code = id[-1:]
        try:
            code = int(code)
        except:
            code = 0
        if not 1 <= code <= 8:
            return None
        word = id[:-1]
        for c in word:
            if c not in self.alphabet:
                return None
        return ("''.join(map(lambda c:"
            "'%s'[\n'%s'.index(c)^%d],'%s'))"
            % (self.alphabet, self.alphabet, code, word))
