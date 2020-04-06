parser grammar XULEParser;

options { tokenVocab=XULELexer; }

xuleFile: (constantDeclaration | assertion | output | namespaceDeclaration)* EOF;

namespaceDeclaration: NAMESPACE identifier ASSIGN URL;

output: OUTPUT accessor (OPEN_BRACKET AT identifier CLOSE_BRACKET)?
    (constantDeclaration | assignment)*
    expression
    (MESSAGE expression)?;

assertion: ASSERT ASSERT_RULE_NAME (ASSERT_SATISFIED | ASSERT_UNSATISFIED)
    (constantDeclaration | assignment)*
    expression
    MESSAGE
    expression
    SEVERITY
    expression;

constantDeclaration: CONSTANT identifier ASSIGN expression;
/*functionDeclaration: TODO;*/
assignment: identifier ASSIGN expression ';';

expression:
    OPEN_PAREN expression CLOSE_PAREN |
    IF expression expression ELSE expression |
    expression AND expression |
    expression OR expression |
    expression (EQUALS | NOT_EQUALS | GREATER_THAN | LESS_THAN) expression |
    expression (PLUS | MINUS) expression |
    expression (TIMES | DIV) expression |
    expression IN expression |
    expression DOT accessor OPEN_PAREN expression CLOSE_PAREN |
    expression OPEN_BRACKET stringLiteral CLOSE_BRACKET |
    accessor OPEN_PAREN expression CLOSE_PAREN |
    literal | accessor | factset | filter;

factset: AT | (OPEN_CURLY aspectFilter* CLOSE_CURLY | OPEN_BRACKET aspectFilter* CLOSE_BRACKET) (SHARP identifier)?;
aspectFilter: AT conceptFilter?;
conceptFilter: (CONCEPT ASSIGN)? expression | accessor ASSIGN expression;

filter: FILTER expression
    (WHERE assignment* expression)?
    (RETURNS expression)?;


/** With this rule we cover IDENTIFIER tokens, as well as other tokens (keywords) that we accept as identifiers as well. */
identifier: IDENTIFIER | PERIOD;
accessor: identifier | ACCESSOR | CONCEPT DOT accessor;
literal: stringLiteral | NUMBER | booleanLiteral;
dataType: identifier COLON identifier;
booleanLiteral: TRUE | FALSE;
stringLiteral: DOUBLE_QUOTED_STRING | SINGLE_QUOTED_STRING;