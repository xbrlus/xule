'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change:  $
'''

from pyparsing import (Word, Keyword,  CaselessKeyword, ParseResults, infixNotation,
                 Literal, CaselessLiteral, FollowedBy, opAssoc,
                 Combine, Optional, nums, Forward, Group, ZeroOrMore,  
                 ParserElement,  delimitedList, Suppress, Regex, 
                 QuotedString, OneOrMore, oneOf, cStyleComment,
                 lineEnd, White, SkipTo, Empty, stringStart, stringEnd, alphas, printables, removeQuotes)

def buildPrecedenceExpressions( baseExpr, opList, lpar=Suppress('('), rpar=Suppress(')')):
    """Simplified and modified version of pyparsing infixNotation helper function
    
    Args:
        baseExpr: The parser that is the operand of the operations
        opList: The list of operators that can be applied to the operand. This is a list in order of operator
            precedence. Highest precedence is first. Each item in the list is a tuple of:
                1 - operator expression: parser that is the operator
                2 - arity: the number of operands. only 1 and 2 are supported
                3 - associativeness: pyparsing.opAssoc.LEFT or pyparsing.opAssoc.RIGHT. Only left is supported for
                                        arity of 2 and right for arity of 1.
                4 - parserAction: parser action for the operation parser that is created.
        lpar: Parenthesized expressions are not supported in this version. This is ignored.
        rpar: Parenthesized expressions are not supported in this version. This is ignored.
        
    Returns:
        This returns a pyparsing parser.
    
    This version only handles binary and unary operations that are left associative. It also does not handle parenthesized
    expressions. It uses the same parameters as the infixNotation. This makes it easy to switch between this 
    version and the official pyparsing version.
    
    This version add results names to the parser. When outputting as a dictionary, it will generate a structure as:
        {'binaryExpr': [
            {'leftExpr' : {...},
             'rights' : [
                             {'op': ...,
                              'rightExpr' : {...}
                             },
                             ...
                        ]
            }
        }
    """
    ret = Forward()
    lastExpr = baseExpr #| ( lpar + ret + rpar )
    for i,operDef in enumerate(opList):
        opExpr,arity,rightLeftAssoc,pa,exprName = (operDef + (None, None))[:5]
        
        #check restrictions
        if arity not in (1, 2):
            raise ValueError('This is a modified version of the pyparsing infixNotation helper function. Only arity of 1 or 2 is supported.')
        if arity == 1 and rightLeftAssoc != opAssoc.RIGHT:
            raise ValueError('This is a modified version of the pyparsing infixNotation helper function. When arity is 1 only right associative operations are supported.')
        if arity == 2 and rightLeftAssoc != opAssoc.LEFT:
            raise ValueError('This is a modified version of the pyparsing infixNotation helper function. When arity is 2 only left associative operations are supported.')

        if opExpr is None:
            raise ValueError('This is a modified version of the pyparsing infixNotation helper function. opExpr must be supplied.')
        termName = "%s term" % opExpr if arity < 3 else "%s%s term" % opExpr
        thisExpr = Forward().setName(termName)
        
        if arity == 1:
#             # try to avoid LR with this extra test
#             if not isinstance(opExpr, Optional):
#                 opExpr = Optional(opExpr)
            #original - matchExpr = FollowedBy(opExpr.expr + thisExpr) + Group( opExpr + thisExpr )
            if exprName is None:
                exprName = 'unaryExpr'
            matchExpr = (FollowedBy(opExpr + lastExpr) + \
                        ( opExpr.setResultsName('op') + lastExpr.setResultsName('expr') ) + nodeName(exprName))
        else: #arity == 2
            #original -matchExpr = FollowedBy(lastExpr + opExpr + lastExpr) + ( lastExpr + OneOrMore( opExpr + lastExpr ) )
            if exprName is None:
                exprName = 'binaryExpr'
            matchExpr = (FollowedBy(lastExpr + opExpr + lastExpr) + \
                      ( lastExpr.setResultsName('leftExpr') + 
                        Group(OneOrMore(Group( opExpr.setResultsName('op') + 
                                   lastExpr.setResultsName('rightExpr') +
                                   nodeName('rightOperation')))).setResultsName('rights') ) +
                              nodeName(exprName)
                         )
            
        if pa:
            if isinstance(pa, (tuple, list)):
                matchExpr.setParseAction(*pa)
            else:
                matchExpr.setParseAction(pa)
        thisExpr <<= (Group(matchExpr.setName(termName)) | lastExpr )
        lastExpr = thisExpr
    ret <<= lastExpr
    return ret

def nodeName(name):
    return Empty().setParseAction(lambda: name).setResultsName('exprName')

def get_grammar():
    """Return the XULE grammar"""
    
    ParserElement.enablePackrat()
    
    #comment = cStyleComment() | (Literal("//") + SkipTo(lineEnd()))
    comment = cStyleComment | (Literal("//") + SkipTo(lineEnd))
    
    #expression forwards
    expr = Forward()
    blockExpr = Forward()

    #keywords
    assertKeyword = CaselessKeyword('assert')
    outputKeyword = CaselessKeyword('output')
    outputAttributeKeyword = CaselessKeyword('output-attribute')
    ruleNamePrefixKeyword = CaselessKeyword('rule-name-prefix')
    ruleNameSeparatorKeyword = CaselessKeyword('rule-name-separator')
    namespaceKeyword = CaselessKeyword('namespace')
    constantKeyword = CaselessKeyword('constant')
    functionKeyword = CaselessKeyword('function')
    
    declarationKeywords = (assertKeyword | outputKeyword | outputAttributeKeyword | namespaceKeyword | constantKeyword | functionKeyword | ruleNamePrefixKeyword | ruleNameSeparatorKeyword)

    lParen = Literal('(')
    rParen = Literal(')')
    lCurly = Literal('{')
    rCurly = Literal('}')
    lSquare = Literal('[')
    rSquare = Literal(']')
    bar = Literal('|')
    coveredAspectStart = Literal('@').setParseAction(lambda s, l, t: 'covered')
    uncoveredAspectStart = Literal('@@').setParseAction(lambda s, l, t: 'uncovered')
    propertyOp = Literal('.')
    assignOp = Literal('=')
    asOp = CaselessKeyword('as')
    commaOp = Literal(',')
    ifOp = CaselessKeyword('if')
    thenOp = CaselessKeyword('then')
    elseOp = CaselessKeyword('else')
    forOp = CaselessKeyword('for')
    inOp = CaselessKeyword('in')

    varIndicator = Literal('$')
    methodOp = Literal(".")
    
    #operators
    unaryOp = oneOf('+ -')
    multiOp = oneOf('* /')
    addOp = oneOf('+> -> + - <+> <+ <-> <-')
    symDiffOp = Literal('^')
    intersectOp = Literal('&')
    notOp = CaselessKeyword('not')
    andOp = CaselessKeyword('and')
    orOp = CaselessKeyword('or')
    notInOp = Combine(notOp + White().setParseAction(lambda: ' ') + inOp)
    compOp = oneOf('== != <= < >= >') | inOp | notInOp
    
    #numeric literals
    sign = oneOf("+ -")
    sciNot = Literal("e")
    decimalPoint = CaselessLiteral(".")
    digits = Word(nums)
    integerPart = Combine(Optional(sign) + digits)
    integerLiteral = Group(integerPart.setResultsName("value") +
                      nodeName('integer'))
    infLiteral = Combine(Optional(sign) + CaselessKeyword("INF"))
    floatLiteral = Group((Combine(decimalPoint + digits + Optional(sciNot + integerPart)) |
                     Combine(integerPart + decimalPoint + Optional(digits, default='0') + Optional(sciNot + integerPart)) |
                     infLiteral).setResultsName("value") +
                    nodeName('float'))
    #string literals
    stringLiteral = Group(((QuotedString("'", multiline=True, unquoteResults=False, escChar="\\").setParseAction(removeQuotes)  | 
                      QuotedString('"', multiline=True, unquoteResults=False, escChar="\\").setParseAction(removeQuotes)).setResultsName("value")) +
                     nodeName('string'))
    
    #boolean literals
    booleanLiteral = Group((CaselessKeyword("true") | CaselessKeyword("false")).setResultsName("value") + nodeName('boolean'))
    
    #none literal
    noneLiteral = Group(CaselessKeyword("none").setResultsName('value') + nodeName('none'))
    #unbound
    unboundLiteral = Group(CaselessKeyword("unbound").setResultsName('value') + nodeName('none'))
    
    #severity literals  
    errorLiteral = CaselessKeyword("error")
    warningLiteral = CaselessKeyword("warning")
    okLiteral = CaselessKeyword("ok")
    passLiteral = CaselessKeyword("pass")
    severityLiteral = Group((errorLiteral | warningLiteral | okLiteral | passLiteral).setResultsName('value') + nodeName('severity'))
    
    #direction keywords
    directionLiteral = ((CaselessKeyword('ancestors').setResultsName('direction') + Optional(digits, -1).setResultsName('depth')) |  
                        (CaselessKeyword('descendants').setResultsName('direction')  + Optional(digits, -1).setResultsName('depth')) | 
                        CaselessKeyword('parents').setResultsName('direction') |
                        CaselessKeyword('children').setResultsName('direction') |
                        CaselessKeyword('siblings').setResultsName('direction') | 
                        CaselessKeyword('previous-siblings').setResultsName('direction') | 
                        CaselessKeyword('following-siblings').setResultsName('direction') | 
                        CaselessKeyword('self').setResultsName('direction'))
    
    qNameOp = Literal(":")
    ncName = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
                  "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_.-]*)"
                  )
#     prefix = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
#              "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_.-]*)"
#               )
    
    # A simpleName is a ncName that does not allow a dot.
    simpleName = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
                  "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_-]*)"
                  )
    # A qName normally allows a dot character as long it is not the first character. In Xule, the doc is used to indicate a property. For qName literals
    # a dot character will have to be escaped  by a backslash. Assets\.Current is the 
    # A qNameLocalName does not allow a dot unless it is escaped with a backslash.  Assets.local-part is a qname with a property of local-part. Assets\.local-part is a qname of "Assets.local-part".
    qNameLocalName = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF"
                           "\uF900-\uFDCF\uFDF0-\uFFFD_]"
                           "([A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF"
                           "\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_-]|(\\\.))"
                           "*)"
                  ).setParseAction(lambda s, l, t: [t[0].replace('\\','')]) #parse action removes the escape backslash character
    prefix = qNameLocalName

    qName = Group(Optional(Combine(prefix + ~White() + Suppress(qNameOp)), default="*").setResultsName("prefix") + 
                  ~White() 
                  + qNameLocalName.setResultsName("localName")
                  + nodeName('qname'))

    tagOp = Literal('#').setParseAction(lambda: True).setResultsName('tagged')
    tagName = simpleName.setResultsName('tagName')

    covered = CaselessKeyword('covered').setParseAction(lambda: True).setResultsName('covered')
    where = CaselessKeyword('where')
    returns = CaselessKeyword('returns')
    

    properties = Group(OneOrMore(Group(Suppress(propertyOp) +
                                       simpleName.setResultsName('propertyName') +
                                       Optional(Group(Suppress(lParen) +
                                                Optional(delimitedList(blockExpr)) +
                                                Suppress(rParen)
                                                ).setResultsName('propertyArgs')
                                                
                                                ) +
                                       Optional(tagOp + tagName)
                                       + nodeName('property')
                                 ))
                       ).setResultsName('properties')


    whereClause = Suppress(where) + blockExpr.setResultsName('whereExpr')
    returnsClause = Suppress(returns) + blockExpr.setResultsName('returnsExpr')

    # Note the order of uncovered and covered is important. The uncovered must go first because it is a @@
    # while the coveted is a single @. If the order is flipped, the parser will think a @@ is two consecute
    # single @s instead of a single double @.
    aspectStart = (uncoveredAspectStart | coveredAspectStart).setResultsName('coverType') + ~coveredAspectStart + ~White()
    
    aspectName = ((CaselessKeyword('concept') | 
                   CaselessKeyword('unit') | 
                   CaselessKeyword('entity') | 
                   CaselessKeyword('period') | 
                   CaselessKeyword('table')).setResultsName('aspectName') +
                   Optional(
                            #properties.setResultsName('aspectProperties'))
                        Suppress(propertyOp) +
                        ncName.setResultsName('propertyName') +
                        Optional(Group(Suppress(lParen) +
                                       Optional(delimitedList(blockExpr)) +
                                       Suppress(rParen)
                                       ).setResultsName('propertyArgs')
                        )                        
                    )
                  )| Optional(qName.setResultsName('aspectDimensionName'))
    
    aspectOp = assignOp | Literal('!=') | inOp | notInOp
    
    aspectFilter = (aspectStart + 
                    Optional(aspectName +
                             Optional(aspectOp.setResultsName('aspectOperator') + 
                                      (Literal('*').setResultsName('wildcard') |
                                       blockExpr.setResultsName('aspectExpr')
                                      )
                                      ) +
                             Optional(Suppress(asOp) + Suppress(varIndicator) + ~White()+ simpleName.setResultsName('alias'))
                             )
                    + nodeName('aspectFilter'))
    
    factsetInner = (Optional(covered) + 
                    ZeroOrMore(Group(aspectFilter)).setResultsName('aspectFilters') +
#                     Optional((whereClause) | blockExpr.setResultsName('innerExpr')
                    Optional(~ where + blockExpr.setResultsName('innerExpr') ) +
                    Optional(whereClause)
                    )
                    
    
    factset = Group(
                (       
                     (
                      Suppress(lCurly) + 
                      factsetInner +                    
                      Suppress(rCurly) +
                      Empty().setParseAction(lambda s, l, t: 'open').setResultsName('factsetType')
                      ) |
                     (
                      Suppress(lSquare) + 
                      factsetInner +                    
                      Suppress(rSquare) +
                      Empty().setParseAction(lambda s, l, t: 'closed').setResultsName('factsetType')
                      ) |
                      Optional(covered) +
                      Group(OneOrMore(Group(aspectFilter))).setResultsName('aspectFilters') + #This is a factset without enclosing brackets
                      Empty().setParseAction(lambda s, l, t: 'open').setResultsName('factsetType') +
                      Optional(whereClause)
                ) +
                nodeName('factset')        
            )
    
    returnComponents = (Group(simpleName).setResultsName('returnComponents') |
                        (Suppress('(') +
                         Group(delimitedList(simpleName + ~Literal(':') | blockExpr)).setResultsName('returnComponents') +
                         Suppress(')'))
                        )
    
    navigation = Group(
                       Suppress(CaselessKeyword('navigate')) + 
                       # The dimension and arcrole need the FollowedBy() look ahead. I'm not sure why, but it is because these are optional and the direction is reuired.
                       # Without the FollowedBy() look ahead, 'navigate self' fails because the parser thinks 'navigate' is a qname and then does not know what to 
                       # do with 'self'.
                       Optional(CaselessKeyword('dimensions').setParseAction(lambda: True).setResultsName('dimensional') + (FollowedBy(blockExpr | directionLiteral) )) +
                       Optional(blockExpr.setResultsName('arcrole') + FollowedBy(directionLiteral)) +  
                       directionLiteral +
                       Optional(Group(CaselessKeyword('include') + CaselessKeyword('start')).setParseAction(lambda: True).setResultsName('includeStart')) +
                       Optional(Suppress(CaselessKeyword('from')) + blockExpr.setResultsName('from')) +
                       Optional(Suppress(CaselessKeyword('to')) + blockExpr.setResultsName('to')) +
                       Optional(Suppress(CaselessKeyword('role')) + blockExpr.setResultsName('role')) +
                       Optional(Suppress(CaselessKeyword('drs-role')) + blockExpr.setResultsName('drsRole')) +
                       Optional(Suppress(CaselessKeyword('linkbase')) + blockExpr.setResultsName('linkbase')) +
                       Optional(Suppress(CaselessKeyword('table')) + blockExpr.setResultsName('table')) +
                       Optional(Suppress(CaselessKeyword('taxonomy')) + blockExpr.setResultsName('taxonomy')) +
                       Optional(whereClause) +
                       Optional(Group(
                                      Suppress(CaselessKeyword('returns')) +
                                      Optional(Group(CaselessKeyword('by') + CaselessKeyword('network')).setParseAction(lambda: True).setResultsName('byNetwork')) +                                    
                                      Optional(
                                             CaselessKeyword('list') |
                                             CaselessKeyword('set') 
                                             ).setResultsName('returnType') +
                                      Optional(CaselessKeyword('paths').setParseAction(lambda: True).setResultsName('paths')) +
                                      Optional(returnComponents +
                                               Optional(Suppress(CaselessKeyword('as')) + CaselessKeyword('dictionary').setResultsName('returnComponentType'))) +
                                      nodeName('returnExpr')
                                ).setResultsName('return')
                        ) +
                       nodeName('navigation')
                )
    
    filter = Group(
                   Suppress(CaselessKeyword('filter')) +
                   blockExpr.setResultsName('expr') + 
                   Optional(whereClause) +
                   Optional(returnsClause) +
                   nodeName('filter')
                   )
    #function reference
    funcRef = Group(simpleName.setResultsName("functionName") + ~White() +
                    Suppress(lParen) + 
                    Group(Optional(delimitedList(blockExpr)  +
                                   Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                   )).setResultsName("functionArgs") + 
                Suppress(rParen) +
                nodeName('functionReference')) 

    #variable reference
    varRef = Group(Suppress(varIndicator) + simpleName.setResultsName("varName") + nodeName('varRef'))

    #if expression
    elseIfExpr = (ZeroOrMore(Group(Suppress(elseOp + ifOp) + 
                                    blockExpr.setResultsName("condition") +
                                    blockExpr.setResultsName("thenExpr") +
                                    nodeName('elseIf')
                                    )
                              ).setResultsName("elseIfExprs")
                   )

    ifExpr = Group(Suppress(ifOp) + 
                   
                   blockExpr.setResultsName("condition") + 
                   
                   blockExpr.setResultsName("thenExpr") +
                   # this will flatten nested if conditions 
                   elseIfExpr +
                   Suppress(elseOp) + 
                   blockExpr.setResultsName("elseExpr") +
                   nodeName('ifExpr')
              ) 
              
    forExpr = Group(#with parens around the for control
               ((Suppress(forOp) + 
                #for loop control: for var name and loop expression
                Suppress(lParen) + 
                Combine(Suppress(varIndicator) + ~White() + simpleName.setResultsName("forVar")) + 
                Suppress(inOp) + 
                blockExpr.setResultsName("forLoopExpr") +
                Suppress(rParen) +
                #for body expression
                blockExpr.setResultsName("forBodyExpr") + 
                nodeName('forExpr'))) |
               
               #without parens around the for control
               ((Suppress(forOp) + 
                #for loop control
                Combine(Suppress(varIndicator) + ~White() + simpleName.setResultsName("forVar")) + 
                Suppress(inOp) + 
                blockExpr.setResultsName("forLoopExpr") +
                #for body expression
                blockExpr.setResultsName("forBodyExpr") + 
                nodeName('forExpr')))
               )
    
    listLiteral =  Group( 
                        Suppress(lParen) +
                        Group(Optional(delimitedList(blockExpr) +
                                       Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                       )).setResultsName("functionArgs") + 
                        Suppress(rParen) +
                        nodeName('functionReference') +
                       
                       Empty().setParseAction(lambda s, l, t: "list").setResultsName("functionName")
                       )
    
    atom = (
            #listLiteral |
            # parenthesized expression - This needs to be up front for performance. 
            (Suppress(lParen) + blockExpr + Suppress(rParen)) |            
            
            ifExpr |
            forExpr |

            #literals
            floatLiteral |
            integerLiteral |
            stringLiteral |
            booleanLiteral |
            severityLiteral |
            noneLiteral |
            unboundLiteral |
            
            factset |
            navigation |
            filter |
            
            funcRef | 
            varRef|
            
            qName #|

            #list literal - needs to be at the end.
            #listLiteral 
            )

    #expressions with precedence.
    #taggedExpr = (Group(atom) + Suppress('#') + tagName + nodeName('taggedExpr')) | atom
    
    taggedExpr = Group(atom.setResultsName('expr') + Suppress('#') + tagName + nodeName('taggedExpr')) | atom
        
#     unaryExpr = Group(unaryOp.setResultsName('op') + 
#                        #~digits + ~CaselessLiteral('INF') + 
#                        Group(taggedExpr).setResultsName('expr') +
#                       nodeName('unaryExpr')) | taggedExpr
                       
    indexExpr = Group(taggedExpr.setResultsName('expr') +
                      OneOrMore((Suppress(lSquare) + blockExpr + 
                                      Suppress(rSquare) )).setResultsName('indexes') +
                      nodeName('indexExpr')) | taggedExpr
    
    propertyExpr = Group(indexExpr.setResultsName('expr') +
                         properties +
                         nodeName('propertyExpr')) | indexExpr
     
    expr << buildPrecedenceExpressions(propertyExpr,
                          [(unaryOp, 1, opAssoc.RIGHT, None, 'unaryExpr'),
                           (multiOp, 2, opAssoc.LEFT, None, 'multExpr'),
                           (addOp, 2, opAssoc.LEFT, None, 'addExpr'),
                           (intersectOp, 2, opAssoc.LEFT, None, 'intersectExpr'),
                           (symDiffOp, 2, opAssoc.LEFT, None, 'symetricDifferenceExpr'),
                           (compOp, 2, opAssoc.LEFT, None, 'compExpr'),
                           (notOp, 1, opAssoc.RIGHT, None, 'notExpr'),
                           (andOp, 2, opAssoc.LEFT, None, 'andExpr'),
                           (orOp, 2, opAssoc.LEFT, None, 'orExpr')
                          ])

    varDeclaration = (
                           Suppress(varIndicator) + ~White() +
                           simpleName.setResultsName('varName') +   
                           Optional(tagOp +
                                    Optional(tagName)) + 
                           Suppress('=') +
                           blockExpr.setResultsName('body') + Optional(Suppress(';')) +
                           nodeName('varDeclaration')
                           )

    blockExpr << (Group((OneOrMore(Group(varDeclaration)).setResultsName('varDeclarations') + 
                        expr.setResultsName('expr') +
                        nodeName('blockExpr'))) | expr)
    
    #nsURI is based on XML char (http://www.w3.org/TR/xml11/#NT-Char) excluding the space character
    nsURI = Regex("["
                  "\u0021-\u007E"
                  "\u0085"
                  "\u00A0-\uFDCF"
                  "\uE000-\uFDCF"
                  "\uFDF0-\uFFFD"
                  "\u10000-\u1FFFD"
                  "\u20000-\u2FFFD"
                  "\u30000-\u3FFFD"
                  "\u40000-\u4FFFD"
                  "\u50000-\u5FFFD"
                  "\u60000-\u6FFFD"
                  "\u70000-\u7FFFD"
                  "\u80000-\u8FFFD"
                  "\u90000-\u9FFFD"
                  "\uA0000-\uAFFFD"
                  "\uB0000-\uBFFFD"
                  "\uC0000-\uCFFFD"
                  "\uD0000-\uDFFFD"
                  "\uE0000-\uEFFFD"
                  "\uF0000-\uFFFFD"
                  "\u100000-\u10FFFD"
                  "]*")   

    namespaceDeclaration = (
                                 Suppress(namespaceKeyword) +
                                 (
                                  #The prefix is optional. This either matches when the prefix is there or empty to capture the default.
                                  (
                                   prefix.setResultsName('prefix') +
                                   Suppress(Literal('='))
                                   ) |
                                  Empty().setParseAction(lambda s, l, tok: '*').setResultsName('prefix')
                                  ) +
                                 nsURI.setResultsName('namespaceURI') +
                                 nodeName('nsDeclaration')
                                 )

#     outputAttributeDeclaration = Group(
#                                        Suppress(outputAttributeKeyword) +
#                                        simpleName.setResultsName('attributeName')).setResultsName('outputAttributeDeclaration')

    outputAttributeDeclaration = (
                                   Suppress(outputAttributeKeyword) +
                                   simpleName.setResultsName('attributeName') +
                                   nodeName('outputAttributeDeclaration')
                                 )
    
    ruleNamePrefix = (
                      Suppress(ruleNamePrefixKeyword) +
                      ncName.setResultsName('prefix') +
                      nodeName('ruleNamePrefix')
                      )
    
    ruleNameSeparator = (
                         Suppress(ruleNameSeparatorKeyword) +
                         Word(printables).setResultsName('separator') +
                         nodeName('ruleNameSeparator')
                         )
    
    ruleResult = Group( ~declarationKeywords +
                         (CaselessKeyword('message') | CaselessKeyword('severity') | simpleName).setResultsName('resultName') +
                         expr.setResultsName('resultExpr') + nodeName('result')
                    )

    assertDeclaration = (
                              Suppress(assertKeyword) +
                              ncName.setResultsName('ruleName') +
                              Optional(CaselessKeyword('satisfied') | CaselessKeyword('unsatisfied'), default='satisfied').setResultsName('satisfactionType') +
                              blockExpr.setResultsName('body') +
                              ZeroOrMore(ruleResult).setResultsName('results') +
                              nodeName('assertion')
                              )

    outputDeclaration = (
                              Suppress(outputKeyword) +
                              ncName.setResultsName('ruleName') +
                              blockExpr.setResultsName('body') +
                              ZeroOrMore(ruleResult).setResultsName('results') +
                              nodeName('outputRule')
                              )

    constantDeclaration = (
                  Suppress(constantKeyword) +
                  Suppress(varIndicator) + ~ White() +
                  simpleName.setResultsName("constantName") + 
                  Optional(tagOp +
                           Optional(tagName)) + 
                  Suppress(assignOp) + 
                  expr.setResultsName("body") +
                  nodeName('constantDeclaration')
            )                            

    functionDeclaration = (
        Suppress(functionKeyword) + 
        simpleName.setResultsName("functionName") + ~White() +
        Suppress(lParen) + 
        Group(Optional(delimitedList(Group(Suppress(varIndicator) + ~White() + simpleName.setResultsName('argName') + nodeName('functionArg') + 
                                           Optional(tagOp +
                                                    Optional(tagName)))) +
                       Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
        )).setResultsName("functionArgs") + 
        Suppress(rParen) +
        blockExpr.setResultsName("body") +
        nodeName('functionDeclaration')
        )
                     
    xuleFile = (stringStart +
                ZeroOrMore(Group(ruleNameSeparator |
                                 ruleNamePrefix |
                                 namespaceDeclaration |
                                 outputAttributeDeclaration |
                                 functionDeclaration |
                                 constantDeclaration |
                                 assertDeclaration |
                                 outputDeclaration)) +
                stringEnd).setResultsName('xuleDoc').ignore(comment)
    #xuleFile = Group(ZeroOrMore(factset)).setResultsName('xuleDoc')
    
    #xuleFile = (stringStart + Optional(header) + ZeroOrMore(packageBody) + stringEnd).setResultsName("xule").ignore(comment)
    
    return xuleFile
