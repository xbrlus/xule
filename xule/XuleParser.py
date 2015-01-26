
from pyparsing import (Word, Keyword,  
                     Literal, CaselessLiteral, 
                     Combine, Optional, nums, Forward, Group, ZeroOrMore,  
                     ParserElement,  delimitedList, Suppress, Regex, 
                     QuotedString, OneOrMore, ParseResults, oneOf, cStyleComment,
                     lineEnd, White, SkipTo, Empty, stringStart, stringEnd, ParseException, ParseSyntaxException, lineno)

import os
import datetime
import sys

def printRes(pr, level=0):
    level = level + 1
    print("level: " + str(level))
    if isinstance(pr, ParseResults):
        print("name: " + pr.name)
        
        for child in pr:
            printRes(child, level)

def add_location(src, loc, toks):
    #adds location information to the parse results
    '''NEEDS TO BE ADDED TO EACH OF THE ParserElements'''
    toks['char_loc'] = loc
    toks['line'] = lineno(loc, src)
    
    return toks

def get_grammar():
    
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
    methodOp = Literal("::")
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
             "[A-Za-z0-9\xC0-\xD6\xD8-\xF6\xF8-\xFF\u0100-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040\xB7_.-]*)?"
              )
    
    
    ncName = Word(r'_-.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    prefix = Word('_-.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
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
    infLiteral = Combine(Optional(sign) + CaselessLiteral("INF"))
    floatLiteral = Group(( Combine(decimalPoint + digits + Optional (sciNot + integerLiteral)) |
                     Combine(integerLiteral + decimalPoint + digits + Optional (sciNot + integerLiteral)) |
                     Combine(integerLiteral + decimalPoint + Optional (sciNot + integerLiteral)) |
                     infLiteral).setResultsName("value")).setResultsName("float")
    #string literals
    stringLiteral = Group(( QuotedString("'", multiline=True, unquoteResults=True, escChar="\\")  | 
                      QuotedString('"', multiline=True, unquoteResults=True, escChar="\\") ).setResultsName("value")).setResultsName("string")
    
    #boolean literals
    boolLiteral = Group((Keyword("true") | Keyword("false")).setResultsName("value")).setResultsName("boolean")
    
    #void literals
    noneLiteral = Group((Keyword("none")).setResultsName("value")).setResultsName("void") 
    unboundLiteral = Group((Keyword("unbound")).setResultsName("value")).setResultsName("void") 
    voidLiteral = noneLiteral | unboundLiteral #Group((Keyword("none") | Keyword("unbound")).setResultsName("value")).setResultsName("void")
    
    #severity literals   
    severityLiteral = Group(oneOf("error warning info pass").setResultsName("severityName") + 
                            Group(Optional(Suppress(lParen) +
                                           Optional(delimitedList(Group(ncName.setResultsName("tagName") +
                                                                        Suppress("=") +
                                                                        Group(blockExpr).setResultsName("argExpr") 
                                                                        ).setResultsName("severityArg"))) +
                                           Suppress(rParen))).setResultsName("severityArgs")).setResultsName("severity")
    
    #list - have a special from of (1,2,3)
    emptyList = Suppress(lParen + rParen)
    listLiteral = Group(emptyList | 
                        ( 
                         Suppress(lParen) + 
                            blockExpr + 
                            Suppress(commaOp) + 
                            Optional(delimitedList(blockExpr) + 
                                       Optional(Suppress(commaOp))) + 
                         Suppress(rParen)
                        )
                  )
    
    #alternative version of a list looks like a function call: list(1, 2, 3, ...)
    
# These were replaced by aggregation functions
    
#     listLiteralFunction = Group(Suppress(Keyword("list")) +
#                                 Suppress(lParen) + 
#                                 Optional(delimitedList(blockExpr)) +
#                                       Optional(Suppress(commaOp)) +
#                                 Suppress(rParen)
#                           ).setResultsName("list")
#     #set
#     setLiteralFunction = Group(Suppress(Keyword("set")) +
#                                 Suppress(lParen) + 
#                                 Optional(delimitedList(blockExpr)) +
#                                       Optional(Suppress(commaOp)) +
#                                 Suppress(rParen)
#                           ).setResultsName("set")    
    
    #atoms - basic units

    # references
    varRef = Group(Suppress(Literal("$")) + ncName.setResultsName("varName")).setResultsName("varRef") # variable reference
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
    
    
    ifExpr = Group(Suppress(ifOp) + 
                   Suppress(lParen) + 
                   Group(blockExpr).setResultsName("condition") + 
                   Suppress(rParen) +
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
    forExpr = Group(Suppress(forOp) + 
                    Suppress(lParen) + 
                    ncName.setResultsName("forVar") + 
                    Optional(tagOp).setResultsName("tagged") +
                    Suppress(inOp) + 
                    Group(blockExpr).setResultsName("forLoop") + 
                    Suppress(rParen) +
                    Group(blockExpr).setResultsName("expr")).setResultsName("forExpr")
    withExpr = Group(Suppress(withOp) + Suppress(lParen) + Group(blockExpr).setResultsName("controlExpr") + Suppress(rParen) +
                Group(blockExpr).setResultsName("expr")).setResultsName("withExpr")
    
    # hyperspace
    # The "~Keyword("where") is used to prevent this parser from matching the "where" clause of the hyperspace. This only becomes an issue when there is
    # a trailing ";" before the "where". 
    aspectFilter = ~Keyword("where") + Group(Group(qName).setResultsName("aspectName") + 
                         Optional(Suppress(Keyword("as")) + ncName.setResultsName("aspectVar")) +
                         Optional(
                                (assignOp | inOp).setResultsName("aspectOperator") + 
                                ( 
                                    Literal("**").setParseAction(lambda s, l, t: "allWithDefault").setResultsName("all") | 
                                    Literal("*").setParseAction(lambda s, l, t: "all").setResultsName("all") |                                 
                                    Group(blockExpr).setResultsName("aspectExpr")
                                 )
                         )
                   ).setResultsName("aspectFilter")

    openFactset = Group(                        
                        Optional(Group(qName).setResultsName("lineItemAspect")) + #~White() +
                        Suppress(Literal("[")) +
                        Empty().setParseAction(lambda s, l, t: "open").setResultsName("factsetType") + #inserts a parseResult for the factset type
                        Group(Optional(delimitedList(aspectFilter, delim=";") + Suppress(Optional(Literal(";"))))).setResultsName("aspectFilters") + #this is the delimited list of aspects
                        Optional(Group(
                              Suppress(Keyword("where")) +
                                blockExpr
                                ).setResultsName("whereExpr")) +
                        Suppress(Literal("]"))
                     ).setResultsName("factset")    

    closedFactset = Group(                        
                        Optional(Group(qName).setResultsName("lineItemAspect")) + #~White() +
                        Suppress(Literal("[[")) +
                        Empty().setParseAction(lambda s, l, t: "closed").setResultsName("factsetType") + #inserts a parseResult for the factset type
                        Group(Optional(delimitedList(aspectFilter, delim=";") + Suppress(Optional(Literal(";"))))).setResultsName("aspectFilters") + #this is the delimited list of aspects
                        Optional(Group(
                                Suppress(Keyword("where")) +
                                blockExpr
                                ).setResultsName("whereExpr")) +
                        Suppress(Literal("]]"))
                     ).setResultsName("factset")                     

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

            closedFactset |
            openFactset |
            
            severityLiteral |
               
            funcRef |          
            varRef |
            
            boolLiteral |
            voidLiteral |
            
            qName |
            (Suppress(lParen) + blockExpr + Suppress(rParen)) | # parenthesized expression
            listLiteral.setResultsName("list")
             )
    

    #These expressions are in order of operator precedence
    taggedExpr = Group(Group(atom).setResultsName("expr") + Suppress(tagOp) + ncName.setResultsName("tagName")).setResultsName("taggedExpr") | atom
    #unary expressions
    unaryExpr = Group((unaryOp.setResultsName("unaryOp") + Group(taggedExpr).setResultsName("expr"))).setResultsName("unaryExpr") | taggedExpr
    #property expression
    propertyExpr = Group(Optional(Group(unaryExpr).setResultsName("expr")) + 
                       Group(OneOrMore(Group(Suppress(methodOp) + 
                                       ncName.setResultsName("propertyName") +
                                       Optional(Suppress(lParen) + 
                                                    Group(Optional(delimitedList(Group(blockExpr).setResultsName("propertyArg")))).setResultsName("propertyArgs") +
                                                    Suppress(rParen) 
                                        ) +
                                         Optional(Suppress(tagOp) +
                                                 ncName.setResultsName("tagName")
                                        )
                                       
                                       ).setResultsName("property"))).setResultsName("properties")
                       ).setResultsName("propertyExpr") | unaryExpr
    
    
    
    valuesExpr = Group((Suppress(valuesOp) + propertyExpr)).setResultsName("valuesExpr") | propertyExpr
    
    #binary expressions
    multExpr = Group((valuesExpr + OneOrMore(multOp + valuesExpr))).setResultsName("multExpr") | valuesExpr
    addExpr = Group((multExpr + OneOrMore(addOp + multExpr))).setResultsName("addExpr") | multExpr
    compExpr = Group((addExpr + OneOrMore(compOp + addExpr))).setResultsName("compExpr") | addExpr
    notExpr = Group((Suppress(notOp) + compExpr)).setResultsName("notExpr") | compExpr
    andExpr = Group((notExpr + OneOrMore(Suppress(andOp) + notExpr))).setResultsName("andExpr") | notExpr
    orExpr = Group((andExpr + OneOrMore(Suppress(orOp) + andExpr))).setResultsName("orExpr") | andExpr
    
    
    expr << orExpr
    
    # block expression is a set of varibalbe assignments followed by an exprresoin.
    varAssign = Group(ncName.setResultsName("varName") + 
                      Optional(tagOp).setResultsName("tagged") + 
                      Suppress(assignOp) + 
                      Group(blockExpr).setResultsName("expr") + 
                      Suppress(assignEnd)
                ).setResultsName("varAssign")
    blockExpr << (Group((OneOrMore(varAssign) + Group(expr).setResultsName("expr"))).setResultsName("blockExpr") | expr)

    # top level parse elements.
    
    nsURI = ( QuotedString("'", unquoteResults=True)  | QuotedString('"', unquoteResults=True) )
    
    nsDeclaration = Group(
        Suppress(Keyword("xmlns")) +
        Optional(Suppress(qNameOp) + ncName, default="*").setResultsName("prefix") +
        Suppress(Literal("=")) + 
        nsURI.setResultsName("namespaceUri")
        ).setResultsName("nsDeclaration")

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
    
    preconditionRef = Group(Suppress(Keyword("require")) + Group(delimitedList(ncName.setResultsName("preconditionName"))).setResultsName("preconditionNames")).setResultsName("preonditionRef")
    
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
        ).setResultsName("macroDeclaratoin")
    
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
        Group(ZeroOrMore(varAssign)).setResultsName("varAssigns") +
        Group(expr).setResultsName("exprLeft") +
        Suppress(formulaOp) +
        Group(blockExpr).setResultsName("exprRight") +
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


