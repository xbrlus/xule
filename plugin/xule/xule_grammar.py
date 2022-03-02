"""Xule Grammar

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2022 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23204 $
DOCSKIP
"""
from pyparsing import (Word, Keyword,  CaselessKeyword, ParseResults, infixNotation,
                 Literal, CaselessLiteral, FollowedBy, opAssoc,
                 Combine, Optional, nums, Forward, Group, ZeroOrMore,  
                 ParserElement,  delimitedList, Suppress, Regex, 
                 QuotedString, OneOrMore, oneOf, cStyleComment, CharsNotIn,
                 lineEnd, White, SkipTo, Empty, stringStart, stringEnd, alphas, printables, removeQuotes)

INRESULT = False

def in_result():
    global INRESULT
    INRESULT = True

def out_result(*args):
    global INRESULT
    INRESULT = False

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
                        ( (opExpr.setResultsName('op') + ~Word(nums)).leaveWhitespace() + lastExpr.setResultsName('expr') ) + nodeName(exprName))
                        #Group(OneOrMore(Group(opExpr.setResultsName('op') + nodeName('opExpr')))).setResultsName('ops') + lastExpr.setResultsName('expr') + nodeName(exprName) )

                            
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
    global INRESULT
    
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
    versionKeyword = CaselessKeyword('version')

    declarationKeywords = (assertKeyword | outputKeyword | outputAttributeKeyword | namespaceKeyword | constantKeyword | functionKeyword | versionKeyword | ruleNamePrefixKeyword | ruleNameSeparatorKeyword)

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
    unaryOp = oneOf('+ -') #+ ~oneOf(nums)
    multiOp = oneOf('* /')
    addOp = oneOf('+> -> + - <+> <+ <-> <-')
    symDiffOp = Literal('^')
    intersectOp = Literal('&') | CaselessKeyword('intersect')
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
                     Combine(integerPart + decimalPoint + 
                             ~CharsNotIn('0123456789') + ~(sciNot + ~integerPart) # This prevents matching a property of a literal number
                             + Optional(digits, default='0') + Optional(sciNot + integerPart)) |
                     infLiteral).setResultsName("value") +
                    nodeName('float'))
    #string literals
