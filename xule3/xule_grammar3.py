'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21535 $
'''
def get_grammar():
    
    from pyparsing import (Word, Keyword,  CaselessKeyword,
                     Literal, CaselessLiteral, 
                     Combine, Optional, nums, Forward, Group, ZeroOrMore,  
                     ParserElement,  delimitedList, Suppress, Regex, 
                     QuotedString, OneOrMore, oneOf, cStyleComment,
                     lineEnd, White, SkipTo, Empty, stringStart, stringEnd)
    
    ParserElement.enablePackrat()
    
    #expression forwards
    expr = Forward()
    blockExpr = Forward()
    
    #operators
    unaryOp = oneOf("+ -")
    addOp = Group(oneOf("+| -| + - |+| |+ |-| |-").setResultsName("value")).setResultsName("op")
    multOp = Group(oneOf("* /").setResultsName("value")).setResultsName("op")
    andOp = Keyword("and")
    orOp = Keyword("or")
    notOp = Keyword("not")
    eqOp = Group(Literal("==").setResultsName("value")).setResultsName("op")
    neOp = Group(Literal("!=").setResultsName("value")).setResultsName("op")
    ltOp = Group(Literal("<").setResultsName("value")).setResultsName("op")
    leOp = Group(Literal("<=").setResultsName("value")).setResultsName("op")
    gtOp = Group(Literal(">").setResultsName("value")).setResultsName("op")
    geOp = Group(Literal(">=").setResultsName("value")).setResultsName("op")
    #order is importint in the compOP (comparison operators). The >= has to be befor the > otherwise the parser thinks both > and >= are just > and will fail with >=. 
    #The same is true for < and <=.
    compOp = eqOp | neOp | leOp | ltOp | geOp | gtOp  
    assignOp = Literal("=")
    assignEnd = Literal(";")
    tagOp = Literal("#")
    methodOp = Literal(".")
    commaOp = Literal(",")
    ifOp = Keyword("if")
    elseOp = Keyword("else")
    forOp = Keyword("for")
    withOp = Keyword("with")
    qNameOp = Literal(":")
    formulaOp = Literal(":=")
    annotationOp = Literal("@")
    inOp = Keyword("in")
    valuesOp = Keyword("values")
    
    lParen = Literal("(")
    rParen = Literal(")")
    
    #comment = cStyleComment() | (Literal("//") + SkipTo(lineEnd()))
    comment = cStyleComment | (Literal("//") + SkipTo(lineEnd))
    #Literals
    ncName = Regex("([A-Za-z\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD_]"
                  "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_.-]*)"
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
                  + ncName.setResultsName("localName")).setResultsName("qName")
    
    #numeric literals
    sign = oneOf("+ -")
    sciNot = Literal("e")
    decimalPoint = Literal(".")
    digits = Word(nums)
    integerLiteral = Group(Combine(Optional(sign) + digits).setResultsName("value")).setResultsName("integer")
    infLiteral = Combine(Optional(sign) + CaselessKeyword("INF"))
    floatLiteral = Group(( Combine(decimalPoint + digits + Optional (sciNot + integerLiteral)) |
                     Combine(integerLiteral + decimalPoint + digits + Optional (sciNot + integerLiteral)) |
                     Combine(integerLiteral + decimalPoint + Optional (sciNot + integerLiteral)) |
                     infLiteral).setResultsName("value")).setResultsName("float")
    #string literals
    stringLiteral = Group(( QuotedString("'", multiline=True, unquoteResults=False, escChar="\\")  | 
                      QuotedString('"', multiline=True, unquoteResults=False, escChar="\\") ).setResultsName("value")).setResultsName("string")
    
    #boolean literals
    boolLiteral = Group((Keyword("true") | Keyword("false")).setResultsName("value")).setResultsName("boolean")
    
    #void literals
    noneLiteral = Group((Keyword("none")).setResultsName("value")).setResultsName("void") 
    unboundLiteral = Group((Keyword("unbound")).setResultsName("value")).setResultsName("void") 
    voidLiteral = noneLiteral | unboundLiteral #Group((Keyword("none") | Keyword("unbound")).setResultsName("value")).setResultsName("void")
    
    #severity literals  

    errorLiteral = Keyword("error")
    warningLiteral = Keyword("warning")
    infoLiteral = Keyword("info")
    passLiteral = Keyword("pass")
    
    severityLiteral = Group((errorLiteral | warningLiteral | infoLiteral | passLiteral).setResultsName("severityName") + 
                            Group(Optional(Suppress(lParen) +
                                           Optional(delimitedList(Group(ncName.setResultsName("tagName") +
                                                                        Suppress("=") +
                                                                        Group(blockExpr).setResultsName("argExpr") 
                                                                        ).setResultsName("severityArg"))) +
                                           Suppress(rParen))).setResultsName("severityArgs")).setResultsName("severity")

    listLiteral = Group(Empty().setParseAction(lambda s, l, t: "list").setResultsName("functionName") +
                        Suppress(lParen) + 
                        Group(Optional(delimitedList(Group(blockExpr).setResultsName("functionArg")) +
                                   Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                   )).setResultsName("functionArgs") + 
                        Suppress(rParen)).setResultsName("functionReference")

    # references
    varRef = Group(Suppress(Literal("$")) + simpleName.setResultsName("varName")).setResultsName("varRef") # variable reference
#     funcRef = Group(ncName.setResultsName("functionName") + 
#                     Suppress(lParen) + 
#                     Group(Optional(delimitedList(Group(Optional(ncName.setResultsName("argName") + 
#                                                                 Suppress(assignOp + ~assignOp)) + 
#                                                        blockExpr).setResultsName("functionArg")))).setResultsName("functionArgs") + 
#                 Suppress(rParen)).setResultsName("functionReference") 
    
    funcRef = Group(ncName.setResultsName("functionName") + 
                    Suppress(lParen) + 
                    Group(Optional(delimitedList(Group(blockExpr).setResultsName("functionArg")) +
                                   Optional(Suppress(commaOp)) #This allows a trailing comma for lists and sets
                                   )).setResultsName("functionArgs") + 
                Suppress(rParen)).setResultsName("functionReference") 
    
    # non precedence expressions (logical expressions)
    
    printExpr  = Group(Suppress(Keyword("print")) +
                       Suppress(lParen) +
                       Group(blockExpr).setResultsName("printValue") +
                       Suppress(rParen) +
                       Group(blockExpr).setResultsName("passThroughExpr")).setResultsName("printExpr")

    aspect = Group(
                   Suppress(Literal("@")) +
                   Group(qName).setResultsName("aspectName") +
                   Optional(
                            Suppress(lParen) +
                            ncName.setResultsName("aspectVar") +
                            Suppress(rParen)
                            ) +
                   (assignOp | inOp).setResultsName("aspectOperator") + 
                   ( 
                    Literal("**").setParseAction(lambda s, l, t: "allWithDefault").setResultsName("all") | 
                    Literal("*").setParseAction(lambda s, l, t: "all").setResultsName("all") |                                 
                    Group(blockExpr).setResultsName("aspectExpr")
                    )
                   ).setResultsName("aspectFilter")

    aspectEmptyWithVar = Group(
                               Suppress(Literal("@")) +
                               Group(qName).setResultsName("aspectName") +
                               Suppress(lParen) +
                               ncName.setResultsName("aspectVar") +
                               Suppress(rParen)
                               ).setResultsName("aspectFilter")

    aspectLineItem = Group(
                   Suppress(Literal("@")) +

                   Group(
                         Group(
                               Empty().setParseAction(lambda s, l, t: "*").setResultsName("prefix") +
                               Empty().setParseAction(lambda s, l, t: "lineItem").setResultsName("localName")
                               ).setResultsName("qName")
                         
                         ).setResultsName("aspectName") +
                   Empty().setParseAction(lambda s, l, t: "=").setResultsName("aspectOperator") +                                
                   Group(qName).setResultsName("aspectExpr")
                   ).setResultsName("aspectFilter")
    
    factset = Group(
                    Group(OneOrMore(aspect | aspectEmptyWithVar | aspectLineItem)).setResultsName("aspectFilters") +
                    Optional(CaselessLiteral("nomoredims").setParseAction(lambda s, l, t: "closed") | CaselessLiteral("nmd").setParseAction(lambda s, l, t: "closed"), default="open").setResultsName("factsetType") +
                    Optional(Group(
                                   Suppress(Literal("[")) +
                                   blockExpr + 
                                   Suppress(Literal("]"))
                                   ).setResultsName("whereExpr")) 
                    ).setResultsName("factset")

    ifExpr = Group(Suppress(ifOp) + 
             Group(blockExpr).setResultsName("condition") + 
             Group(blockExpr).setResultsName("thenExpr") +
             # this will flatten nested if conditions 
             ZeroOrMore(Group(Suppress(elseOp + ifOp) + 
                              Suppress(lParen) +
                              Group(blockExpr).setResultsName("condition") +
                              Suppress(rParen) +
                              Group(blockExpr).setResultsName("thenExpr")
                              ).setResultsName("elseIfExpr")
                        ) +
             Suppress(elseOp) + 
             Group(blockExpr).setResultsName("elseExpr")).setResultsName("ifExpr")
     
    forExpr = (
               #version with parens around the for control
               (Group(Suppress(forOp) + 
                    Suppress(lParen) + 
                    Group(
                          ncName.setResultsName("forVar") + 
                          Optional(tagOp).setResultsName("tagged") +
                          Suppress(inOp) + 
                          #Group(blockExpr).setResultsName("forLoop")
                          blockExpr.setResultsName('forLoopExpr') 
                          ).setResultsName("forControl") +
                    Suppress(rParen) +
                    Group(blockExpr).setResultsName("forBodyExpr")).setResultsName("forExpr")) |
               #version without parens around the for control
               (Group(Suppress(forOp) + 
                    Group(
                          ncName.setResultsName("forVar") + 
                          Optional(tagOp).setResultsName("tagged") +
                          Suppress(inOp) + 
                          #Group(blockExpr).setResultsName("forLoop")
                          blockExpr.setResultsName('forLoopExpr') 
                          ).setResultsName("forControl") +
                    Group(blockExpr).setResultsName("forBodyExpr")).setResultsName("forExpr"))
               )
    
    withControlExpr = Group(Group(OneOrMore(aspect | aspectEmptyWithVar | aspectLineItem)).setResultsName("aspectFilters")).setResultsName("factset")
           
    withExpr = Group(Suppress(withOp) + 
                     (
                        (
                             Suppress(lParen) + 
                             Group(withControlExpr).setResultsName("controlExpr") + 
                             Suppress(rParen)
                         ) |
                         Group(withControlExpr).setResultsName("controlExpr")
                      ) +
                     Group(blockExpr).setResultsName("expr")
                     ).setResultsName("withExpr")
    
    # Order is important here because it will match the first. 
    # For example, the float literal has to be before the integer literal. This is because a float can starte
    # with an integer in which case the parser will think it is an integer. When it hits the decimal point
    # the parser will fail because an integer cannot have a decimal point. By putting the float first, it can fail matching the float and
    # fall back to see if matches the integer.
    # This issue is also true for "if", "for" and "with" expressions. These have to be before qNames because these expressions
    # start with tokens that could match a qName. 
    atom = (
            printExpr | 
            ifExpr |
            forExpr |
            withExpr |
            
#             listLiteralFunction |
#             setLiteralFunction |
            
            floatLiteral |
            integerLiteral |    
            stringLiteral |

            factset |
            
            severityLiteral |
               
            funcRef |          
            varRef |
            
            boolLiteral |
            voidLiteral |
            
            qName |
            (Suppress(lParen) + blockExpr + Suppress(rParen)) | # parenthesized expression
            listLiteral#.setResultsName("list")
             )

    valuesExpr = Group((Suppress(valuesOp) + atom)).setResultsName("valuesExpr") | atom
    #These expressions are in order of operator precedence
    taggedExpr = Group(Group(valuesExpr).setResultsName("expr") + Suppress(tagOp) + ncName.setResultsName("tagName")).setResultsName("taggedExpr") | valuesExpr
    #unary expressions
    unaryExpr = Group((unaryOp.setResultsName("unaryOp") + Group(taggedExpr).setResultsName("expr"))).setResultsName("unaryExpr") | taggedExpr
    #property expression
    propertyExpr = Group(Optional(Group(unaryExpr).setResultsName("expr")) + 
                       Group(OneOrMore(Group(Suppress(methodOp) + 
                                       simpleName.setResultsName("propertyName") +
                                       Optional(Suppress(lParen) + 
                                                    Group(Optional(delimitedList(Group(blockExpr).setResultsName("propertyArg")))).setResultsName("propertyArgs") +
                                                    Suppress(rParen) 
                                        ) +
                                         Optional(Suppress(tagOp) +
                                                 ncName.setResultsName("tagName")
                                        )
                                       
                                       ).setResultsName("property"))).setResultsName("properties")
                       ).setResultsName("propertyExpr") | unaryExpr
    
    
    
    #valuesExpr = Group((Suppress(valuesOp) + propertyExpr)).setResultsName("valuesExpr") | propertyExpr
    
    #binary expressions
    multExpr = Group((propertyExpr + OneOrMore(multOp + propertyExpr))).setResultsName("multExpr") | propertyExpr
    addExpr = Group((multExpr + OneOrMore(addOp + multExpr))).setResultsName("addExpr") | multExpr
    compExpr = Group((addExpr + OneOrMore(compOp + addExpr))).setResultsName("compExpr") | addExpr
    notExpr = Group((Suppress(notOp) + compExpr)).setResultsName("notExpr") | compExpr
    andExpr = Group((notExpr + OneOrMore(Suppress(andOp) + notExpr))).setResultsName("andExpr") | notExpr
    orExpr = Group((andExpr + OneOrMore(Suppress(orOp) + andExpr))).setResultsName("orExpr") | andExpr
    formulaExpr = Group((orExpr + OneOrMore(Suppress(formulaOp) + orExpr))).setResultsName("formulaExpr") | orExpr
    
    expr << formulaExpr
    
    # block expression is a set of varibalbe assignments followed by an exprresoin.
    varAssign = Group(simpleName.setResultsName("varName") + 
                      Optional(tagOp).setResultsName("tagged") + 
                      Suppress(assignOp) + 
                      Group(blockExpr).setResultsName("expr") + 
                      Optional(Suppress(assignEnd))
                ).setResultsName("varAssign")
    blockExpr << (Group((OneOrMore(varAssign) + Group(expr).setResultsName("expr"))).setResultsName("blockExpr") | expr)

    # top level parse elements.
    
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
    nsDeclaration = (
                    Group(
                          Suppress(Keyword("namespace")) +
                          Group(ncName).setResultsName("prefix") +
                          Suppress(Literal("=")) +
                          nsURI.setResultsName("namespaceUri")
                           ).setResultsName("nsDeclaration") |
                     Group(
                           Suppress(Keyword("namespace")) +
                           Empty().setParseAction(lambda s, l, t: "*").setResultsName("prefix") +
                           nsURI.setResultsName("namespaceUri")
                           ).setResultsName("nsDeclaration")                     
                     )    


    #annotation
    annotation = Group(Suppress(annotationOp) +
                       ncName.setResultsName("annocationName") + 
                       Optional(Suppress(lParen) + 
                             Group(Optional(delimitedList(Group(expr).setResultsName("annotationArg")))).setResultsName("annotationArgs") +
                             Suppress(rParen))
                 ).setResultsName("annotation")
    
    #constant
    constant = Group(
                  Suppress(Keyword("constant")) +
                  ncName.setResultsName("constantName") + 
                  Optional(tagOp).setResultsName("tagged") + 
                  Suppress(assignOp) + 
                  Group(expr).setResultsName("expr") 
            ).setResultsName("constantAssign")
    
    #extras needed for top level parse elements.
    severity = Suppress(Keyword("severity")) + ncName.setResultsName("severity")
    message = Suppress(Keyword("message")) + Group(expr).setResultsName("message")
    
    #precondition
    preconditionDeclaration = Group(Suppress(Keyword("precondition")) +
                                    ncName.setResultsName("preconditionName") +
                                    blockExpr.setResultsName("expr") +
                                    Optional(Suppress(Keyword("otherwise")) +
                                             Suppress(Keyword("raise")) + 
                                             ncName.setResultsName("otherwiseRuleName") +
                                             Optional(severity)) +
                                    Optional(message)
                                ).setResultsName("preconditionDeclaration")
    
    preconditionRef = Group(Suppress(Keyword("require")) + Group(delimitedList(ncName.setResultsName("preconditionName"))).setResultsName("preconditionNames")).setResultsName("preconditionRef")
    
    packageDeclaration = Group(Optional(annotation) + 
                               Optional(preconditionRef) +
                               Suppress(Keyword("package")) + 
                               ncName.setResultsName("packageName")).setResultsName("package")

    functionDeclaration = Group(
        Optional(annotation) +
        Suppress(Keyword("function")) + 
        ncName.setResultsName("functionName") + 
        Suppress(lParen) + 
        Group(Optional(delimitedList(Group(ncName.setResultsName("argName") + Optional(tagOp.setResultsName("tagged")) + Optional(ncName.setResultsName("tagName"))).setResultsName("functionArg")))).setResultsName("functionArgs") +
        Suppress(rParen) +
        Group(blockExpr).setResultsName("expr")
        ).setResultsName("functionDeclaration")
    
    macroDeclaration = Group(
        Optional(annotation) +                            
        Suppress(Keyword("macro")) + 
        ncName.setResultsName("macroName") + 
        Suppress(lParen) + 
        Group(Optional(delimitedList(Group(ncName.setResultsName("argName") + Optional(tagOp.setResultsName("tagged")) + Optional(ncName.setResultsName("tagName"))).setResultsName("macroArg")))).setResultsName("macroArgs") +
        Suppress(rParen) +
        Group(blockExpr).setResultsName("expr")
        ).setResultsName("macroDeclaration")
    
    raiseDeclaration = Group(
        Optional(annotation) +
        Optional(preconditionRef) +
        Suppress(Keyword("raise")) +
        ncName.setResultsName("raiseName") + 
        Optional(severity) +
        Group(blockExpr).setResultsName("expr") +
        Optional(message)
        ).setResultsName("raiseDeclaration")
        
    reportDeclaration = Group(
        Optional(annotation) +
        Optional(preconditionRef) +
        Suppress(Keyword("report")) +
        ncName.setResultsName("reportName") + 
        Optional(severity) +
        Group(blockExpr).setResultsName("expr") +
        Optional(message)
        ).setResultsName("reportDeclaration")

    formulaDeclaration = Group(
        Optional(annotation) +
        Optional(preconditionRef) +
        Suppress(Keyword("formula")) +
        ncName.setResultsName("formulaName") +
        Optional(severity) + 
        Optional(Suppress(Keyword("bind")) + (Keyword("both") | Keyword("left") | Keyword("right")), default="both").setResultsName("bind") +
        Group(blockExpr).setResultsName("expr") +
        Optional(message)
        ).setResultsName("formulaDeclaration")
        
    ruleBase = Group(
                     Optional(annotation) +
                     Optional(preconditionRef) +
                     Suppress(Keyword("rule-base"))
                ).setResultsName("ruleBase")
            
    xuleFile = Group(stringStart +
            ZeroOrMore(nsDeclaration) +
            ZeroOrMore(preconditionDeclaration) +
            Optional(packageDeclaration) +
            ZeroOrMore(
                    constant |
                    functionDeclaration |
                    macroDeclaration |
                    raiseDeclaration |
                    formulaDeclaration |
                    preconditionDeclaration |
                    reportDeclaration |
                    ruleBase 
                  ) + stringEnd
                ).setResultsName("xuleFile").ignore(comment)
    
    #xuleFile = (stringStart + Optional(header) + ZeroOrMore(packageBody) + stringEnd).setResultsName("xule").ignore(comment)
    
    return xuleFile
