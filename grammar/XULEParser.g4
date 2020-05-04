parser grammar XULEParser;

options { tokenVocab=XULELexer; }

xuleFile: (topLevelDeclaration | assertion | output)* EOF;

topLevelDeclaration:
    namespaceDeclaration | constantDeclaration | functionDeclaration | outputAttributeDeclaration | ruleNamePrefixDeclaration;

namespaceDeclaration: NAMESPACE (identifier ASSIGN)? URL;
outputAttributeDeclaration: OUTPUT_ATTRIBUTE identifier;
ruleNamePrefixDeclaration: RULE_NAME_PREFIX identifier;

output:
    OUTPUT identifier (OPEN_BRACKET AT identifier CLOSE_BRACKET)?
    (constantDeclaration | assignment)*
    expression outputAttribute*;
outputAttribute: outputAttributeName expression SEMI?;

assertion:
    ASSERT ASSERT_RULE_NAME (ASSERT_SATISFIED | ASSERT_UNSATISFIED)
    (constantDeclaration | functionDeclaration | assignment | expression outputAttribute*)+;

constantDeclaration: CONSTANT identifier ASSIGN expression;
functionDeclaration: FUNCTION identifier OPEN_PAREN (functionArgument (COMMA functionArgument)*)? CLOSE_PAREN block;
functionArgument: identifier;

/** Expressions */
expression:
    ifExpression | forExpression |
    OPEN_PAREN expression CLOSE_PAREN |
    expression SHARP tag |
    expression OPEN_BRACKET expression CLOSE_BRACKET |
    expression propertyAccess+ |
    expression parametersList |
    (PLUS | MINUS) expression |
    expression (TIMES | DIV) expression |
    expression (PLUS | MINUS | ADD_LR | ADD_L | ADD_R | SUB_LR | SUB_L | SUB_R) expression |
    expression (AND_OP | INTERSECT) expression |
    expression SIMM_DIFF expression |
    expression (EQUALS | NOT_EQUALS | GT | LT | GTE | LTE | NOT? IN) expression |
    NOT expression |
    expression AND expression |
    expression OR expression |
    //"Simple" expressions
    literal | variableRead | factset | filter | navigation;

block: assignment* expression;

assignment: assignedVariable ASSIGN block SEMI?;
ifExpression: IF expression block ELSE block;

forExpression: FOR (OPEN_PAREN forHead CLOSE_PAREN | forHead) block;
forHead: forVariable IN expression;

parametersList: OPEN_PAREN (expression (COMMA expression)* COMMA?)? CLOSE_PAREN;

factset: AT | OPEN_CURLY factsetBody CLOSE_CURLY | OPEN_BRACKET factsetBody CLOSE_BRACKET;
factsetBody: AT | (aspectFilter | factset | expression)*;
aspectFilter:
    (aspectFilterOptions | aspectFilterOptions? aspectFilterFilter)
    (AS assignedVariable)? (WHERE expression)?;

aspectFilterOptions: (COVERED | COVERED_DIMS) NONILS? | NONILS (COVERED | COVERED_DIMS)?;
aspectFilterFilter:
    AT AT? (CONCEPT | identifier) propertyAccess*
    ((ASSIGN | NOT_EQUALS | GT | LT | GTE | LTE | NOT? IN) (expression | TIMES))?;

filter: FILTER expression (WHERE block)? (RETURNS filterReturn)?;
filterReturn : (expression | OPEN_PAREN expression (COMMA expression)* CLOSE_PAREN);

navigation: NAVIGATE DIMENSIONS? arcrole? direction levels=INTEGER? (INCLUDE START)? (FROM expression)? (TO expression)?
    (STOP WHEN expression)? (ROLE role)? (DRS_ROLE role)?
    (CUBE identifier)? (TAXONOMY expression)?
    navigationWhereClause?
    (RETURNS ((BY NETWORK navigationReturnOptions?) | navigationReturnOptions) (AS (LIST | DICTIONARY))?)?;
navigationReturnOptions: (LIST | SET)?
    (OPEN_PAREN navigationReturnOption (COMMA navigationReturnOption)* CLOSE_PAREN | navigationReturnOption);
navigationWhereClause: WHERE expression;
/** This exists so that when we know when to declare a new variable. */
tag: identifier;
/** This exists so that when we know when to declare a new variable. */
forVariable: identifier;
/** This exists so that when validating and suggesting code we can restrict to known variables. */
assignedVariable: identifier;
/** This exists so that when validating and suggesting code we can restrict to known variables. */
variableRead: identifier;
/** This exists so that when validating and suggesting code we can restrict to well-known keywords. */
navigationReturnOption: identifier;

arcrole: role;
role: identifier propertyAccess* | stringLiteral;
/** This exists so that when suggesting code we can restrict to well-known keywords. */
direction: identifier;
/** This exists so that when suggesting code we can restrict to well-known keywords. */
outputAttributeName: identifier;
//End expressions

propertyAccess: DOT identifier;
/** With this rule we cover IDENTIFIER tokens, as well as other tokens (keywords) that we accept as identifiers as well. */
identifier: IDENTIFIER |
    AS | ASSERT | BY | CONCEPT | CONSTANT | COVERED | CUBE | DICTIONARY | DIMENSIONS | DRS_ROLE | FALSE | INTERSECT |
    LIST | NETWORK | ROLE | SET | START | STOP | TAXONOMY | TRUE | WHEN | WHERE;
literal: stringLiteral | numberLiteral | booleanLiteral;
booleanLiteral: TRUE | FALSE;
numberLiteral: INTEGER | REAL;
stringLiteral:
    DOUBLE_QUOTE (STRING_CONTENTS | OPEN_CURLY expression CLOSE_CURLY)* DOUBLE_QUOTE |
    SINGLE_QUOTE (STRING_CONTENTS | OPEN_CURLY expression CLOSE_CURLY)* SINGLE_QUOTE;