#     stringLiteral = Group(((QuotedString("'", multiline=True, unquoteResults=False, escChar="\\").setParseAction(removeQuotes)  | 
#                       QuotedString('"', multiline=True, unquoteResults=False, escChar="\\").setParseAction(removeQuotes)).setResultsName("value")) +
#                      nodeName('string'))
    
    stringEscape = Group(Suppress(Literal('\\')) + Regex('.').setResultsName('value') + nodeName('escape'))
    stringExpr = Suppress(Literal('{')) + blockExpr + Suppress(Literal('}'))
    singleQuoteString = Suppress(Literal("'")) + ZeroOrMore(stringEscape | stringExpr | Group(Combine(OneOrMore(Regex("[^\\\\'{]"))).setResultsName('value') + nodeName('baseString'))) + Suppress(Literal("'"))
    doubleQuoteString = Suppress(Literal('"')) + ZeroOrMore(stringEscape | stringExpr | Group(Combine(OneOrMore(Regex('[^\\\\"{]'))).setResultsName('value') + nodeName('baseString'))) + Suppress(Literal('"'))
    stringLiteral = Group((Group(singleQuoteString | doubleQuoteString).setResultsName('stringList') + nodeName('string'))).leaveWhitespace()

    #boolean literals
    booleanLiteral = Group((CaselessKeyword("true") | CaselessKeyword("false")).setResultsName("value") + nodeName('boolean'))
    
    #none literal
    noneLiteral = Group(CaselessKeyword("none").setResultsName('value') + nodeName('none'))
    skipLiteral = Group(CaselessKeyword("skip").setResultsName('value') + nodeName('none'))
    
    #severity literals  
    errorLiteral = CaselessKeyword("error")
    warningLiteral = CaselessKeyword("warning")
    okLiteral = CaselessKeyword("ok")
    passLiteral = CaselessKeyword("pass")
    severityLiteral = Group((errorLiteral | warningLiteral | okLiteral | passLiteral).setResultsName('value') + nodeName('severity'))
    
    #balance literals
    balanceLiteral = Group((CaselessKeyword('debit') | CaselessKeyword('credit')).setResultsName('value') + nodeName('balance'))
    periodTypeLiteral = Group((CaselessKeyword('instant') | CaselessKeyword('duration')).setResultsName('value') + nodeName('periodType'))


    #forever literal
    foreverLiteral = Group(Suppress(CaselessKeyword('forever')) + Empty().setParseAction(lambda s, l, t: True).setResultsName('forever') + nodeName('period'))

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
    # A qNameLocalName normally allows a dot character as long it is not the first character. In Xule, the dot is used
    # to indicate a property. For qNameLocalName literals a dot character will have to be escaped by a backslash. Assets.
    # local-part is a qname with a property of local-part. Assets\.local-part is a qname of "Assets.local-part".
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
    coveredDims = CaselessKeyword('covered-dims').setParseAction(lambda: True).setResultsName('coveredDims')
    includeNils = CaselessKeyword('nils').setParseAction(lambda: True).setResultsName('includeNils')
    excludeNils = CaselessKeyword('nonils').setParseAction(lambda: True).setResultsName('excludeNils')
    nilDefault = CaselessKeyword('nildefault').setParseAction(lambda: True).setResultsName('nilDefault')
    where = CaselessKeyword('where')
    returns = CaselessKeyword('returns')

    #variable reference
    varRef = Group(Suppress(varIndicator) + simpleName.setResultsName('varName') + Empty().setParseAction(lambda: 'tagRef' if INRESULT else 'varRef').setResultsName('exprName'))

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
    
    aspectNameLiteral = Group((CaselessKeyword('concept').setResultsName('value') | 
                               CaselessKeyword('unit').setResultsName('value') | 
                               CaselessKeyword('entity').setResultsName('value') | 
                               CaselessKeyword('period').setResultsName('value') | 
                               CaselessKeyword('cube').setResultsName('value')) + nodeName('aspectName')
                              )
    
    aspectName = ((aspectNameLiteral.setResultsName('aspectName') +
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
                   )| 
                   qName.setResultsName('aspectName') | 
                   varRef.setResultsName('aspectName')
                  )
    
    aspectOp = assignOp | Literal('!=') | inOp | notInOp
    
    aspectFilter = (aspectStart + 
                    aspectName +
                             Optional(aspectOp.setResultsName('aspectOperator') + 
                                      (Literal('*').setResultsName('wildcard') |
                                       blockExpr.setResultsName('aspectExpr')
                                      )
                                      ) +
                             Optional(Suppress(asOp) + Suppress(varIndicator) + ~White()+ simpleName.setResultsName('alias'))
                             
                    + nodeName('aspectFilter'))
    
    factsetInner =  ((Optional(excludeNils | includeNils) &
                    Optional(coveredDims) +
                    Optional(covered)) + 
#                   (ZeroOrMore(Group(aspectFilter)).setResultsName('aspectFilters') ) +
                    Optional((Suppress(Literal('@')) ^ OneOrMore(Group(aspectFilter)).setResultsName('aspectFilters'))) +
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
                      (Optional(excludeNils | includeNils) +
                      Optional(nilDefault) +
                      Optional(covered) +
                      (Suppress(Literal('@')) ^ OneOrMore(Group(aspectFilter)).setResultsName('aspectFilters')) + #This is a factset without enclosing brackets
                      Empty().setParseAction(lambda s, l, t: 'open').setResultsName('factsetType') +
                      Optional(whereClause))
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
                       Optional(Suppress(Group(CaselessKeyword('stop') + CaselessKeyword('when'))) + blockExpr.setResultsName('stopExpr')) +
                       Optional(Suppress(CaselessKeyword('role')) + blockExpr.setResultsName('role')) +
                       Optional(Suppress(CaselessKeyword('drs-role')) + blockExpr.setResultsName('drsRole')) +
                       Optional(Suppress(CaselessKeyword('linkbase')) + blockExpr.setResultsName('linkbase')) +
                       Optional(Suppress(CaselessKeyword('cube')) + blockExpr.setResultsName('cube')) +
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
    
    #dictExpr = Group(Suppress(CaselessKeyword('dict')) +
    #                 Group(delimitedList(Group(blockExpr.setResultsName('key') + Literal('=') + blockExpr.setResultsName('value') + nodeName('item')))).setResultsName('items') +
    #                 nodeName('dictExpr'))
    #
    #listExpr = Group(Suppress(CaselessKeyword('list')) +
    #                 Group(delimitedList(blockExpr)).setResultsName('items') +
    #                 nodeName('listExpr'))
    #
    #setExpr = Group(Suppress(CaselessKeyword('set')) +
    #                Group(delimitedList(blockExpr)).setResultsName('items') +
    #                nodeName('setExpr'))
    
    atom = (
            #listLiteral |
            # parenthesized expression - This needs to be up front for performance. 
            (Suppress(lParen) + blockExpr + Suppress(rParen)) |            

            funcRef | 
            varRef|
            ifExpr |
            forExpr |
            navigation |
            filter |

            factset |

            #literals
            floatLiteral |
            integerLiteral |
            stringLiteral |
            booleanLiteral |
            severityLiteral |
            balanceLiteral |
            periodTypeLiteral |
            noneLiteral |
            skipLiteral |
            foreverLiteral |

            #aspectNameLiteral |
            
            #dictExpr |
            #listExpr |
            #setExpr |
            
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
                  
                  "\U00010000-\U0001FFFD"
                  "\U00020000-\U0002FFFD"
                  "\U00030000-\U0003FFFD"
                  "\U00040000-\U0004FFFD"
                  "\U00050000-\U0005FFFD"
                  "\U00060000-\U0006FFFD"
                  "\U00070000-\U0007FFFD"
                  "\U00080000-\U0008FFFD"
                  "\U00090000-\U0009FFFD"
                  "\U000A0000-\U000AFFFD"
                  "\U000B0000-\U000BFFFD"
                  "\U000C0000-\U000CFFFD"
                  "\U000D0000-\U000DFFFD"
                  "\U000E0000-\U000EFFFD"
                  "\U000F0000-\U000FFFFD"
                  "\U00100000-\U0010FFFD"
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
                         (CaselessKeyword('message') | CaselessKeyword('severity') | CaselessKeyword('rule-suffix') | CaselessKeyword('rule-focus') | simpleName).setResultsName('resultName') + Empty().setParseAction(in_result) +
                         expr.setResultsName('resultExpr').setParseAction(out_result).setFailAction(out_result) + nodeName('result')
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

    versionDeclaration = (
            Suppress(versionKeyword) + Word(printables).setResultsName('version') + nodeName('versionDeclaration')
    )

    xuleFile = (stringStart +
                ZeroOrMore(Group(ruleNameSeparator |
                                 ruleNamePrefix |
                                 namespaceDeclaration |
                                 outputAttributeDeclaration |
                                 functionDeclaration |
                                 constantDeclaration |
                                 versionDeclaration |
                                 assertDeclaration |
                                 outputDeclaration)) +
                stringEnd).setResultsName('xuleDoc').ignore(comment)
    #xuleFile = Group(ZeroOrMore(factset)).setResultsName('xuleDoc')
    
    #xuleFile = (stringStart + Optional(header) + ZeroOrMore(packageBody) + stringEnd).setResultsName("xule").ignore(comment)
    
    return xuleFile