def parseFile(fileName, xuleGrammar, ruleSet, xml_dir=None):
    try:
        '''WOULD LIKE TO CHECK IF THE FILE IS ALREADY IN THE RULE SET AND IF IT HAS CHANGED.
           IF IT HASN'T CAN SKIP THE PARSING AND USE THE EXISTING PICKLED FILE. HOWEVER,
           NEED TO CHANGE THE WAY 'NEW' IS DONE IN THE XULERULESET, SO THAT IT PRESERVES THE 
           EXISTING FILES AND CATALOGS AND THEN CLEANS EVERYTHING UP WHEN THE RULESET IS CLOSED.
        '''
        start_time = datetime.datetime.today()
        print("%s: parse start %s" % (datetime.datetime.isoformat(start_time), fileName))
        
        parseRes = xuleGrammar.parseFile(fileName)

        if xml_dir:
            xml_file = xml_dir + "/" + os.path.basename(fileName) + ".xml"
            
            if not os.path.exists(xml_dir):
                os.makedirs(xml_dir)
            
            with open(xml_file,"w") as o:
                o.write(parseRes.asXML())
        
        end_time = datetime.datetime.today()
        print("%s: parse end. Took %s" % (datetime.datetime.isoformat(end_time), end_time - start_time))
        
        ast_start = datetime.datetime.today()
        print("%s: ast start" % datetime.datetime.isoformat(ast_start))
        ruleSet.add(parseRes, os.path.getmtime(fileName), os.path.basename(fileName))
        ast_end = datetime.datetime.today()
        print("%s: ast end. Took %s" %(datetime.datetime.isoformat(ast_end), ast_end - ast_start))
        
        
    except (ParseException, ParseSyntaxException) as err:
        print("Parse error in %s \n" 
            "line: %i col: %i position: %i\n"
            "%s\n"
            "%s" % (sys.argv[1], err.lineno, err.col, err.loc, err.msg, err.line))



