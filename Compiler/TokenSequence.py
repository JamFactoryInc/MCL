import LexGen

# basic regex-like pattern matching

# holds the patterns added by the `add()` method.
patterns = []

def add(name, regex, returnPattern = False):
    """
    parses the metaregex pattern `regex` into a `Pattern` to be easily used by `searchPattern()`
    """

    # pads the regex string to fix a bug
    regex = regex + ' '


    pattern = Pattern()
    tokenName = ''

    # patternRule is the variable to hold the Pattern.Rule that is currently being parsed
    patternRule = None

    # keeps track of how many parenthesis-pairs deep the parser is
    parenDepth = 0

    # if this method was called by itself to parse a subpatter, this is the variable that holds it
    subRegex = ''

    # iterate through each character in the metaregex pattern
    for i, _ in enumerate(regex):
        c = regex[i]
        # if the current character is an opening parenthesis then add 1 to the paren depth and continue
        if c == '(':
            parenDepth += 1
            continue

        # if c is inside the outermost layer of parentheses
        if parenDepth > 0:

            # if the current character is a closing parenthesis then subtract 1 from the paren depth 
            if c == ')':
                parenDepth -= 1

            # if, after potentially subtracting 1, the depth is now 0, then we are no longer within the outermost parentheses
            # then assign `patternRule` to a new tokenRule. tokenRule's subpattern field is set to the returned value from calling this same function with the contents of the subpattern
            if parenDepth == 0:
                print('SUB REGEX: ' + subRegex)
                patternRule = Pattern.TokenRule('SUBPATTERN', subPattern=add(subRegex, returnPattern=True))
                subRegex = ''
                continue

            # the subpattern's content has the current character added to it. This is eventually passed into this same function
            subRegex += c
            
        # if c is not in parentheses
        else:
            # if c is uppercase, that means it is part of the name of a token. Just add it and continue
            if c.isupper():
                tokenName += c
                continue
            
            # if c is *, that means that the rule should be matched 0 to inifnite times
            if c == '*':
                patternRule = Pattern.TokenRule(tokenName, repeat=True, minNumber=0, maxNumber=float('inf'))
                continue

            # if c is +, that means that the rule should be matched 1 to inifnite times
            elif c == '+':
                patternRule = Pattern.TokenRule(tokenName, repeat=True, maxNumber=float('inf'))
                continue

            # if c is ^, that means that the matching pattern will not be captured
            if c == '^':
                if patternRule != None:
                    patternRule.noncapturing = True
                else:
                    patternRule = Pattern.TokenRule(tokenName, noncapturing=True, minNumber=0, maxNumber=1)
                continue

            # if c is !, that means that it will match only if the rule is not satisfied
            if c == '!':
                if patternRule != None:
                    patternRule.inverted = True
                else:
                    patternRule = Pattern.TokenRule(tokenName, inverted=True, minNumber=0, maxNumber=1)
                continue

            # if c is =, it should be followed by a single character that will act as the 'key'. The metadata of this token must match the metadata assigned to this 'key' value. Used for matching balanced parentheses/brackets
            # example: r'OPAREN=1!,ALL*,OPAREN=1!' will match "1*(4+3)" from the expression: "(1*(4+3))""
            if c == '=':
                if patternRule != None:
                    patternRule.matching = regex[i+1]
                else:
                    patternRule = Pattern.TokenRule(tokenName, matching=regex[i+1], minNumber=1, maxNumber=1)
                i += 1
                continue

            # if c is ? and is preceded by a * or +, then the rule should act as a lazy rule. If it's not, then that means the rule should be matched 0 or 1 time
            if c == '?':
                if patternRule != None:
                    patternRule.lazy = True
                else:
                    patternRule = Pattern.TokenRule(tokenName, minNumber=0, maxNumber=1)
                continue

            # if c is ',', this means it is the border between two rules and the last rule should be appended to pattern.rules
            if c == ',':

                # if patternRule has not yet been assigned then append a generic Tokenrule with the name of the rule
                if patternRule == None:
                    print('appended default')
                    pattern.rules.append(Pattern.TokenRule(tokenName))

                # if patternRule has been assigned, then append it to pattern.rules
                else:
                    print('appended ' + str(patternRule))
                    pattern.rules.append(patternRule)
                    patternRule = None

                # reset tokenName and continue
                tokenName = ''
                continue
    
    # if tokenName hasn't been reset, that means that patternRule hasn't been appended, so this catches those cases
    if tokenName != '' or (patternRule != None and patternRule.tokenName == 'SUBPATTERN'):
        # same logic as before
        if patternRule == None:
            print('appended default')
            pattern.rules.append(Pattern.TokenRule(tokenName))

        # if patternRule has been assigned, then append it to pattern.rules and resets patternRule
        else:
            print('appended ' + str(patternRule))
            pattern.rules.append(patternRule)
            patternRule = None

    # if the method was called with the `returnPattern` param, then instead of appending to `patterns`, it returns the pattern
    if returnPattern == True:
        print('returned pattern' + str(pattern))
        return pattern

    print('ADDED ' + str(pattern) + ' TO PATTERNS')
    pattern.name = name
    patterns.append(pattern)

def search(tokens):
    matches = []
    print('LENGTH: ' + str(len(patterns)))
    for p in patterns:
        print('NOW SEARCHING: ' + str(p))
        matches.append( LexGen.Token(name=p.name, subtokens=searchPattern(p, tokens)))
    return matches

