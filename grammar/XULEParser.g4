parser grammar XULEParser;

options { tokenVocab=XULELexer; }

xuleFile: (topLevelDeclaration | assertion | output)* EOF;

topLevelDeclaration:
    namespaceDeclaration | constantDeclaration | functionDeclaration | outputAttributeDeclaration | ruleNamePrefixDeclaration;

namespaceDeclaration: NAMESPACE identifier ASSIGN URL;
outputAttributeDeclaration: OUTPUT_ATTRIBUTE identifier;
ruleNamePrefixDeclaration: RULE_NAME_PREFIX identifier;

output:
    OUTPUT identifier (OPEN_BRACKET AT identifier CLOSE_BRACKET)?
    (constantDeclaration | assignment)*
    expression
    (MESSAGE expression SEMI?)?;

assertion: ASSERT ASSERT_RULE_NAME (ASSERT_SATISFIED | ASSERT_UNSATISFIED)
    (constantDeclaration | functionDeclaration | assignment | expression (MESSAGE expression SEMI?)? (SEVERITY expression)?)+;

constantDeclaration: CONSTANT identifier ASSIGN expression;
functionDeclaration: FUNCTION identifier OPEN_PAREN (functionArgument (COMMA functionArgument)*)? CLOSE_PAREN body;
functionArgument: identifier;

/** Expressions */
expression:
    OPEN_PAREN expression CLOSE_PAREN |
    expression SHARP identifier |
    ifExpression | forExpression |
    expression AND expression |
    expression OR expression |
    expression (EQUALS | NOT_EQUALS | GREATER_THAN | LESS_THAN) expression |
    expression NOT? IN expression |
    expression (PLUS | MINUS) expression |
    expression (TIMES | DIV) expression |
    expression EXP expression |
    expression INTERSECT expression |
    (PLUS|MINUS|NOT) expression |
    expression propertyAccess+ |
    expression propertyAccess* parametersList |
    expression OPEN_BRACKET expression CLOSE_BRACKET |
    //"Simple" expressions
    variableRef | literal | factset | filter | navigation;

body: assignment* expression;

assignment: identifier ASSIGN expression SEMI?;
ifExpression: IF expression body ELSE body;

forExpression: FOR (OPEN_PAREN forHead CLOSE_PAREN | forHead) body;
forHead: identifier IN expression;

parametersList: OPEN_PAREN (expression (COMMA expression)*)? CLOSE_PAREN;

factset: AT | OPEN_CURLY factsetBody CLOSE_CURLY | OPEN_BRACKET factsetBody CLOSE_BRACKET;
factsetBody: AT | aspectFilter*;
aspectFilter:
    (COVERED | COVERED_DIMS)? AT AT? ((CONCEPT | variableRef) propertyAccess* (ASSIGN | IN))? (expression | TIMES)
    (AT UNIT ASSIGN (expression | TIMES))?
    (AS identifier)? (WHERE expression)?;

filter: FILTER expression (WHERE body)? (RETURNS expression)?;

navigation: NAVIGATE DIMENSIONS? arcrole? direction levels=INTEGER? (INCLUDE START)? (FROM expression)? (TO expression)?
    (STOP WHEN expression)? (ROLE role)?
    (CUBE identifier)? (TAXONOMY expression)?
    (WHERE expression)?
    (RETURNS ((BY NETWORK returnExpression?) | returnExpression)
        (AS DICTIONARY)?)?;

returnExpression : (expression | OPEN_PAREN expression (COMMA expression)* CLOSE_PAREN);
/** This exists so that when suggesting code we can restrict to well-known keywords. */
arcrole: role;
role: identifier | stringLiteral;
/** This exists so that when suggesting code we can restrict to well-known keywords. */
direction: identifier;

//End expressions

/** This exists so that when suggesting names we can restrict only to certain name spaces. */
variableRef: identifier;
propertyAccess: DOT identifier;
/** With this rule we cover IDENTIFIER tokens, as well as other tokens (keywords) that we accept as identifiers as well. */
identifier: IDENTIFIER |
    AS | BY | CONCEPT | COVERED | CUBE | DICTIONARY | DIMENSIONS | FALSE | NETWORK | ROLE | START | STOP | TAXONOMY |
    TRUE | WHEN | WHERE;
literal: stringLiteral | NUMBER | booleanLiteral;
booleanLiteral: TRUE | FALSE;
stringLiteral: DOUBLE_QUOTED_STRING | SINGLE_QUOTED_STRING;