def parseRules(files, dest, xml_dir=None):
    
    parse_start = datetime.datetime.today()
    
    #Need to check the recursion limit. 1000 is too small for some rules.
    new_depth = 2500
    orig_recursionlimit = sys.getrecursionlimit()
    if orig_recursionlimit < new_depth:
        sys.setrecursionlimit(new_depth)
    
    xuleGrammar = get_grammar()
    ruleSet = XuleRuleSet()
    ruleSet.new(dest)
    
    for ruleFile in files:
        processFile = ruleFile.strip()
        if os.path.isfile(processFile):
            parseFile(processFile, xuleGrammar, ruleSet, xml_dir)

        elif os.path.isdir(ruleFile.strip()):
            for root, dirs, files in os.walk(ruleFile.strip()):
                for name in files:
                    if os.path.splitext(name)[1] == ".xsr":
                        print("Processing: %s" % os.path.basename(name))
                        parseFile(os.path.join(root, name), xuleGrammar, ruleSet, xml_dir)            
        else:
            print("Not a file or directory: %s" % processFile)
    
    ruleSet.close()
    
    #reset the recursion limit
    if orig_recursionlimit != sys.getrecursionlimit():
        sys.setrecursionlimit(orig_recursionlimit)    

    parse_end = datetime.datetime.today()
    print("%s: Parsing finished. Took %s" %(datetime.datetime.isoformat(parse_end), parse_end - parse_start))
    
if __name__ == "__main__":
    from XuleRuleSet import XuleRuleSet
    
    if len(sys.argv) > 1:
        dest = sys.argv[2].strip() if len(sys.argv) > 2 else "xuleRules"
        if len(sys.argv) > 3:
            parseRules([sys.argv[1]], dest, xml_dir = sys.argv[3])
        else:
            parseRules([sys.argv[1]], dest)
    '''    
    else: 
        try:   
            for test in tests:
                print("-----------------------------------------------------")
                print(test)
                xuleGrammar = get_grammar()
                
                parseRes = xuleGrammar.parseString(test)
                
                print(parseRes.asXML())
        except (ParseException, ParseSyntaxException) as err:
            print("Parse error  \n" 
                "line: %i col: %i position: %i\n"
                "%s\n"
                "%s" % ( err.lineno, err.col, err.loc, err.msg, err.line)) 
    
            #print(parseRes.dump()) 
    '''        
else:
    from .XuleRuleSet import XuleRuleSet