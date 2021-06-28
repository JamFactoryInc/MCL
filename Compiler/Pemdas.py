def eval(tokens):
    parenDepth = 0
    expression = []
    mode = 'INT'
    for t in tokens:
        if t.name == 'OPEN_PAREN':
            parenDepth += 1
        elif t.name == 'CLOSE_PAREN':
            parenDepth -= 1
        elif t.name == 'STR':
            mode = 'STR'
        elif 

        
def 