def searchPattern(pattern, tokens):

    # index of the rule currently being searched
    currentRule = 0

    # the number of matches the current rule has
    currentRuleMatched = 0

    # each match is added to matches
    matches = []

    # the match that is currently being added to before it is appended to matches
    currentMatch = []

    # index of the current token
    i = 0

    # loops while the token index is less than the length of the list of tokens
    while i < len(tokens):
        
        # variable to use instead of typing tokens[i] over and over
        t = tokens[i]

        # similar to t but holds the current value of r
        r = pattern.rules[currentRule]

        print('PATTERN RULES LEN: ' + str(currentRule))

        # if the token matches the rule and the rule allows for more matches
        print(str(t) + ' MATCHES: ' + str(r.matches(t) and r.matched < r.max) + ' R is ' + str(r))
        if (r.matches(t) and r.matched < r.max):
            print(1, t)

            # increments the number of matches the current rule has
            r.matched += 1

            # appends the current token to the current match
            if not r.noncapturing:
                currentMatch.append(t)

            # if the next token matches the next rule in the pattern
            print('CURRENTRULE: ' + str((currentRule + 2) < len(pattern.rules) and pattern.rules[currentRule + 1].min == 0))
            if (currentRule + 1) < len(pattern.rules) and i+1 < len(tokens) and pattern.rules[currentRule + 1].matches(tokens[i+1]):
                print(2, t)

                # changes the rule index to point to the next rule in the list
                currentRule += 1
            
            # if the next token does not match the next rule in the pattern but does match the rule 2 after the current rule AND the next rule is optional
            elif (currentRule + 2) < len(pattern.rules) and i+1 < len(tokens) and pattern.rules[currentRule + 2].matches(tokens[i+1]) and pattern.rules[currentRule + 1].min == 0:
                print(2.5, t)

                # increment the index pointing to the rule by 2
                currentRule += 2

        # if the token does not match the rule OR the rule does not allow for more matches
        # AND the first rule matches the current token (meaning that we should reset and start over at the current token)
        elif pattern.rules[0].matches(t):
            print(3, t)

            # then reset all of the values and decrement the token index so the funciton loops over the current one again
            i -= 1
            currentMatch = []
            r.matched = 0
            currentRule = 0
            pattern.reset()

        else:
            print(4, t)

            # resets the current token index and moves on to the next one
            currentMatch = []
            currentRule = 0
            pattern.reset()

        # if the entire pattern is satisfied then append the current match and reset the pattern. Continue matching
        if pattern.isSatisfied() and not (len(tokens) > i+1 and r.matches(tokens[i+1])):
            print(5, t)
            if len(currentMatch) > 0:
                matches.append(currentMatch)
            currentMatch = []
            pattern.reset()
        
        # increment the token index to look at the next one on the next iteration
        i += 1

    # return the list of matches      
    return matches


class Pattern:
    matchKeys = {}
    def __init__(self):
        self.rules = []
        self.name = ''

    def __str__(self):
        ret = ''
        for r in self.rules:
            print(r)
            ret += str(r)
        return ret

    def isSatisfied(self):
        for r in self.rules:
            print('testing if satisfied: ' + str(r))
            if not r.isSatisfied():
                return False
        return True
    def reset(self):
        for r in self.rules:
            r.matched = 0
    class TokenRule:
        

        def __init__(self, tokenName, repeat=False, minNumber=1, maxNumber=1, lazy=False, noncapturing = False, matching='', inverted=False):
            self.tokenName = tokenName
            self.repeat = repeat
            self.min = minNumber
            self.max = maxNumber
            self.lazy = lazy
            self.matched = 0
            self.noncapturing =  noncapturing
            self.matching = matching
            self.inverted = inverted
            if matching != '':
                Pattern.matchKeys[matching] = None

        def matches(self, token):
            print('COMPARING ' + str(self) + ', and ' + str(token))
            if self.matching != '':
                print(' matching evals to ' + str(Pattern.matchKeys[self.matching]))
            ret = (self.tokenName == token.name or (self.tokenName == r'\v' and token.name in ['FLOAT','INT','STR','CMD']) or (self.tokenName == 'ALL' and token.name != 'END')) and (self.matching == '' or Pattern.matchKeys[self.matching] == None or Pattern.matchKeys[self.matching] == token.metadata)

            if self.matching != '' and Pattern.matchKeys[self.matching] == token.metadata:
                Pattern.matchKeys[self.matching] = None
            elif ret and self.matching != '' and Pattern.matchKeys[self.matching] == None:
                Pattern.matchKeys[self.matching] = token.metadata
                
            print('EVALUATES TO ' + str(ret))
            if self.inverted:
                return not ret
            return ret
        def __str__(self):
            return '('+ 'tokenName:' + self.tokenName + '\trepeat:' + str(self.repeat) + '\tmin:' + str(self.min) + '\tmax:' + str(self.max) + '\tlazy:' + str(self.lazy) + '\tmatched:' + str(self.matched) + '\tsatisfied:' + str(self.isSatisfied()) + ' inverted:' + str(self.inverted) + ')'

        def isSatisfied(self):
            return (self.matched >= self.min and self.matched <= self.max)
        



