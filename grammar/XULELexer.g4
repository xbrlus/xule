lexer grammar XULELexer;

tokens {
    STRING_CONTENTS
}

LINE_COMMENT: ('//' [^\n\r]*) -> channel(HIDDEN);
BLOCK_COMMENT: ('/*' .*? '*/') -> channel(HIDDEN);
WS: (' ' | '\t' | '\n' | '\r' | '\u00A0') -> channel(HIDDEN);

OPEN_BRACKET: '[';
CLOSE_BRACKET: ']';
OPEN_PAREN: '(';
CLOSE_PAREN: ')';
//Close curly pops the mode in order to return to the interpolated string, if any. So we push the default mode for it
//to have something to pop.
OPEN_CURLY: '{' -> pushMode(DEFAULT_MODE);
CLOSE_CURLY: '}' -> popMode;
AND_OP: '&';
AT: '@';
NOT_EQUALS: '!=';
EQUALS: '==';
ASSIGN: '=';
DOT: '.';
SEMI: ';';
ADD_LR: '<+>';
ADD_L: '<+';
ADD_R: '+>';
SUB_LR: '<->';
SUB_L: '<-';
SUB_R: '->';
GTE: '>=';
GT: '>';
LTE: '<=';
LT: '<';
SIMM_DIFF: '^';
PLUS: '+';
MINUS: '-';
TIMES: '*';
DIV: '/';
SHARP: '#';
COMMA: ',';

DOUBLE_QUOTE: '"' -> pushMode(doubleQuotedString);
SINGLE_QUOTE: '\'' -> pushMode(singleQuotedString);

WHERE: W H E R E;
WHEN: W H E N;

URL: 'http' ('s')? '://' ~('\n' | '\r' | ' ' | '\t')+;

TRUE: T R U E;
TO: T O;
TAXONOMY: T A X O N O M Y;

STOP: S T O P;
START: S T A R T;
SET: S E T;

RULE_NAME_PREFIX: R U L E MINUS N A M E MINUS P R E F I X;
ROLE: R O L E;
RETURNS: R E T U R N S;

OUTPUT_ATTRIBUTE: O U T P U T MINUS A T T R I B U T E;
OUTPUT: O U T P U T -> pushMode(output);
OR: O R;

NOT: N O T;
NONILS: N O N I L S;
NETWORK: N E T W O R K;
NAVIGATE: N A V I G A T E;
NAMESPACE: N A M E S P A C E;

LIST: L I S T;

INTERSECT: I N T E R S E C T;
INCLUDE: I N C L U D E;
IN: I N;
IF: I F;

FUNCTION: F U N C T I O N;
FROM: F R O M;
FOR: F O R;
FILTER: F I L T E R;
FALSE: F A L S E;

ELSE: E L S E;

DRS_ROLE: D R S MINUS R O L E;
DIMENSIONS: D I M E N S I O N S;
DICTIONARY: D I C T I O N A R Y;

CUBE: C U B E;
COVERED_DIMS: C O V E R E D MINUS D I M S;
COVERED: C O V E R E D;
CONSTANT: C O N S T A N T;
CONCEPT: C O N C E P T;

BY: B Y;

ASSERT: A S S E R T -> pushMode(assert);
AS: A S;
AND: A N D;

REAL: INTEGER DOT INTEGER;
INTEGER: [0-9]+;

/** Also cover partial/invalid identifiers because we need them for code completion. */
IDENTIFIER: (IDENTIFIER_COMPONENT ':')? IDENTIFIER_COMPONENT | IDENTIFIER_COMPONENT ':' IDENTIFIER_COMPONENT?;
IDENTIFIER_COMPONENT : [$a-zA-Z] [a-zA-Z_\-0-9]*;

UNRECOGNIZED_TOKEN: .;

mode assert;
ASSERT_UNSATISFIED: (U N S A T I S F I E D) -> popMode;
ASSERT_SATISFIED: (S A T I S F I E D) -> popMode;
ASSERT_RULE_NAME: [a-zA-Z_\-] [a-zA-Z0-9_\-.]*;
ASSERT_WS: WS -> channel(HIDDEN);

mode output;
OUTPUT_RULE_NAME: [a-zA-Z_\-] [a-zA-Z0-9_\-.]* -> popMode;
OUTPUT_WS: WS -> channel(HIDDEN);

mode doubleQuotedString;
DQS_END_QUOTE: '"' -> type(DOUBLE_QUOTE), popMode;
DQS_ESCAPE: '\\' -> channel(HIDDEN), pushMode(escape);
DQS_CURLY: '{' -> type(OPEN_CURLY), pushMode(DEFAULT_MODE);
DQS_STRING_CHAR: ~[\\{"]+ -> type(STRING_CONTENTS);

mode singleQuotedString;
SQS_END_QUOTE: '\'' -> type(SINGLE_QUOTE), popMode;
SQS_ESCAPE: '\\' -> channel(HIDDEN), pushMode(escape);
SQS_CURLY: '{' -> type(OPEN_CURLY), pushMode(DEFAULT_MODE);
SQS_STRING_CHAR: ~[\\{']+ -> type(STRING_CONTENTS);

mode escape;
ESCAPED_CHAR: . -> popMode, type(STRING_CONTENTS);

fragment A : [aA];
fragment B : [bB];
fragment C : [cC];
fragment D : [dD];
fragment E : [eE];
fragment F : [fF];
fragment G : [gG];
fragment H : [hH];
fragment I : [iI];
fragment J : [jJ];
fragment K : [kK];
fragment L : [lL];
fragment M : [mM];
fragment N : [nN];
fragment O : [oO];
fragment P : [pP];
fragment Q : [qQ];
fragment R : [rR];
fragment S : [sS];
fragment T : [tT];
fragment U : [uU];
fragment V : [vV];
fragment W : [wW];
fragment X : [xX];
fragment Y : [yY];
fragment Z : [zZ];
