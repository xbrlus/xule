grammar XULE;

factset: '@' | '{' aspect_filter* '}' | '[' aspect_filter* ']';
aspect_filter: '@' (concept_filter)?;
concept_filter:
    (CONCEPT '=')? identifier |
    CONCEPT_LOCAL_NAME '=' localName=SINGLE_QUOTED_STRING |
    CONCEPT_PERIOD_TYPE '=' periodType=(INSTANT | DURATION) |
    CONCEPT_BALANCE '=' balance=(DEBIT | CREDIT | NONE | '*') |
    CONCEPT_ATTRIBUTE '(' IDENTIFIER ')' '=' (value | NONE | '*') |
    (CONCEPT_BASE_TYPE | CONCEPT_DATA_TYPE) '=' dataType |
    test=(CONCEPT_HAS_ENUMERATIONS | CONCEPT_IS_MONETARY | CONCEPT_IS_NUMERIC) '=' booleanValue;

/** Leave the possibility open for using some keywords as identifiers */
identifier: IDENTIFIER;
/** TODO */
value: ;
dataType: identifier ':' identifier;
booleanValue: TRUE | FALSE;

DOUBLE_QUOTED_STRING: '"' .*? '"';
SINGLE_QUOTED_STRING: '\'' .*? '\'';

CONCEPT_PERIOD_TYPE: CONCEPT '.period_type';
CONCEPT_LOCAL_NAME: CONCEPT '.local-name';
CONCEPT_IS_NUMERIC: CONCEPT '.is-numeric';
CONCEPT_IS_MONETARY: CONCEPT '.is-monetary';
CONCEPT_HAS_ENUMERATIONS: CONCEPT '.has-enumerations';
CONCEPT_DATA_TYPE: CONCEPT '.data-type';
CONCEPT_BASE_TYPE: CONCEPT '.base-type';
CONCEPT_BALANCE: CONCEPT '.balance';
CONCEPT_ATTRIBUTE: CONCEPT '.attribute';
CONCEPT: 'concept';

PERIOD_FILTER: 'period';
UNIT_FILTER: 'unit';
ENTITY_FILTER: 'entity';
CUBE_FILTER: 'cube';

INSTANT: 'instant';
DURATION: 'duration';

DEBIT: 'debit';
CREDIT: 'credit';
NONE: 'none';

TRUE: 'true';
FALSE: 'false';

IDENTIFIER: [a-zA-Z] [a-zA-Z_\-0-9]*;
WS: (' ' | '\t' | '\n' | '\r') -> skip;