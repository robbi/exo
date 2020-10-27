import re
import math
import readline
from collections import namedtuple

PROMPT = '#> '
Token = namedtuple('Token', ['kind', 'value', 'pos'])

class ParseError(Exception):
    def __init__(self, message, position):
        self.msg = message
        self.pos = position

    def __str__(self):
        return f'{" " * (len(PROMPT)+self.pos)}^\nErreur: {self.msg}'


class ParseSyntaxError(ParseError):
    TRAD = {
        'EXPR': 'expression attendue',
        'NEG_EXPR': 'expression attendue',
        'OPERATION': 'opération attendue',
        'OPERAND': 'opérande attendue',
        'NEG_OPERAND': 'chiffre attendu',
    }

    def __init__(self, value, expected, position):
        super().__init__(
            f'{ParseSyntaxError.TRAD[expected]}, "{value}" trouvé', position)


def tokenize(input_str):
    keywords = {}
    constant = {'PI': math.pi}
    token_specification = [
        ('NUMBER', r'\d+(?:,\d*)?'),  # Entier ou décimal
        ('OP', r'[+\-*/]'),  # Opérateur arithmétique
        ('POPEN', r'\('),  # Parenthèse ouvrante
        ('PCLOSE', r'\)'),  # Parenthèse fermante
        ('ID', r'[A-Za-z]+'),  # Identifiant
        ('SKIP', r'\s+'),  # Passe les espaces
        ('MISMATCH', r'.'),  # Tout autre caractère
    ]
    tok_regex = '|'.join(
        f'(?P<{name}>{regex})' for (name, regex) in token_specification)
    for mo in re.finditer(tok_regex, input_str):
        kind = mo.lastgroup
        value = mo.group()
        pos = mo.start()

        if kind == 'NUMBER':
            if ',' in value:
                value = float(value.replace(',', '.'))
            else:
                value = int(value)
        elif kind == 'ID' and value.upper() in keywords:
            kind = value.upper()
        elif kind == 'ID' and value.upper() in constant:
            name = value.upper()
            kind = 'NUMBER'
            value = constant[name]
        elif kind == 'SKIP':
            continue
        yield Token(kind, value, pos)
    yield Token('EOF', '', len(input_str))


def reduce_rpn(stack):
    values = []
    for token in stack:
        (kind, value, _) = token
        if kind == 'NUMBER':
            values.append(value)
        elif kind == 'OP':
            if value == '+':
                result = values.pop() + values.pop()
            elif value == '-':
                result = -values.pop() + values.pop()
            elif value == '*':
                result = values.pop() * values.pop()
            elif value == '/':
                denominator = values.pop()
                result = values.pop() / denominator
            elif value == 'NEG':
                result = -values.pop()
            else:
                raise NotImplementedError()
            values.append(result)
        elif kind == 'NOP':
            pass
        else:
            raise NotImplementedError()
    return values.pop()


def parse(tokens):
    stack = []
    subexpr = []
    expect = 'EXPR'

    for token in tokens:
        (kind, value, pos) = token

        if kind == 'MISMATCH':
            raise ParseError(f'Erreur : entrée inconnue {value}', pos)

        elif kind == 'NUMBER':
            if expect == 'EXPR':
                stack.append(token)
                expect = 'OPERATION'
            elif expect == 'NEG_EXPR':
                (_, _, pos) = stack.pop()
                stack.append(Token(kind, -value, pos))
                expect = 'OPERATION'
            elif expect in ['OPERAND', 'NEG_OPERAND']:
                if expect == 'NEG_OPERAND':
                    (_, _, pos) = stack.pop()
                    token = Token(kind, -value, pos)
                stack.append(token)
                if len(stack) >= 2 and stack[-2].kind == 'OP':
                    stack[-1], stack[-2] = stack[-2], stack[-1]
                    if (len(stack) >= 3
                            and stack[-1].value in ('*', '/')
                            and stack[-2].kind == 'NUMBER'
                            and stack[-3].kind == 'OP'
                            and stack[-3].value in ('+', '-')):
                        # '*','/' before '+','-'
                        stack[-3:] = stack[-2], stack[-1], stack[-3]
                expect = 'OPERATION'
            else:
                raise ParseSyntaxError(value, expect, pos)

        elif kind == 'OP':
            if expect == 'EXPR' or expect == 'OPERAND':
                if value == '-':
                    stack.append(token)
                    expect = f'NEG_{expect}'
                else:
                    raise ParseSyntaxError(value, expect, pos)
            elif expect == 'OPERATION':
                stack.append(token)
                expect = 'OPERAND'
            else:
                raise ParseSyntaxError(value, expect, pos)

        elif kind == 'POPEN':
            if expect in ['EXPR', 'OPERAND']:
                pass
            elif expect == 'NEG_EXPR':
                (_, _, op_pos) = stack.pop()
                stack.append(('OP', 'NEG', op_pos))
            else:
                raise ParseSyntaxError(value, expect, pos)
            subexpr.append((stack, expect))
            stack, expect = [], 'EXPR'

        elif kind == 'PCLOSE':
            if len(subexpr) == 0 or expect != 'OPERATION':
                raise ParseSyntaxError(value, expect, pos)
            stack.append(Token('NOP', 0, pos))
            stack_token = stack
            stack, expect = subexpr.pop()
            if expect == 'EXPR':
                stack.extend(stack_token)
                expect = 'OPERATION'
            elif expect == 'NEG_EXPR':
                last_op = stack.pop()
                stack.extend(stack_token)
                stack.append(last_op)
                expect = 'OPERATION'
            elif expect == 'OPERAND':
                prev_op = None
                last_op = stack.pop()
                if (last_op.value in ('*', '/')
                        and len(stack) >= 1
                        and stack[-1].kind == 'OP'
                        and stack[-1].value in ('+', '-')):
                    # '*','/' before '+','-'
                    prev_op = stack.pop()
                stack.extend(stack_token)
                stack.append(last_op)
                if prev_op is not None:
                    stack.append(prev_op)
                expect = 'OPERATION'
            else:
                raise ParseSyntaxError(value, expect, pos)

        elif kind == 'EOF':
            if expect != 'OPERATION':
                raise ParseSyntaxError('FIN', expect, pos)
            if len(subexpr) > 0:
                raise ParseError('")" manquante', len(input_str))

        else:
            raise ParseSyntaxError(value, expect, pos)

    return stack


def calc(input_str):
    tokens = tokenize(input_str)
    tree = parse(tokens)
    result = reduce_rpn(tree)
    return result


if __name__ == "__main__":
    while True:
        try:
            input_str = input(PROMPT)
            result = calc(input_str)
            print(f" {result}")
        except EOFError:
            print("")
            break
        except ParseError as e:
            print(e)
        except ZeroDivisionError:
            print("Erreur : division par zero")
