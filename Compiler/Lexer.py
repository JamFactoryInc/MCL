# from rply import LexerGenerator as lg
from LexGen import Generator

def tokenize(source):

    tokens = []

    genericTokens = {
        r'\v': ['INT','FLOAT','CMD','WORD,OPEN_PAREN,(WORD,SET?,DELIM)*,WORD,CLOSE_PAREN'],''
        r'\o':['MUL','DIV','SUB','MOD','SUM'],
        r'\d':['FLOAT','INT']
        }

    lexgen = Generator()

    lexgen.add('CMD', r'`.*?`')

    lexgen.add('STR', r'(?:(["\'])(?:(?<!\\)\\(?:\\\\)*\1|(?!\1).)*?\1+)')

    lexgen.add('COMMENT', r'\/\/.*')

    lexgen.add('DELIM', r'\,')

    lexgen.add('FLOAT', r'\d+\.\d*')

    lexgen.add('INT', r'\d+')

    lexgen.add('DOT', r'\.')

    lexgen.add('TO', r'\:')

    lexgen.add('SUM', r'\+')

    lexgen.add('SUB', r'\-')

    lexgen.add('MUL', r'\*')

    lexgen.add('DIV', r'\/')

    lexgen.add('MOD', r'\%')

    lexgen.add('IADD', r'\=\+')

    lexgen.add('ISUB', r'\=\-')

    lexgen.add('IMUL', r'\=\*')

    lexgen.add('IDIV', r'\=\/')

    lexgen.add('IMOD', r'\=\%')

    lexgen.add('INC', r'\+\+')

    lexgen.add('DEC', r'\-\-')

    lexgen.add('END', r'\;')

    lexgen.add('LTEQ', r'\<\=')

    lexgen.add('GTEQ', r'\>\=')

    lexgen.add('XOR', r'\<\>')

    lexgen.add('LT', r'\<')

    lexgen.add('GT', r'\>')

    lexgen.add('EQUAL', r'\=\=')

    lexgen.add('NOTEQUAL', r'\!\=')

    lexgen.add('AND', r'\&\&')

    lexgen.add('OR', r'\|\|')

    lexgen.add('SET', r'\=')

    lexgen.add('OPAREN', r'\(')

    lexgen.add('CPAREN', r'\)')

    lexgen.add('OBRACE', r'\{')

    lexgen.add('CBRACE', r'\}')

    lexgen.add('OBRACKET', r'\[')

    lexgen.add('CBRACKET', r'\]')

    lexgen.add('WORD', r'[A-z_]\w*')





    lexgen.balance('PAREN')

    lexgen.balance('BRACKET')

    lexgen.balance('BRACE')

    

    #lexgen.ignore(r'\s+')

    #builtlex = lexgen.build()

    # pad the source with new lines to fix some regex fuckery as well as some bugs if there's an error on the last line
    source = '\n' + source + '\n'

    # try:
    tokens = lexgen.lex(source)
        # for token in tokens:
        #     print(token)
    return tokens
    # except Exception as e:
    #     print('Unregistered character or expression: ' + source[e.source_pos.idx] + ' at line ' +  str(e.source_pos.lineno) + ' column ' + str(e.source_pos.colno))
    #     print('If this is unexpected behaviour, please submit a bug report to the MCL discord with the following contents:')
    #     print('Lexing error trying to read: "' + source[source.rindex('\n',0,e.source_pos.idx)+1:source.index('\n',e.source_pos.idx)] + '"  Encountered unregistered expression: ' + source[e.source_pos.idx])

    



