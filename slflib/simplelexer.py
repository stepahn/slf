from pypy.rlib.parsing.lexer import Lexer, Token, SourcePos
import re

class LexerError(Exception):
    def __init__(self, input, source_pos, msg=""):
        self.input = input
        self.source_pos = source_pos
        self.msg = msg
        self.args = (input, source_pos)

    def nice_error_message(self, filename="<unknown>"):
        result = ["  File %s, line %s" % (filename, self.source_pos.lineno+1)]
        result.append(self.input.split("\n")[self.source_pos.lineno])
        result.append(" " * self.source_pos.columnno + "^")
        result.append("LexerError: %s" % (self.msg, ))
        return "\n".join(result)

    def __str__(self):
        return self.nice_error_message()

# attempts at writing a simple Python-like lexer

def group(*choices, **namegroup):
    choices = list(choices)
    for name, value in namegroup.iteritems():
        choices.append("(?P<%s>%s)" % (name, value))
        re.compile(value)
    return '(' + '|'.join(choices) + ')'
def any(*choices):
    result = group(*choices) + '*'
    return result
def maybe(*choices):
    return group(*choices) + '?'

Number = r'(([+-])?[1-9][0-9]*)|0'

# ' or " string.
def make_single_string(delim):
    normal_chars = r"[^\n\%s]*" % (delim, )
    return "".join([delim, normal_chars,
                    any(r"\\" + delim + normal_chars), delim])

String = group(make_single_string(r"\'"),
                     make_single_string(r'\"'))


#____________________________________________________________
# Ignored

Whitespace = r'[ \f\t]'
Newline = r'\r?\n'
Linecontinue = r'\\' + Newline
Comment = r'#[^\r\n]*'
Indent = Newline + any(Whitespace)
Ignore = group(Whitespace + '+', Linecontinue, Comment)

#____________________________________________________________

Name = r'[a-zA-Z_][a-zA-Z0-9_]*'
PrimitiveName = '\\$' + Name

Special = r'[\:\=\,]'

OpenBracket = r'[\[\(\{]'
CloseBracket = r'[\]\)\}]'

tokens = ["Number", "String", "Name", "Ignore", "Indent", 
          "OpenBracket", "CloseBracket", "Special", "PrimitiveName"]

def make_lexer():
    from pypy.rlib.parsing.regexparse import parse_regex
    return Lexer([parse_regex(globals()[r]) for r in tokens], tokens[:])
    
simplelexer = make_lexer()

tabsize = 4

def postprocess(tokens, source):
    parenthesis_level = 0
    indentation_levels = [0]
    output_tokens = []
    tokens = [token for token in tokens if token.name != "Ignore"]
    token = None
    for i in range(len(tokens)):
        token = tokens[i]
        if token.name == "OpenBracket":
            parenthesis_level += 1
            output_tokens.append(token)
        elif token.name == "CloseBracket":
            parenthesis_level -= 1
            if parenthesis_level < 0:
                raise LexerError(source, token.source_pos, "unmatched parenthesis")
            output_tokens.append(token)
        elif token.name == "Indent":
            if i+1 < len(tokens) and tokens[i+1].name == "Indent":
                continue
            if parenthesis_level == 0:
                s = token.source
                length = len(s)
                pos = 0
                column = 0
                # the token looks like this: \r?\n[ \f\t]*
                if s[0] == '\n':
                    pos = 1
                    start = 1
                else:
                    pos = 2
                    start = 2
                while pos < length:  # count the indentation depth of the whitespace
                    c = s[pos]
                    if c == ' ':
                        column = column + 1
                    elif c == '\t':
                        column = (column // tabsize + 1) * tabsize
                    elif c == '\f':
                        column = 0
                    pos = pos + 1
                # split the token in two: one for the newline and one for the 
                # in/dedent
                output_tokens.append(Token("Newline", s[:start], token.source_pos))
                if column > indentation_levels[-1]: # count indents or dedents
                    indentation_levels.append(column)
                    token.name = "Indent"
                    token.source = s[start:]
                    token.source_pos.i += start
                    token.source_pos.lineno += 1
                    token.source_pos.columnno = 0
                    output_tokens.append(token)
                else:
                    dedented = False
                    while column < indentation_levels[-1]:
                        dedented = True
                        indentation_levels.pop()
                        output_tokens.append(Token("Dedent", "",
                                                   token.source_pos)) 
                    if dedented:
                        token.name = "Dedent"
                        token.source = s[start:]
                        token.source_pos.i += start
                        token.source_pos.lineno += 1
                        token.source_pos.columnno = 0
                        output_tokens[-1] = token
            else:
                pass # implicit line-continuations within parenthesis
        else:
            output_tokens.append(token)
    if token is not None:
        output_tokens.append(Token("EOF", "", token.source_pos))
    return output_tokens

def lex(s):
    if not s.endswith('\n'):
        s += '\n'
    return postprocess(simplelexer.tokenize(s), s)
