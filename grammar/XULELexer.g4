lexer grammar XULELexer;

BLOCK_COMMENT: ('/*' .*? '*/') -> skip;

OPEN_BRACKET: '[';
CLOSE_BRACKET: ']';
OPEN_PAREN: '(';
CLOSE_PAREN: ')';
OPEN_CURLY: '{';
CLOSE_CURLY: '}';
AT: '@';
NOT_EQUALS: '!=';
EQUALS: '==';
ASSIGN: '=';
DOT: '.';
COLON: ':';
SEMI: ';';
GREATER_THAN: '>';
LESS_THAN: '<';
EXP: '^';
PLUS: '+';
MINUS: '-';
TIMES: '*';
DIV: '/';
SHARP: '#';
COMMA: ',';

DOUBLE_QUOTED_STRING: '"' .*? '"';
SINGLE_QUOTED_STRING: '\'' .*? '\'';

WHERE: W H E R E;
WHEN: W H E N;

URL: 'http' ('s')? '://' (.*? '/')* .*? ('\n' | '\r');
UNIT: U N I T;

TRUE: T R U E;
TO: T O;
TAXONOMY: T A X O N O M Y;

STOP: S T O P;
START: S T A R T;
SEVERITY: S E V E R I T Y;

ROLE: R O L E;
RETURNS: R E T U R N S;

PERIOD: P E R I O D;

OUTPUT: O U T P U T;
OR: O R;

NOT: N O T;
NONE: N O N E;
NETWORK: N E T W O R K;
NAVIGATE: N A V I G A T E;
NAMESPACE: N A M E S P A C E;

MESSAGE: M E S S A G E;

INSTANT: I N S T A N T;
INCLUDE: I N C L U D E;
IN: I N;
IF: I F;

FUNCTION: F U N C T I O N;
FROM: F R O M;
FILTER: F I L T E R;
FALSE: F A L S E;

ENTITY: E N T I T Y;
ELSE: E L S E;

DURATION: D U R A T I O N;
DIMENSIONS: D I M E N S I O N S;
DICTIONARY: D I C T I O N A R Y;
DEBIT: D E B I T;

CUBE: C U B E;
CREDIT: C R E D I T;
CONSTANT: C O N S T A N T;
CONCEPT: C O N C E P T;

BY: B Y;

ASSERT: A S S E R T -> pushMode(assertMode);
AS: A S;
AND: A N D;

NUMBER: INTEGER;
INTEGER: [0-9]+;

ACCESSOR: IDENTIFIER ('.' NAME)+;
IDENTIFIER: (NAME ':')? NAME;
NAME : [$a-zA-Z] [a-zA-Z_\-0-9]*;
WS: (' ' | '\t' | '\n' | '\r') -> skip;

UNRECOGNIZED_TOKEN: .;

mode assertMode;
ASSERT_UNSATISFIED: (U N S A T I S F I E D) -> popMode;
ASSERT_SATISFIED: (S A T I S F I E D) -> popMode;
ASSERT_RULE_NAME: [a-zA-Z_\-]+ ('.' [a-zA-Z0-9_\-]+)*;
ASSERT_WS: WS -> skip;


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
