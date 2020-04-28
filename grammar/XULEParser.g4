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
    expression
    (outputAttributeName expression SEMI?)*;

assertion: ASSERT ASSERT_RULE_NAME (ASSERT_SATISFIED | ASSERT_UNSATISFIED)
    (constantDeclaration | functionDeclaration | assignment | expression (outputAttributeName expression SEMI?)*)+;

constantDeclaration: CONSTANT identifier ASSIGN expression;
functionDeclaration: FUNCTION identifier OPEN_PAREN (functionArgument (COMMA functionArgument)*)? CLOSE_PAREN block;
functionArgument: identifier;

/** Expressions */
expression:
    ifExpression | forExpression |
    expression OR expression |
    expression AND expression |
    NOT expression |
    expression (EQUALS | NOT_EQUALS | GT | LT | GTE | LTE | NOT? IN) expression |
    expression SIMM_DIFF expression |
    expression (AND_OP | INTERSECT) expression |
    expression (PLUS | MINUS | ADD_LR | ADD_L | ADD_R | SUB_LR | SUB_L | SUB_R) expression |
    expression (TIMES | DIV) expression |
    (PLUS | MINUS) expression |
    expression parametersList |
    expression propertyAccess+ |
    expression OPEN_BRACKET expression CLOSE_BRACKET |
    expression SHARP identifier |
    OPEN_PAREN expression CLOSE_PAREN |
    //"Simple" expressions
    literal | identifier | factset | filter | navigation;

block: assignment* expression;

assignment: identifier ASSIGN block SEMI?;
ifExpression: IF expression block ELSE block;

forExpression: FOR (OPEN_PAREN forHead CLOSE_PAREN | forHead) block;
forHead: identifier IN expression;

parametersList: OPEN_PAREN (expression (COMMA expression)* COMMA?)? CLOSE_PAREN;

factset: AT | OPEN_CURLY factsetBody CLOSE_CURLY | OPEN_BRACKET factsetBody CLOSE_BRACKET;
factsetBody: AT | (aspectFilter | factset | expression)*;
aspectFilter:
    (aspectFilterOptions | aspectFilterOptions? aspectFilterFilter)
    (AS identifier)? (WHERE expression)?;

aspectFilterOptions: (COVERED | COVERED_DIMS) NONILS? | NONILS (COVERED | COVERED_DIMS)?;
aspectFilterFilter:
    AT AT? ((CONCEPT | identifier) propertyAccess* (ASSIGN | NOT_EQUALS | GT | LT | GTE | LTE | NOT? IN))?
    (expression | TIMES);

filter: FILTER expression (WHERE block)? (RETURNS returnExpression)?;

navigation: NAVIGATE DIMENSIONS? arcrole? direction levels=INTEGER? (INCLUDE START)? (FROM expression)? (TO expression)?
    (STOP WHEN expression)? (ROLE role)? (DRS_ROLE role)?
    (CUBE identifier)? (TAXONOMY expression)?
    (WHERE expression)?
    (RETURNS ((BY NETWORK returnExpression?) | returnExpression) (AS (LIST | DICTIONARY))?)?;

returnExpression : (expression | OPEN_PAREN expression (COMMA expression)* CLOSE_PAREN);
/** This exists so that when suggesting code we can restrict to well-known keywords. */
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
    LIST | NETWORK | ROLE | START | STOP | TAXONOMY | TRUE | WHEN | WHERE;
literal: stringLiteral | NUMBER | booleanLiteral;
booleanLiteral: TRUE | FALSE;

stringLiteral:
    DOUBLE_QUOTE (STRING_CONTENTS | OPEN_CURLY expression CLOSE_CURLY)* DOUBLE_QUOTE |
    SINGLE_QUOTE (STRING_CONTENTS | OPEN_CURLY expression CLOSE_CURLY)* SINGLE_QUOTE;