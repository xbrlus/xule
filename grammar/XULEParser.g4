parser grammar XULEParser;

options { tokenVocab=XULELexer; }

xuleFile: (declaration | assertion | output)* EOF;

declaration: namespaceDeclaration | constantDeclaration | functionDeclaration;

namespaceDeclaration: NAMESPACE identifier ASSIGN URL;

output: OUTPUT access (OPEN_BRACKET AT identifier CLOSE_BRACKET)?
    (constantDeclaration | assignment)*
    expression
    (MESSAGE expression)?;

assertion: ASSERT ASSERT_RULE_NAME (ASSERT_SATISFIED | ASSERT_UNSATISFIED)
    (constantDeclaration | assignment)*
    expression
    (MESSAGE expression)?
    (SEVERITY expression)?;

constantDeclaration: CONSTANT identifier ASSIGN expression;
functionDeclaration: FUNCTION identifier OPEN_PAREN identifier (COMMA identifier)* CLOSE_PAREN
    assignment* expression;
assignment: identifier ASSIGN expression SEMI;

expression:
    expression SHARP identifier |
    OPEN_PAREN expression CLOSE_PAREN |
    IF expression expression ELSE expression |
    expression AND expression |
    expression OR expression |
    expression (EQUALS | NOT_EQUALS | GREATER_THAN | LESS_THAN) expression |
    expression (NOT) IN expression |
    expression (PLUS | MINUS) expression |
    expression (TIMES | DIV) expression |
    expression EXP expression |
    expression DOT access parametersList |
    expression OPEN_BRACKET stringLiteral CLOSE_BRACKET |
    access parametersList | literal | access | factset | filter;

parametersList : OPEN_PAREN (expression (COMMA expression)*)? CLOSE_PAREN ;

factset: factsetBody | OPEN_CURLY factsetBody CLOSE_CURLY | OPEN_BRACKET factsetBody CLOSE_BRACKET;
factsetBody: AT |aspectFilter*;
aspectFilter: AT AT? ((CONCEPT ASSIGN)? expression | access ASSIGN expression) (AS identifier)?;

filter: FILTER expression
    (WHERE assignment* expression)?
    (RETURNS expression)?;


/** With this rule we cover IDENTIFIER tokens, as well as other tokens (keywords) that we accept as identifiers as well. */
identifier: IDENTIFIER | PERIOD;
access: identifier | ACCESSOR | CONCEPT DOT access;
literal: stringLiteral | NUMBER | booleanLiteral;
dataType: identifier COLON identifier;
booleanLiteral: TRUE | FALSE;
stringLiteral: DOUBLE_QUOTED_STRING | SINGLE_QUOTED_STRING;