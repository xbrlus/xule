"""Xule Grammar

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2021 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23604 $
DOCSKIP
"""
from pyparsing import (Word, CaselessKeyword,
                 Literal, CaselessLiteral, FollowedBy, OpAssoc,
                 Combine, Opt, nums, Forward, Group, ZeroOrMore,  
                 ParserElement, delimited_list, Suppress, Regex, 
                 OneOrMore, one_of, c_style_comment, CharsNotIn,
                 line_end, White, SkipTo, Empty, string_start, string_end, printables)

INRESULT = False

def in_result():
    global INRESULT
    INRESULT = True

def out_result(*args):
    global INRESULT
    INRESULT = False

def buildPrecedenceExpressions( baseExpr, opList, lpar=Suppress('('), rpar=Suppress(')')):
    """Simplified and modified version of pyparsing infix_notation helper function
    
    Args:
        baseExpr: The parser that is the operand of the operations
        opList: The list of operators that can be applied to the operand. This is a list in order of operator
            precedence. Highest precedence is first. Each item in the list is a tuple of:
                1 - operator expression: parser that is the operator
                2 - arity: the number of operands. only 1 and 2 are supported
                3 - associativeness: pyparsing.OpAssoc.LEFT or pyparsing.OpAssoc.RIGHT. Only left is supported for
                                        arity of 2 and right for arity of 1.
                4 - parserAction: parser action for the operation parser that is created.
        lpar: Parenthesized expressions are not supported in this version. This is ignored.
        rpar: Parenthesized expressions are not supported in this version. This is ignored.
        
    Returns:
        This returns a pyparsing parser.
    
    This version only handles binary and unary operations that are left associative. It also does not handle parenthesized
    expressions. It uses the same parameters as the infix_notation. This makes it easy to switch between this 
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
            raise ValueError('This is a modified version of the pyparsing infix_notation helper function. Only arity of 1 or 2 is supported.')
        if arity == 1 and rightLeftAssoc != OpAssoc.RIGHT:
            raise ValueError('This is a modified version of the pyparsing infix_notation helper function. When arity is 1 only right associative operations are supported.')
        if arity == 2 and rightLeftAssoc != OpAssoc.LEFT:
            raise ValueError('This is a modified version of the pyparsing infix_notation helper function. When arity is 2 only left associative operations are supported.')

        if opExpr is None:
            raise ValueError('This is a modified version of the pyparsing infix_notation helper function. opExpr must be supplied.')
        termName = "%s term" % opExpr if arity < 3 else "%s%s term" % opExpr
        thisExpr = Forward().set_name(termName)
        
        if arity == 1:
#             # try to avoid LR with this extra test
#             if not isinstance(opExpr, Optional):
#                 opExpr = Opt(opExpr)
            #original - matchExpr = FollowedBy(opExpr.expr + thisExpr) + Group( opExpr + thisExpr )
            if exprName is None:
                exprName = 'unaryExpr'
            matchExpr = (FollowedBy(opExpr + lastExpr) + \
                        ( (opExpr.set_results_name('op') + ~Word(nums)).leave_whitespace() + lastExpr.set_results_name('expr') ) + nodeName(exprName))
                        #Group(OneOrMore(Group(opExpr.set_results_name('op') + nodeName('opExpr')))).set_results_name('ops') + lastExpr.set_results_name('expr') + nodeName(exprName) )

                            
        else: #arity == 2
            #original -matchExpr = FollowedBy(lastExpr + opExpr + lastExpr) + ( lastExpr + OneOrMore( opExpr + lastExpr ) )
            if exprName is None:
                exprName = 'binaryExpr'
            matchExpr = (FollowedBy(lastExpr + opExpr + lastExpr) + \
                      ( lastExpr.set_results_name('leftExpr') + 
                        Group(OneOrMore(Group( opExpr.set_results_name('op') + 
                                   lastExpr.set_results_name('rightExpr') +
                                   nodeName('rightOperation')))).set_results_name('rights') ) +
                              nodeName(exprName)
                         )
            
        if pa:
            if isinstance(pa, (tuple, list)):
                matchExpr.set_parse_action(*pa)
            else:
                matchExpr.set_parse_action(pa)
        thisExpr <<= (Group(matchExpr.set_name(termName)) | lastExpr )
        lastExpr = thisExpr
    ret <<= lastExpr
    return ret

def nodeName(name):
    return Empty().set_parse_action(lambda: name).set_results_name('exprName')

def get_grammar():
    """Return the XULE grammar"""
    global INRESULT
    
    ParserElement.enable_packrat()
    
    #comment = c_style_comment() | (Literal("//") + SkipTo(line_end()))
    comment = c_style_comment | (Literal("//") + SkipTo(line_end))
    
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
    namespaceGroupKeyword = CaselessKeyword('namespace-group')
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
    coveredAspectStart = Literal('@').set_parse_action(lambda s, l, t: 'covered')
    uncoveredAspectStart = Literal('@@').set_parse_action(lambda s, l, t: 'uncovered')
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
    unaryOp = one_of('+ -') #+ ~one_of(nums)
    multiOp = one_of('* /')
    addOp = one_of('+> -> + - <+> <+ <-> <-')
    symDiffOp = Literal('^')
    intersectOp = Literal('&') | CaselessKeyword('intersect')
    notOp = CaselessKeyword('not')
    andOp = CaselessKeyword('and')
    orOp = CaselessKeyword('or')
    notInOp = Combine(notOp + White().set_parse_action(lambda: ' ') + inOp)
    compOp = one_of('== != <= < >= >') | inOp | notInOp
    
    #numeric literals
    sign = one_of("+ -")
    sciNot = Literal("e")
    decimalPoint = CaselessLiteral(".")
    digits = Word(nums)
    integerPart = Combine(Opt(sign) + digits)
    integerLiteral = Group(integerPart.set_results_name("value") +
                      nodeName('integer'))
    infLiteral = Combine(Opt(sign) + CaselessKeyword("INF"))
    floatLiteral = Group((Combine(decimalPoint + digits + Opt(sciNot + integerPart)) |
                     Combine(integerPart + decimalPoint + 
                             ~CharsNotIn('0123456789') + ~(sciNot + ~integerPart) # This prevents matching a property of a literal number
                             + Opt(digits, default='0') + Opt(sciNot + integerPart)) |
                     infLiteral).set_results_name("value") +
                    nodeName('float'))
    #string literals
#     stringLiteral = Group(((QuotedString("'", multiline=True, unquoteResults=False, escChar="\\").set_parse_action(remove_quotes)  | 
#                       QuotedString('"', multiline=True, unquoteResults=False, escChar="\\").set_parse_action(remove_quotes)).set_results_name("value")) +
#                      nodeName('string'))
    
    stringEscape = Group(Suppress(Literal('\\')) + Regex('.').set_results_name('value') + nodeName('escape'))
    stringExpr = Suppress(Literal('{')) + blockExpr + Suppress(Literal('}'))
    singleQuoteString = Suppress(Literal("'")) + ZeroOrMore(stringEscape | stringExpr | Group(Combine(OneOrMore(Regex("[^\\\\'{]"))).set_results_name('value') + nodeName('baseString'))) + Suppress(Literal("'"))
    doubleQuoteString = Suppress(Literal('"')) + ZeroOrMore(stringEscape | stringExpr | Group(Combine(OneOrMore(Regex('[^\\\\"{]'))).set_results_name('value') + nodeName('baseString'))) + Suppress(Literal('"'))
    stringLiteral = Group((Suppress(Opt(White())) + Group(singleQuoteString | doubleQuoteString).set_results_name('stringList') + Suppress(Opt(White())) + nodeName('string'))).leave_whitespace()

    #boolean literals
    booleanLiteral = Group((CaselessKeyword("true") | CaselessKeyword("false")).set_results_name("value") + nodeName('boolean'))
    
    #none literal
    noneLiteral = Group(CaselessKeyword("none").set_results_name('value') + nodeName('none'))
    skipLiteral = Group(CaselessKeyword("skip").set_results_name('value') + nodeName('none'))
    
    #severity literals  
    errorLiteral = CaselessKeyword("error")
    warningLiteral = CaselessKeyword("warning")
    okLiteral = CaselessKeyword("ok")
    passLiteral = CaselessKeyword("pass")
    severityLiteral = Group((errorLiteral | warningLiteral | okLiteral | passLiteral).set_results_name('value') + nodeName('severity'))
    
    #balance literals
    balanceLiteral = Group((CaselessKeyword('debit') | CaselessKeyword('credit')).set_results_name('value') + nodeName('balance'))
    periodTypeLiteral = Group((CaselessKeyword('instant') | CaselessKeyword('duration')).set_results_name('value') + nodeName('periodType'))


    #forever literal
    foreverLiteral = Group(Suppress(CaselessKeyword('forever')) + Empty().set_parse_action(lambda s, l, t: True).set_results_name('forever') + nodeName('period'))

    #direction keywords
    directionLiteral = ((CaselessKeyword('ancestors').set_results_name('direction') + Opt(digits, -1).set_results_name('depth')) |  
                        (CaselessKeyword('descendants').set_results_name('direction')  + Opt(digits, -1).set_results_name('depth')) | 
                        CaselessKeyword('parents').set_results_name('direction') |
                        CaselessKeyword('children').set_results_name('direction') |
                        CaselessKeyword('siblings').set_results_name('direction') | 
                        CaselessKeyword('previous-siblings').set_results_name('direction') | 
                        CaselessKeyword('following-siblings').set_results_name('direction') | 
                        CaselessKeyword('self').set_results_name('direction'))
    
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
                  ).set_parse_action(lambda s, l, t: [t[0].replace('\\','')]) #parse action removes the escape backslash character
    prefix = qNameLocalName

    qName = Group(Opt(Combine(prefix + ~White() + Suppress(qNameOp)), default="*").set_results_name("prefix") + 
                  ~White() 
                  + qNameLocalName.set_results_name("localName")
                  + nodeName('qname'))

    tagOp = Literal('#').set_parse_action(lambda: True).set_results_name('tagged')
    tagName = simpleName.set_results_name('tagName')

    covered = CaselessKeyword('covered').set_parse_action(lambda: True).set_results_name('covered')
    coveredDims = CaselessKeyword('covered-dims').set_parse_action(lambda: True).set_results_name('coveredDims')
    includeNils = CaselessKeyword('nils').set_parse_action(lambda: True).set_results_name('includeNils')
    excludeNils = CaselessKeyword('nonils').set_parse_action(lambda: True).set_results_name('excludeNils')
    nilDefault = CaselessKeyword('nildefault').set_parse_action(lambda: True).set_results_name('nilDefault')
    where = CaselessKeyword('where')
    returns = CaselessKeyword('returns')

    #variable reference
    varRef = Group(Suppress(varIndicator) + simpleName.set_results_name('varName') + Empty().set_parse_action(lambda: 'tagRef' if INRESULT else 'varRef').set_results_name('exprName'))

    properties = Group(OneOrMore(Group(Suppress(propertyOp) +
                                       simpleName.set_results_name('propertyName') +
                                       Opt(Group(Suppress(lParen) +
                                                Opt(delimited_list(blockExpr)) +
                                                Suppress(rParen)
                                                ).set_results_name('propertyArgs')
                                                
                                                ) +
                                       Opt(tagOp + tagName)
                                       + nodeName('property')
                                 ))
                       ).set_results_name('properties')


    whereClause = Suppress(where) + blockExpr.set_results_name('whereExpr')
    returnsClause = Suppress(returns) + blockExpr.set_results_name('returnsExpr')

    # Note the order of uncovered and covered is important. The uncovered must go first because it is a @@
    # while the coveted is a single @. If the order is flipped, the parser will think a @@ is two consecute
    # single @s instead of a single double @.
    aspectStart = (uncoveredAspectStart | coveredAspectStart).set_results_name('coverType') + ~coveredAspectStart + ~White()
    
    aspectNameLiteral = Group((CaselessKeyword('concept').set_results_name('value') | 
                               CaselessKeyword('unit').set_results_name('value') | 
                               CaselessKeyword('entity').set_results_name('value') | 
                               CaselessKeyword('period').set_results_name('value') | 
                               CaselessKeyword('instance').set_results_name('value') |
                               CaselessKeyword('cube').set_results_name('value')) + nodeName('aspectName')
                              )
    
    aspectName = ((aspectNameLiteral.set_results_name('aspectName') +
                    Opt(
                             #properties.set_results_name('aspectProperties'))
                         Suppress(propertyOp) +
                         ncName.set_results_name('propertyName') +
                         Opt(Group(Suppress(lParen) +
                                        Opt(delimited_list(blockExpr)) +
                                        Suppress(rParen)
                                        ).set_results_name('propertyArgs')
                         )                        
                     )
                   )| 
                   qName.set_results_name('aspectName') | 
                   varRef.set_results_name('aspectName')
                  )
    
    aspectOp = assignOp | Literal('!=') | inOp | notInOp
    
    aspectFilter = (aspectStart + 
                    aspectName +
                             Opt(aspectOp.set_results_name('aspectOperator') + 
                                      (Literal('*').set_results_name('wildcard') |
                                       blockExpr.set_results_name('aspectExpr')
                                      )
                                      ) +
                             Opt(Suppress(asOp) + Suppress(varIndicator) + ~White()+ simpleName.set_results_name('alias'))
                             
                    + nodeName('aspectFilter'))
    
    factsetInner =  ((Opt(excludeNils | includeNils) &
                    Opt(coveredDims) +
                    Opt(covered)) + 
#                   (ZeroOrMore(Group(aspectFilter)).set_results_name('aspectFilters') ) +
                    Opt((Suppress(Literal('@')) ^ OneOrMore(Group(aspectFilter)).set_results_name('aspectFilters'))) +
#                     Opt((whereClause) | blockExpr.set_results_name('innerExpr')
                    Opt(~ where + blockExpr.set_results_name('innerExpr') ) +
                    Opt(whereClause)
                    )
                    
    
    factset = Group(
                (       
                     (
                      Suppress(lCurly) + 
                      factsetInner +                    
                      Suppress(rCurly) +
                      Empty().set_parse_action(lambda s, l, t: 'open').set_results_name('factsetType')
                      ) |
                     (
                      Suppress(lSquare) + 
                      factsetInner +                    
                      Suppress(rSquare) +
                      Empty().set_parse_action(lambda s, l, t: 'closed').set_results_name('factsetType')
                      ) |
                      (Opt(excludeNils | includeNils) +
                      Opt(nilDefault) +
                      Opt(covered) +
                      (Suppress(Literal('@')) ^ OneOrMore(Group(aspectFilter)).set_results_name('aspectFilters')) + #This is a factset without enclosing brackets
                      Empty().set_parse_action(lambda s, l, t: 'open').set_results_name('factsetType') +
                      Opt(whereClause))
                ) +
                nodeName('factset')        
            )
    
    returnComponents = (Group(simpleName).set_results_name('returnComponents') |
                        (Suppress('(') +
                         Group(delimited_list(simpleName + ~Literal(':') | blockExpr)).set_results_name('returnComponents') +
                         Suppress(')'))
                        )
    
    navigation = Group(
                       Suppress(CaselessKeyword('navigate')) + 
                       # The dimension and arcrole need the FollowedBy() look ahead. I'm not sure why, but it is because these are optional and the direction is reuired.
                       # Without the FollowedBy() look ahead, 'navigate self' fails because the parser thinks 'navigate' is a qname and then does not know what to 
                       # do with 'self'.
                       Opt(CaselessKeyword('dimensions').set_parse_action(lambda: True).set_results_name('dimensional') + (FollowedBy(blockExpr | directionLiteral) )) +
                       Opt(blockExpr.set_results_name('arcrole') + FollowedBy(directionLiteral)) +  
                       directionLiteral +
                       Opt(Group(CaselessKeyword('include') + CaselessKeyword('start')).set_parse_action(lambda: True).set_results_name('includeStart')) +
                       Opt(Suppress(CaselessKeyword('from')) + blockExpr.set_results_name('from')) +
                       Opt(Suppress(CaselessKeyword('to')) + blockExpr.set_results_name('to')) +
                       Opt(Suppress(Group(CaselessKeyword('stop') + CaselessKeyword('when'))) + blockExpr.set_results_name('stopExpr')) +
                       Opt(Suppress(CaselessKeyword('role')) + blockExpr.set_results_name('role')) +
                       Opt(Suppress(CaselessKeyword('drs-role')) + blockExpr.set_results_name('drsRole')) +
                       Opt(Suppress(CaselessKeyword('linkbase')) + blockExpr.set_results_name('linkbase')) +
                       Opt(Suppress(CaselessKeyword('cube')) + blockExpr.set_results_name('cube')) +
                       Opt(Suppress(CaselessKeyword('taxonomy')) + blockExpr.set_results_name('taxonomy')) +
                       Opt(whereClause) +
                       Opt(Group(
                                      Suppress(CaselessKeyword('returns')) +
                                      Opt(Group(CaselessKeyword('by') + CaselessKeyword('network')).set_parse_action(lambda: True).set_results_name('byNetwork')) +                                    
                                      Opt(
                                             CaselessKeyword('list') |
                                             CaselessKeyword('set') 
                                             ).set_results_name('returnType') +
                                      Opt(CaselessKeyword('paths').set_parse_action(lambda: True).set_results_name('paths')) +
                                      Opt(returnComponents +
                                               Opt(Suppress(CaselessKeyword('as')) + CaselessKeyword('dictionary').set_results_name('returnComponentType'))) +
                                      nodeName('returnExpr')
                                ).set_results_name('return')
                        ) +
                       nodeName('navigation')
                )
    
    filter = Group(
                   Suppress(CaselessKeyword('filter')) +
                   blockExpr.set_results_name('expr') + 
                   Opt(whereClause) +
                   Opt(returnsClause) +
                   nodeName('filter')
                   )
    #function reference
    funcRef = Group(simpleName.set_results_name("functionName") + ~White() +
                    Suppress(lParen) + 
                    Group(Opt(delimited_list(blockExpr)  +
                                   Opt(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                   )).set_results_name("functionArgs") + 
                Suppress(rParen) +
                nodeName('functionReference')) 

    #if expression
    elseIfExpr = (OneOrMore(Group(Suppress(elseOp + ifOp) + 
                                    blockExpr.set_results_name("condition") +
                                    blockExpr.set_results_name("thenExpr") +
                                    nodeName('elseIf')
                                    )
                              ).set_results_name("elseIfExprs")
                   )

    ifExpr = Group(Suppress(ifOp) + 
                   
                   blockExpr.set_results_name("condition") + 
                   
                   blockExpr.set_results_name("thenExpr") +
                   # this will flatten nested if conditions 
                   Opt(elseIfExpr) +
                   Suppress(elseOp) + 
                   blockExpr.set_results_name("elseExpr") +
                   nodeName('ifExpr')
              ) 
              
    forExpr = Group(#with parens around the for control
               ((Suppress(forOp) + 
                #for loop control: for var name and loop expression
                Suppress(lParen) + 
                Combine(Suppress(varIndicator) + ~White() + simpleName.set_results_name("forVar")) + 
                Suppress(inOp) + 
                blockExpr.set_results_name("forLoopExpr") +
                Suppress(rParen) +
                #for body expression
                blockExpr.set_results_name("forBodyExpr") + 
                nodeName('forExpr'))) |
               
               #without parens around the for control
               ((Suppress(forOp) + 
                #for loop control
                Combine(Suppress(varIndicator) + ~White() + simpleName.set_results_name("forVar")) + 
                Suppress(inOp) + 
                blockExpr.set_results_name("forLoopExpr") +
                #for body expression
                blockExpr.set_results_name("forBodyExpr") + 
                nodeName('forExpr')))
               )
    
    listLiteral =  Group( 
                        Suppress(lParen) +
                        Group(Opt(delimited_list(blockExpr) +
                                       Opt(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                       )).set_results_name("functionArgs") + 
                        Suppress(rParen) +
                        nodeName('functionReference') +
                       
                       Empty().set_parse_action(lambda s, l, t: "list").set_results_name("functionName")
                       )
    
    #dictExpr = Group(Suppress(CaselessKeyword('dict')) +
    #                 Group(delimited_list(Group(blockExpr.set_results_name('key') + Literal('=') + blockExpr.set_results_name('value') + nodeName('item')))).set_results_name('items') +
    #                 nodeName('dictExpr'))
    #
    #listExpr = Group(Suppress(CaselessKeyword('list')) +
    #                 Group(delimited_list(blockExpr)).set_results_name('items') +
    #                 nodeName('listExpr'))
    #
    #setExpr = Group(Suppress(CaselessKeyword('set')) +
    #                Group(delimited_list(blockExpr)).set_results_name('items') +
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
    
    taggedExpr = Group(atom.set_results_name('expr') + Suppress('#') + tagName + nodeName('taggedExpr')) | atom
        
#     unaryExpr = Group(unaryOp.set_results_name('op') + 
#                        #~digits + ~CaselessLiteral('INF') + 
#                        Group(taggedExpr).set_results_name('expr') +
#                       nodeName('unaryExpr')) | taggedExpr
                       
    indexExpr = Group(taggedExpr.set_results_name('expr') +
                      OneOrMore((Suppress(lSquare) + blockExpr + 
                                      Suppress(rSquare) )).set_results_name('indexes') +
                      nodeName('indexExpr')) | taggedExpr
    
    propertyExpr = Group(indexExpr.set_results_name('expr') +
                         properties +
                         nodeName('propertyExpr')) | indexExpr
     
    expr << buildPrecedenceExpressions(propertyExpr,
                          [(unaryOp, 1, OpAssoc.RIGHT, None, 'unaryExpr'),
                           (multiOp, 2, OpAssoc.LEFT, None, 'multExpr'),
                           (addOp, 2, OpAssoc.LEFT, None, 'addExpr'),
                           (intersectOp, 2, OpAssoc.LEFT, None, 'intersectExpr'),
                           (symDiffOp, 2, OpAssoc.LEFT, None, 'symetricDifferenceExpr'),
                           (compOp, 2, OpAssoc.LEFT, None, 'compExpr'),
                           (notOp, 1, OpAssoc.RIGHT, None, 'notExpr'),
                           (andOp, 2, OpAssoc.LEFT, None, 'andExpr'),
                           (orOp, 2, OpAssoc.LEFT, None, 'orExpr')
                          ])

    varDeclaration = (
                           Suppress(varIndicator) + ~White() +
                           simpleName.set_results_name('varName') +   
                           Opt(tagOp +
                                    Opt(tagName)) + 
                           Suppress('=') +
                           blockExpr.set_results_name('body') + Opt(Suppress(';')) +
                           nodeName('varDeclaration')
                           )

    blockExpr << (Group((OneOrMore(Group(varDeclaration)).set_results_name('varDeclarations') + 
                        expr.set_results_name('expr') +
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
                                   prefix.set_results_name('prefix') +
                                   Suppress(Literal('='))
                                   ) |
                                  Empty().set_parse_action(lambda s, l, tok: '*').set_results_name('prefix')
                                  ) +
                                 nsURI.set_results_name('namespaceURI') +
                                 nodeName('nsDeclaration')
                                 )

#     outputAttributeDeclaration = Group(
#                                        Suppress(outputAttributeKeyword) +
#                                        simpleName.set_results_name('attributeName')).set_results_name('outputAttributeDeclaration')

    outputAttributeDeclaration = (
                                   Suppress(outputAttributeKeyword) +
                                   simpleName.set_results_name('attributeName') +
                                   nodeName('outputAttributeDeclaration')
                                 )
    
    ruleNamePrefix = (
                      Suppress(ruleNamePrefixKeyword) +
                      ncName.set_results_name('prefix') +
                      nodeName('ruleNamePrefix')
                      )
    
    ruleNameSeparator = (
                         Suppress(ruleNameSeparatorKeyword) +
                         Word(printables).set_results_name('separator') +
                         nodeName('ruleNameSeparator')
                         )
    
    ruleResult = Group( ~declarationKeywords +
                         (CaselessKeyword('message') | CaselessKeyword('severity') | CaselessKeyword('rule-suffix') | CaselessKeyword('rule-focus') | simpleName).set_results_name('resultName') + Empty().set_parse_action(in_result) +
                         expr.set_results_name('resultExpr').set_parse_action(out_result).set_fail_action(out_result) + nodeName('result')
                    )

    assertDeclaration = (
                              Suppress(assertKeyword) +
                              ncName.set_results_name('ruleName') +
                              Opt(CaselessKeyword('satisfied') | CaselessKeyword('unsatisfied'), default='satisfied').set_results_name('satisfactionType') +
                              blockExpr.set_results_name('body') +
                              ZeroOrMore(ruleResult).set_results_name('results') +
                              nodeName('assertion')
                              )

    outputDeclaration = (
                              Suppress(outputKeyword) +
                              ncName.set_results_name('ruleName') +
                              blockExpr.set_results_name('body') +
                              ZeroOrMore(ruleResult).set_results_name('results') +
                              nodeName('outputRule')
                              )

    constantDeclaration = (
                  Suppress(constantKeyword) +
                  Suppress(varIndicator) + ~ White() +
                  simpleName.set_results_name("constantName") + 
                  Opt(tagOp +
                           Opt(tagName)) + 
                  Suppress(assignOp) + 
                  expr.set_results_name("body") +
                  nodeName('constantDeclaration')
            )                            

    namespaceGroupDeclaration = (
                  Suppress(namespaceGroupKeyword) +
                  simpleName.set_results_name("namespaceGroupName") + 
                  Suppress(assignOp) + 
                  expr.set_results_name("body") +
                  nodeName('namespaceGroupDeclaration')
            )  

    functionDeclaration = (
        Suppress(functionKeyword) + 
        simpleName.set_results_name("functionName") + ~White() +
        Suppress(lParen) + 
        Group(Opt(delimited_list(Group(Suppress(varIndicator) + ~White() + simpleName.set_results_name('argName') + nodeName('functionArg') + 
                                           Opt(tagOp +
                                                    Opt(tagName)))) +
                       Opt(Suppress(commaOp)) #This allows a trailing comma for lists and sets
        )).set_results_name("functionArgs") + 
        Suppress(rParen) +
        blockExpr.set_results_name("body") +
        nodeName('functionDeclaration')
        )

    versionDeclaration = (
            Suppress(versionKeyword) + Word(printables).set_results_name('version') + nodeName('versionDeclaration')
    )

    xuleFile = (string_start +
                ZeroOrMore(Group(ruleNameSeparator |
                                 ruleNamePrefix |
                                 namespaceGroupDeclaration | 
                                 namespaceDeclaration |
                                 outputAttributeDeclaration |
                                 functionDeclaration |
                                 constantDeclaration |
                                 versionDeclaration |
                                 assertDeclaration |
                                 outputDeclaration)) +
                string_end).set_results_name('xuleDoc').ignore(comment)
    #xuleFile = Group(ZeroOrMore(factset)).set_results_name('xuleDoc')
    
    #xuleFile = (string_start + Opt(header) + ZeroOrMore(packageBody) + string_end).set_results_name("xule").ignore(comment)
    
    return xuleFile
