import re
import uuid as UUID

tokenList = []
balanced = {}
def addTokensFromRegex(m):
        "For internal use. Passed into the regex.sub call in lex()"
        tokenList.append(Token(text=m.group(),range=m.span()))
        return ''

class Generator:
    """
        The instantiatable class to help with lexing source code into a token stream 
    """
    
    def __init__(self):
        self.patterns = []

    def add(self, name, regex):
        """
        adds a regex pattern to the lexer \n
        Be sure to add patterns in order of most specific. Example: r'\=' will match 
        for whatever reason underscores break the logic, so only uppercase characters A-Z allowed
        """
        self.patterns.append(Pattern(name, regex))

    

    def lex(self, source):
        "Generates an ordered tokenstream from the source code based on the given regex patterns"
        global tokenList
        ts = TokenStream()

        for p in self.patterns:
            re.sub(p.regex, addTokensFromRegex, source)
            for t in tokenList:
                t.name = p.name
            ts.tokens.extend(tokenList)
            tokenList = []
        ts.sort()

        self.matchBalanced(ts.tokens)

        return ts.tokens

    def balance(self, name):
        balanced[name] = {"depth":0, "pairs":{}}

    @staticmethod
    def matchBalanced(tokens):
        toBeBalanced = {}
        for t in tokens:
            name = t.name[1:]
            if name in balanced.keys():
                if t.name[0] == 'O':
                    balanced[name]["depth"] += 1
                    uuid = UUID.uuid4().hex
                    toBeBalanced[balanced[name]["depth"]] = uuid
                    t.metadata = uuid
                    balanced[name]["pairs"][uuid] = [t]
                    
                elif t.name[0] == 'C':
                    t.metadata = toBeBalanced[balanced[name]["depth"]]
                    balanced[name]["depth"] -= 1


class Pattern:
    "A glorified tuple containing only `name` and `regex`"
    def __init__(self, name, regex):
        self.name = name
        self.regex = regex


class Token:
    "Stores information about each token"
    def __init__(self, name='', text='', range='', subtokens = [], metadata = None):
        self.name = name
        self.range = range
        self.text = text
        self.subtokens = subtokens
        self.metadata = metadata
    def __lt__(self, other):
         return self.range[0] < other.range[0]
    def __str__(self):
        return '('+self.name+ ', ' + str(self.range) + ', `' + self.text + '`' + (', meta:' + self.metadata if self.metadata != None else '') +  (', sub:' + str(self.subtokens) if len(self.subtokens) != 0 else '') +')'
    def __repr__(self):
        return str(self)

class TokenStream:
    "Container for the list of tokens"
    def __init__(self):
        self.tokens = []
    def sort(self):
        self.tokens.sort()

