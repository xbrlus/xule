'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change:  $
'''
from lxml.html.builder import OPTION
from argparse import OPTIONAL
from pyparsing import (Word, Keyword,  CaselessKeyword, ParseResults, infixNotation,
                 Literal, CaselessLiteral, FollowedBy, opAssoc,
                 Combine, Optional, nums, Forward, Group, ZeroOrMore,  
                 ParserElement,  delimitedList, Suppress, Regex, 
                 QuotedString, OneOrMore, oneOf, cStyleComment,
                 lineEnd, White, SkipTo, Empty, stringStart, stringEnd, alphas)

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
    
    This version only handles binary and unary operations that are left associative. It also does not handle  parenthesized
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
    lastExpr = baseExpr 
    for i,operDef in enumerate(opList):
        opExpr,arity,rightLeftAssoc,pa,exprName = (operDef + (None, None))[:5]
        
        #check restrictions
        if arity not in (1, 2):
            raise ValueError('This is a modified version of the pyparsing infixNotation helper function. Only arity of 1 or 2 is supported.')
        if arity == 1 and rightLeftAssoc != opAssoc.RIGHT:
            raise ValueError('This is a modified version of the pyparsing infixNotation helper function. When arity is 1 only right associative operations are supported.')
        if arity == 2 and rightLeftAssoc != opAssoc.LEFT:
            raise ValueError('This is a modified version of teh pyparsing infixNotation helper function. When arity is 2 only left associative operations are supported.')

        if opExpr is None:
            raise ValueError('This is a modified version of teh pyparsing infixNotation helper function. opExpr must be supplied.')
        termName = "%s term" % opExpr if arity < 3 else "%s%s term" % opExpr
        thisExpr = Forward().setName(termName)
        
        if arity == 1:
#             # try to avoid LR with this extra test
#             if not isinstance(opExpr, Optional):
#                 opExpr = Optional(opExpr)
            #original - matchExpr = FollowedBy(opExpr.expr + thisExpr) + Group( opExpr + thisExpr )
            if exprName is None:
                exprName = 'unaryExpr'
            matchExpr = Group(FollowedBy(opExpr + lastExpr) + ( opExpr.setResultsName('op') + lastExpr.setResultsName('expr') )).setResultsName(exprName)
        else: #arity == 2
            #original -matchExpr = FollowedBy(lastExpr + opExpr + lastExpr) + ( lastExpr + OneOrMore( opExpr + lastExpr ) )
            if exprName is None:
                exprName = 'binaryExpr'
            matchExpr = Group(FollowedBy(lastExpr + opExpr + lastExpr) + \
                      ( lastExpr.setResultsName('leftExpr') + 
                        Group(OneOrMore(Group( opExpr.setResultsName('op') + 
                                   lastExpr.setResultsName('rightExpr') ))).setResultsName('rights') )
                         ).setResultsName(exprName)
            
        if pa:
            if isinstance(pa, (tuple, list)):
                matchExpr.setParseAction(*pa)
            else:
                matchExpr.setParseAction(pa)
        thisExpr <<= (Group(matchExpr.setName(termName)) | lastExpr )
        lastExpr = thisExpr
    ret <<= lastExpr
    return ret

def get_grammar():
    """Return the XULE grammar"""
    
    ParserElement.enablePackrat()
    
    
    #expression forwards
    expr = Forward()
    blockExpr = Forward()

    #keywords
    assertKeyword = CaselessKeyword('assert')
    outputKeyword = CaselessKeyword('output')
    outputAttributeKeyword = CaselessKeyword('output-attribute')
    namespaceKeyword = CaselessKeyword('namespace')
    constantKeyword = CaselessKeyword('constant')
    functionKeyword = CaselessKeyword('function')
    
    declarationKeywords = (assertKeyword | outputKeyword | outputAttributeKeyword | namespaceKeyword | constantKeyword | functionKeyword)

    lParen = Literal('(')
    rParen = Literal(')')
    lCurly = Literal('{')
    rCurly = Literal('}')
    bar = Literal('|')
    coveredAspectStart = Literal('@').setParseAction(lambda s, l, t: 'covered')
    uncoveredAspectStart = Literal('@@').setParseAction(lambda s, l, t: 'uncovered')
    propertyOp = Literal('.')
    assignOp = Literal('=')
    aspectOp = Literal('=') | Literal('!=') | CaselessKeyword('in')
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
    addOp = oneOf('+ -')
    compOp = oneOf('== != <= < >= >')
    notOp = CaselessKeyword('not')
    andOp = CaselessKeyword('and')
    orOp = CaselessKeyword('or')

    #numeric literals
    sign = oneOf("+ -")
    sciNot = Literal("e")
    decimalPoint = CaselessLiteral(".")
    digits = Word(nums)
    integerPart = Combine(Optional(sign) + digits)
    integerLiteral = integerPart.setResultsName("integer")
    infLiteral = Combine(Optional(sign) + CaselessKeyword("INF"))
    floatLiteral = (Combine(decimalPoint + digits + Optional(sciNot + integerPart)) |
                     Combine(integerPart + decimalPoint + Optional(digits, default='0') + Optional(sciNot + integerPart)) |
                     infLiteral).setResultsName("float")
    #string literals
    stringLiteral = (QuotedString("'", multiline=True, unquoteResults=False, escChar="\\")  | 
                      QuotedString('"', multiline=True, unquoteResults=False, escChar="\\")).setResultsName("string")
    
    #boolean literals
    booleanLiteral = (CaselessKeyword("true") | CaselessKeyword("false")).setResultsName("boolean")
    
    #none literal
    noneLiteral = CaselessKeyword("none").setResultsName('none')
    
    #severity literals  
    errorLiteral = CaselessKeyword("error")
    warningLiteral = CaselessKeyword("warning")
    infoLiteral = CaselessKeyword("info")
    passLiteral = CaselessKeyword("pass")
    severityLiteral = (errorLiteral | warningLiteral | infoLiteral | passLiteral).setResultsName('severity')
    
    qNameOp = Literal(":")
    ncName = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
                  "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_-]*)"
                  )
    prefix = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
             "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_.-]*)"
              )
    simpleName = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
                  "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_-]*)"
                  )
 
    #ncName = Word(r'_-.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    #prefix = Word('_-.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    # The + ~qNameOp is needed to disambiguate qNames with ":" from method operators "::".
    qName = Group(Optional(Combine(prefix + ~White() + Suppress(qNameOp) + ~qNameOp), default="*").setResultsName("prefix") + 
                  ~White() 
                  + ncName.setResultsName("localName")).setResultsName("qname")

    tagOp = Literal('#').setParseAction(lambda s, l, t: True).setResultsName('tagged')
    tagName = ncName.setResultsName('tagName')

    covered = CaselessKeyword('covered').setParseAction(lambda s, l, t: True).setResultsName('covered')
    where = CaselessKeyword('where')
    

    properties = Group(OneOrMore(Group(Suppress(propertyOp) +
                                       simpleName.setResultsName('propertyName') +
                                       Optional(tagOp + tagName)
                                 ))).setResultsName('properties')


    whereClause = Suppress(where) + blockExpr.setResultsName('whereExpr')

    # Note the order of uncovered and covered is important. The uncovered must go first because it is a @@
    # while the coveted is a single @. If the order is flipped, the parser will think a @@ is two consecute
    # single @s instead of a single double @.
    aspectStart = (uncoveredAspectStart | coveredAspectStart).setResultsName('coverType') + ~coveredAspectStart + ~White()
    
    aspectName = ((CaselessKeyword('concept') | CaselessKeyword('unit') | CaselessKeyword('entity') | CaselessKeyword('period') | CaselessKeyword('table')).setResultsName('aspectName') +
                   Optional(properties))| Optional(qName.setResultsName('aspectDimensionName'))
        
    aspectFilter = Group(aspectStart + 
                    Optional(aspectName +
                             Optional(aspectOp.setResultsName('aspectOperator') + blockExpr.setResultsName('aspectExpr')) +
                             Optional(Suppress(asOp) + simpleName.setResultsName('alias'))
                             )).setResultsName('aspectFilter')
    
    factsetInner = (Optional(covered) + 
                    ZeroOrMore(Group(aspectFilter)).setResultsName('aspectFilters') + 
                    Optional(~ where + blockExpr.setResultsName('innerExpr')) +
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
                              Suppress(bar) + 
                              factsetInner +                    
                              Suppress(bar) +
                              Empty().setParseAction(lambda s, l, t: 'closed').setResultsName('factsetType')
                              ) |
                              Group(OneOrMore(Group(aspectFilter))).setResultsName('aspectFilters') + #This is a factset without enclosing brackets
                              Empty().setParseAction(lambda s, l, t: 'open').setResultsName('factsetType') +
                              Optional(whereClause)
                        ) 
                    
                    ).setResultsName('factset')
    
    direction = oneOf('ancestors parents descendants children siblings previous-siblings following-siblings self',
                      caseless=True).setResultsName('direction')
    
    returnComponents = (Group(Word(alphas)).setResultsName('returnComponents') |
                        (Suppress('(') +
                         Group(delimitedList(Word(alphas))).setResultsName('returnComponents') +
                         Suppress(')'))
                        )
    
    navigation = Group(
                       Suppress(CaselessKeyword('navigate')) + 
                       Optional(CaselessKeyword('dimensions').setParseAction(lambda s, l, t: True).setResultsName('dimensional')) +
                       Optional(blockExpr.setResultsName('arcrole')) +
                       direction +
                       Optional(Group(CaselessKeyword('include') + CaselessKeyword('start')).setParseAction(lambda s, l, : True).setResultsName('includeStart')) +
                       Optional(Suppress(CaselessKeyword('from')) + blockExpr.setResultsName('from')) +
                       Optional(Suppress(CaselessKeyword('to')) + blockExpr.setResultsName('to')) +
                       Optional(Suppress(CaselessKeyword('role')) + blockExpr.setResultsName('role')) +
                       Optional(Suppress(CaselessKeyword('drs-role')) + blockExpr.setResultsName('drsRole')) +
                       Optional(Suppress(CaselessKeyword('linkbase')) + blockExpr.setResultsName('linkbase')) +
                       Optional(Suppress(CaselessKeyword('table')) + blockExpr.setResultsName('table')) +
                       Optional(Suppress(CaselessKeyword('in')) + blockExpr.setResultsName('taxonomy')) +
                       Optional(whereClause) +
                       Optional(Group(
                                      Suppress(CaselessKeyword('returns')) +
                                      Optional((
                                                     CaselessKeyword('list') |
                                                     CaselessKeyword('set') |
                                                     (CaselessKeyword('network') +
                                                           Optional(Suppress(CaselessKeyword('as')) + (CaselessKeyword('dictionary') |
                                                                          CaselessKeyword('list')).setResultsName('networkType'))
                                                           )
                                                     ).setResultsName('returnType')
                                               ) +
                                      Optional(CaselessKeyword('paths').setParseAction(lambda s, l, t: True).setResultsName('paths')) +
                                      returnComponents
                                ).setResultsName('return')
                        )
                ).setResultsName('navigation')

    #function reference
    funcRef = Group(ncName.setResultsName("functionName") + 
                    Suppress(lParen) + 
                    Group(Optional(delimitedList(blockExpr) +
                                   Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                   )).setResultsName("functionArgs") + 
                Suppress(rParen)).setResultsName("functionReference") 

    #variable reference
    varRef = Group(Suppress(varIndicator) + simpleName.setResultsName("varName")).setResultsName("varRef") # variable reference

    #if expression
    elseIfExpr = (ZeroOrMore(Group(Suppress(elseOp + ifOp) + 
                                    
                                    blockExpr.setResultsName("condition") +
                                    
                                    blockExpr.setResultsName("thenExpr")
                                    )
                              ).setResultsName("elseIfExprs")
                   )

    ifExpr = (Group(Suppress(ifOp) + 
                   
                   blockExpr.setResultsName("condition") + 
                   
                   blockExpr.setResultsName("thenExpr") +
                   # this will flatten nested if conditions 
                   elseIfExpr +
                   Suppress(elseOp) + 
                   blockExpr.setResultsName("elseExpr")).setResultsName("ifExpr")
              ) 
              
    forExpr = (#with parens around the for control
               (Group(Suppress(forOp) + 
                Suppress(lParen) + 
                Group(
                      Combine(Suppress(varIndicator) + ncName.setResultsName("forVar")) + 
                      Optional(tagOp) +
                      Suppress(inOp) + 
                      blockExpr.setResultsName("forLoopExpr")
                      #blockExpr.setResultsName('forLoopExpr') 
                      ).setResultsName("forControl") +
                Suppress(rParen) +
                blockExpr.setResultsName("forBodyExpr")).setResultsName("forExpr")) |
               #without parens around the for control
                (Group(Suppress(forOp) + 
                Group(
                      Combine(Suppress(varIndicator) + ncName.setResultsName("forVar")) + 
                      Optional(tagOp) +
                      Suppress(inOp) + 
                      blockExpr.setResultsName("forLoopExpr")
                      #blockExpr.setResultsName('forLoopExpr') 
                      ).setResultsName("forControl") +
                blockExpr.setResultsName("forBodyExpr")).setResultsName("forExpr"))
               )
    
    listLiteral = Group(Empty().setParseAction(lambda s, l, t: "list").setResultsName("functionName") +
                        Suppress(lParen) + 
                        Group(Optional(delimitedList(blockExpr) +
                                       Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                       )).setResultsName("functionArgs") + 
                        Suppress(rParen)
                       ).setResultsName("functionReference")    
    
    atom = (
            ifExpr |
            forExpr |
            #literals
            floatLiteral |
            integerLiteral |
            stringLiteral |
            booleanLiteral |
            severityLiteral |
            noneLiteral |
            
            factset |
            navigation |
            
            funcRef | 
            varRef|
            
            qName |
            
            # parenthesized expression
            (Suppress(lParen) + blockExpr + Suppress(rParen)) |
            #list literal - needs to be at the end.
            listLiteral
            )

    #expressions with precedence.
    taggedExpr = Group(Group(atom).setResultsName('expr') +
                       tagOp + tagName).setResultsName('taggedExpr') | atom
       
    unaryExpr = Group((unaryOp.setResultsName('unaryOp') + ~digits + ~CaselessLiteral('INF') + Group(taggedExpr).setResultsName('expr'))).setResultsName('unaryExpr') | taggedExpr
   
    propertyExpr = Group(Group(unaryExpr).setResultsName('expr') +
                         properties).setResultsName('propertyExpr') | unaryExpr

    expr << buildPrecedenceExpressions(Group(propertyExpr),
                          [(multiOp, 2, opAssoc.LEFT, None, 'multiExpr'),
                           (addOp, 2, opAssoc.LEFT, None, 'addExpr'),
                           (compOp, 2, opAssoc.LEFT, None, 'compExpr'),
                           (notOp, 1, opAssoc.RIGHT, None, 'notExpr'),
                           (andOp, 2, opAssoc.LEFT, None, 'andExpr'),
                           (orOp, 2, opAssoc.LEFT, None, 'orExpr')
                          ])

    varDeclaration = Group(
                           Suppress(varIndicator) +
                           simpleName.setResultsName('varName') +   
                           Optional(tagOp +
                                    Optional(tagName)) + 
                           Suppress('=') +
                           blockExpr.setResultsName('expr') + Optional(Suppress(';'))
                           ).setResultsName('varDeclaration')

    blockExpr << (Group(Group(OneOrMore(Group(varDeclaration)).setResultsName('varDeclaraions') + 
                        expr.setResultsName('expr')).setResultsName('blockExpr')) | expr)
    
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

    namespaceDeclaration = Group(
                                 Suppress(namespaceKeyword) +
                                 Optional(
                                          ncName +
                                          Suppress(Literal('='))
                                          ,default='*').setResultsName('prefix') +
                                 nsURI.setResultsName('namespaceURI')
                                 ).setResultsName('nsDeclaration')

    outputAttributeDeclaration = Group(
                                       Suppress(outputAttributeKeyword) +
                                       simpleName.setResultsName('attributeName')).setResultsName('outputAttributeDeclaration')

    ruleResult = Group( ~declarationKeywords +
                         (oneOf('message severity') | simpleName).setResultsName('resultName') +
                         Group(expr).setResultsName('resultExpr')
                    )

    assertDeclaration = Group(
                              Suppress(assertKeyword) +
                              ncName.setResultsName('ruleName') +
                              Optional(CaselessKeyword('satisfied') | CaselessKeyword('unsatisfied'), default='satisfied').setResultsName('satisfactionType') +
                              blockExpr.setResultsName('body') +
                              ZeroOrMore(ruleResult).setResultsName('results')
                              ).setResultsName('assertion')

    outputDeclaration = Group(
                              Suppress(outputKeyword) +
                              ncName.setResultsName('ruleName') +
                              blockExpr.setResultsName('boyd') +
                              ZeroOrMore(ruleResult).setResultsName('results')
                              ).setResultsName('outputRule')

    constantDeclaration = Group(
                  Suppress(constantKeyword) +
                  ncName.setResultsName("constantName") + 
                  Optional(tagOp +
                           Optional(tagName)) + 
                  Suppress(assignOp) + 
                  Group(expr).setResultsName("body") 
            ).setResultsName("constantDeclaration")                              

    functionDeclaration = Group(
        Suppress(functionKeyword) + 
        ncName.setResultsName("functionName") + 
        Suppress(lParen) + 
        Group(Optional(delimitedList(Group(ncName.setResultsName('argName') + 
                                           Optional(tagOp +
                                                    Optional(tagName)))) +
                       Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
        )).setResultsName("functionArgs") + 
        Suppress(rParen) +
        Group(blockExpr).setResultsName("body")
        ).setResultsName("functionDeclaration")
                              
#     xuleFile = Group(
#                      stringStart +
#                      ZeroOrMore(Group(namespaceDeclaration) |
#                                 
#                                 Group(assertDeclaration) |
#                                       outputDeclaration |
#                                       functionDeclaration |
#                                       constantDeclaration)
#                                 +
#                      stringEnd
#                      ).setResultsName('xuleDoc')
                     
    xuleFile = (stringStart +
                ZeroOrMore(Group(namespaceDeclaration |
                                 outputAttributeDeclaration |
                                 functionDeclaration |
                                 constantDeclaration |
                                 assertDeclaration |
                                 outputDeclaration)) +
                stringEnd).setResultsName('xuleDoc')
    #xuleFile = Group(ZeroOrMore(factset)).setResultsName('xuleDoc')
    
    #xuleFile = (stringStart + Optional(header) + ZeroOrMore(packageBody) + stringEnd).setResultsName("xule").ignore(comment)
    
    return xuleFile
