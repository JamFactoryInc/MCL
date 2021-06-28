import Lexer
import TokenSequence as ts

tokens = Lexer.tokenize(
"""
;
(1+(2+4+(6*3)))
method(1234)
1 + (4*x+3)
Int x = 4;
"""
)

print(tokens)


ts.add('EXPRESSION', r'WORD^!,OPAREN=1^,ALL*,CPAREN=1^')
ts.add('METHOD', r'WORD,OPAREN=1^,ALL*^,CPAREN=1^')
ts.add('DECLARE', r'WORD,WORD,SET,INT,END')

matches = ts.search(tokens)

for m in matches:
    print(m)

# ts.search()