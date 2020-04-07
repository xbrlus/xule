parser grammar XULEParser;

options { tokenVocab=XULELexer; }

xuleFile: (topLevelDeclaration | assertion | output)* EOF;

topLevelDeclaration: namespaceDeclaration | constantDeclaration | functionDeclaration;

namespaceDeclaration: NAMESPACE identifier ASSIGN URL;

output: OUTPUT access (OPEN_BRACKET AT identifier CLOSE_BRACKET)?
    (constantDeclaration | assignment)*
    expression
    (MESSAGE expression SEMI?)?;

assertion: ASSERT ASSERT_RULE_NAME (ASSERT_SATISFIED | ASSERT_UNSATISFIED)
    (constantDeclaration | functionDeclaration | assignment | expression (MESSAGE expression SEMI?)? (SEVERITY expression)?)+;

constantDeclaration: CONSTANT identifier ASSIGN expression;
functionDeclaration: FUNCTION identifier OPEN_PAREN identifier (COMMA identifier)* CLOSE_PAREN
    assignment* expression;
assignment: identifier ASSIGN expression SEMI;

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
    (PLUS|MINUS|NOT) expression |
    expression DOT access parametersList? |
    access parametersList? |
    expression OPEN_BRACKET stringLiteral CLOSE_BRACKET |
    literal | factset | filter | navigation;

ifExpression: IF expression expression ELSE expression;

forExpression: FOR (OPEN_PAREN forHead CLOSE_PAREN | forHead) expression;
forHead: identifier IN expression;

parametersList: OPEN_PAREN (expression (COMMA expression)*)? CLOSE_PAREN;

factset: AT | OPEN_CURLY factsetBody CLOSE_CURLY | OPEN_BRACKET factsetBody CLOSE_BRACKET;
factsetBody: AT | aspectFilter*;
aspectFilter: AT AT? ((CONCEPT ASSIGN)? | access ASSIGN) (expression | TIMES) (AS identifier)? (WHERE expression)?;

filter: FILTER expression
    (WHERE assignment* expression)?
    (RETURNS expression)?;

navigation: NAVIGATE DIMENSIONS? arcrole=role? direction=identifier levels=INTEGER? (INCLUDE START)? (ROLE role)?
    (FROM expression)? (TAXONOMY expression)? (CUBE identifier)? (TO expression)?
    (STOP WHEN expression)?
    (WHERE expression)?
    (RETURNS ((BY NETWORK returnExpression?) | returnExpression)
        (AS DICTIONARY)?)?;

returnExpression : (expression | OPEN_PAREN expression (COMMA expression)* CLOSE_PAREN) ;
role: identifier | stringLiteral;

//End expressions

/** With this rule we cover IDENTIFIER tokens, as well as other tokens (keywords) that we accept as identifiers as well. */
identifier: IDENTIFIER | CONCEPT | PERIOD | TAXONOMY;
access: identifier | ACCESSOR | CONCEPT DOT access;
literal: stringLiteral | NUMBER | booleanLiteral;
booleanLiteral: TRUE | FALSE;
stringLiteral: DOUBLE_QUOTED_STRING | SINGLE_QUOTED_STRING;