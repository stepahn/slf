from simplelexer import lex


def test_single_quoted_string():
    for s in ["""'abc'""",
              """'ab"c'""",
              """'ab\\'c'""",
              ]:
        tokens = lex(s)
        token, newline, eof = tokens
        assert token.name == 'String'
        assert newline.name == 'Newline'
        assert eof.name == 'EOF'

def test_number():
    for s in ["0",
              "+1",
              "-1",
              "-1123123",
              ]:
        tokens = lex(s)
        token, newline, eof = tokens
        assert token.name == 'Number'
        assert newline.name == 'Newline'
        assert eof.name == 'EOF'

def test_name():
    for s in ["abc",
              "_",
              "a_0",
              "_0",
              ]:
        tokens = lex(s)
        token, newline, eof = tokens
        assert token.name == 'Name'
        assert newline.name == 'Newline'
        assert eof.name == 'EOF'
        s = '$' + s
        tokens = lex(s)
        token, newline, eof = tokens
        assert token.name == 'PrimitiveName'
        assert newline.name == 'Newline'
        assert eof.name == 'EOF'

def test_long():
    for s, numtoken in [
            ("if x:\n    print x", 10),
            ("if x:#foo\n    x abc = 17", 12),
            ("1 a \\\n 2", 5)]:
        tokens = lex(s)
        assert len(tokens) == numtoken
        print tokens

def test_indentation():
    s = """a
b
    c
        d
      
  #some comment
    e
        f
    """
    tokens = lex(s)
    assert [t.name for t in tokens] == ["Name", "Newline", "Name", "Newline",
                                        "Indent", "Name", "Newline", "Indent",
                                        "Name", "Newline", "Dedent", "Name",
                                        "Newline", "Indent", "Name", "Newline",
                                        "Dedent", "Dedent", "EOF"]

def test_linecont():
    s = "a a \\\n     b"
    tokens = lex(s)
    assert [t.name for t in tokens] == ["Name", "Name", "Name", "Newline",
                                        "EOF"]

def test_parenthesis():
    s = "(a = \n     b)"
    tokens = lex(s)
    assert [t.name for t in tokens] == ["OpenBracket", "Name", "Special", "Name",
                                        "CloseBracket", "Newline", "EOF"]

def test_comment():
    s = "(a = # foo this is a comment \n     b)"
    tokens = lex(s)
    assert [t.name for t in tokens] == ["OpenBracket", "Name", "Special", "Name",
                                        "CloseBracket", "Newline", "EOF"]

