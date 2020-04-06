// Generated from XULEParser.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');
var XULEParserListener = require('./XULEParserListener').XULEParserListener;
var grammarFileName = "XULEParser.g4";


var serializedATN = ["\u0003\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964",
    "\u0003?\u00eb\u0004\u0002\t\u0002\u0004\u0003\t\u0003\u0004\u0004\t",
    "\u0004\u0004\u0005\t\u0005\u0004\u0006\t\u0006\u0004\u0007\t\u0007\u0004",
    "\b\t\b\u0004\t\t\t\u0004\n\t\n\u0004\u000b\t\u000b\u0004\f\t\f\u0004",
    "\r\t\r\u0004\u000e\t\u000e\u0004\u000f\t\u000f\u0004\u0010\t\u0010\u0004",
    "\u0011\t\u0011\u0004\u0012\t\u0012\u0003\u0002\u0003\u0002\u0003\u0002",
    "\u0003\u0002\u0007\u0002)\n\u0002\f\u0002\u000e\u0002,\u000b\u0002\u0003",
    "\u0002\u0003\u0002\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003",
    "\u0004\u0003\u0004\u0005\u0004<\n\u0004\u0003\u0004\u0003\u0004\u0007",
    "\u0004@\n\u0004\f\u0004\u000e\u0004C\u000b\u0004\u0003\u0004\u0003\u0004",
    "\u0003\u0004\u0005\u0004H\n\u0004\u0003\u0005\u0003\u0005\u0003\u0005",
    "\u0003\u0005\u0003\u0005\u0007\u0005O\n\u0005\f\u0005\u000e\u0005R\u000b",
    "\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0003",
    "\u0005\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0003",
    "\u0007\u0003\u0007\u0003\u0007\u0003\u0007\u0003\u0007\u0003\b\u0003",
    "\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003",
    "\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003",
    "\b\u0005\bx\n\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003",
    "\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003",
    "\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003",
    "\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0007\b\u0098\n\b\f\b\u000e",
    "\b\u009b\u000b\b\u0003\t\u0003\t\u0003\t\u0007\t\u00a0\n\t\f\t\u000e",
    "\t\u00a3\u000b\t\u0003\t\u0003\t\u0003\t\u0007\t\u00a8\n\t\f\t\u000e",
    "\t\u00ab\u000b\t\u0003\t\u0005\t\u00ae\n\t\u0003\t\u0003\t\u0005\t\u00b2",
    "\n\t\u0005\t\u00b4\n\t\u0003\n\u0003\n\u0005\n\u00b8\n\n\u0003\u000b",
    "\u0003\u000b\u0005\u000b\u00bc\n\u000b\u0003\u000b\u0003\u000b\u0003",
    "\u000b\u0003\u000b\u0003\u000b\u0005\u000b\u00c3\n\u000b\u0003\f\u0003",
    "\f\u0003\f\u0003\f\u0007\f\u00c9\n\f\f\f\u000e\f\u00cc\u000b\f\u0003",
    "\f\u0005\f\u00cf\n\f\u0003\f\u0003\f\u0005\f\u00d3\n\f\u0003\r\u0003",
    "\r\u0003\u000e\u0003\u000e\u0003\u000e\u0003\u000e\u0003\u000e\u0005",
    "\u000e\u00dc\n\u000e\u0003\u000f\u0003\u000f\u0003\u000f\u0005\u000f",
    "\u00e1\n\u000f\u0003\u0010\u0003\u0010\u0003\u0010\u0003\u0010\u0003",
    "\u0011\u0003\u0011\u0003\u0012\u0003\u0012\u0003\u0012\u0002\u0003\u000e",
    "\u0013\u0002\u0004\u0006\b\n\f\u000e\u0010\u0012\u0014\u0016\u0018\u001a",
    "\u001c\u001e \"\u0002\t\u0003\u0002<=\u0004\u0002\u000b\f\u0011\u0012",
    "\u0003\u0002\u0013\u0014\u0003\u0002\u0015\u0016\u0004\u0002\u001f\u001f",
    "88\u0003\u000234\u0003\u0002\u0018\u0019\u0002\u0100\u0002*\u0003\u0002",
    "\u0002\u0002\u0004/\u0003\u0002\u0002\u0002\u00064\u0003\u0002\u0002",
    "\u0002\bI\u0003\u0002\u0002\u0002\nY\u0003\u0002\u0002\u0002\f^\u0003",
    "\u0002\u0002\u0002\u000ew\u0003\u0002\u0002\u0002\u0010\u00b3\u0003",
    "\u0002\u0002\u0002\u0012\u00b5\u0003\u0002\u0002\u0002\u0014\u00c2\u0003",
    "\u0002\u0002\u0002\u0016\u00c4\u0003\u0002\u0002\u0002\u0018\u00d4\u0003",
    "\u0002\u0002\u0002\u001a\u00db\u0003\u0002\u0002\u0002\u001c\u00e0\u0003",
    "\u0002\u0002\u0002\u001e\u00e2\u0003\u0002\u0002\u0002 \u00e6\u0003",
    "\u0002\u0002\u0002\"\u00e8\u0003\u0002\u0002\u0002$)\u0005\n\u0006\u0002",
    "%)\u0005\b\u0005\u0002&)\u0005\u0006\u0004\u0002\')\u0005\u0004\u0003",
    "\u0002($\u0003\u0002\u0002\u0002(%\u0003\u0002\u0002\u0002(&\u0003\u0002",
    "\u0002\u0002(\'\u0003\u0002\u0002\u0002),\u0003\u0002\u0002\u0002*(",
    "\u0003\u0002\u0002\u0002*+\u0003\u0002\u0002\u0002+-\u0003\u0002\u0002",
    "\u0002,*\u0003\u0002\u0002\u0002-.\u0007\u0002\u0002\u0003.\u0003\u0003",
    "\u0002\u0002\u0002/0\u0007#\u0002\u000201\u0005\u0018\r\u000212\u0007",
    "\r\u0002\u000223\u0007\u001b\u0002\u00023\u0005\u0003\u0002\u0002\u0002",
    "45\u0007 \u0002\u00025;\u0005\u001a\u000e\u000267\u0007\u0004\u0002",
    "\u000278\u0007\n\u0002\u000289\u0005\u0018\r\u00029:\u0007\u0005\u0002",
    "\u0002:<\u0003\u0002\u0002\u0002;6\u0003\u0002\u0002\u0002;<\u0003\u0002",
    "\u0002\u0002<A\u0003\u0002\u0002\u0002=@\u0005\n\u0006\u0002>@\u0005",
    "\f\u0007\u0002?=\u0003\u0002\u0002\u0002?>\u0003\u0002\u0002\u0002@",
    "C\u0003\u0002\u0002\u0002A?\u0003\u0002\u0002\u0002AB\u0003\u0002\u0002",
    "\u0002BD\u0003\u0002\u0002\u0002CA\u0003\u0002\u0002\u0002DG\u0005\u000e",
    "\b\u0002EF\u0007$\u0002\u0002FH\u0005\u000e\b\u0002GE\u0003\u0002\u0002",
    "\u0002GH\u0003\u0002\u0002\u0002H\u0007\u0003\u0002\u0002\u0002IJ\u0007",
    "1\u0002\u0002JK\u0007>\u0002\u0002KP\t\u0002\u0002\u0002LO\u0005\n\u0006",
    "\u0002MO\u0005\f\u0007\u0002NL\u0003\u0002\u0002\u0002NM\u0003\u0002",
    "\u0002\u0002OR\u0003\u0002\u0002\u0002PN\u0003\u0002\u0002\u0002PQ\u0003",
    "\u0002\u0002\u0002QS\u0003\u0002\u0002\u0002RP\u0003\u0002\u0002\u0002",
    "ST\u0005\u000e\b\u0002TU\u0007$\u0002\u0002UV\u0005\u000e\b\u0002VW",
    "\u0007\u001d\u0002\u0002WX\u0005\u000e\b\u0002X\t\u0003\u0002\u0002",
    "\u0002YZ\u0007/\u0002\u0002Z[\u0005\u0018\r\u0002[\\\u0007\r\u0002\u0002",
    "\\]\u0005\u000e\b\u0002]\u000b\u0003\u0002\u0002\u0002^_\u0005\u0018",
    "\r\u0002_`\u0007\r\u0002\u0002`a\u0005\u000e\b\u0002ab\u0007\u0010\u0002",
    "\u0002b\r\u0003\u0002\u0002\u0002cd\b\b\u0001\u0002de\u0007\u0006\u0002",
    "\u0002ef\u0005\u000e\b\u0002fg\u0007\u0007\u0002\u0002gx\u0003\u0002",
    "\u0002\u0002hi\u0007\'\u0002\u0002ij\u0005\u000e\b\u0002jk\u0005\u000e",
    "\b\u0002kl\u0007*\u0002\u0002lm\u0005\u000e\b\u0010mx\u0003\u0002\u0002",
    "\u0002no\u0005\u001a\u000e\u0002op\u0007\u0006\u0002\u0002pq\u0005\u000e",
    "\b\u0002qr\u0007\u0007\u0002\u0002rx\u0003\u0002\u0002\u0002sx\u0005",
    "\u001c\u000f\u0002tx\u0005\u001a\u000e\u0002ux\u0005\u0010\t\u0002v",
    "x\u0005\u0016\f\u0002wc\u0003\u0002\u0002\u0002wh\u0003\u0002\u0002",
    "\u0002wn\u0003\u0002\u0002\u0002ws\u0003\u0002\u0002\u0002wt\u0003\u0002",
    "\u0002\u0002wu\u0003\u0002\u0002\u0002wv\u0003\u0002\u0002\u0002x\u0099",
    "\u0003\u0002\u0002\u0002yz\f\u000f\u0002\u0002z{\u00072\u0002\u0002",
    "{\u0098\u0005\u000e\b\u0010|}\f\u000e\u0002\u0002}~\u0007!\u0002\u0002",
    "~\u0098\u0005\u000e\b\u000f\u007f\u0080\f\r\u0002\u0002\u0080\u0081",
    "\t\u0003\u0002\u0002\u0081\u0098\u0005\u000e\b\u000e\u0082\u0083\f\f",
    "\u0002\u0002\u0083\u0084\t\u0004\u0002\u0002\u0084\u0098\u0005\u000e",
    "\b\r\u0085\u0086\f\u000b\u0002\u0002\u0086\u0087\t\u0005\u0002\u0002",
    "\u0087\u0098\u0005\u000e\b\f\u0088\u0089\f\n\u0002\u0002\u0089\u008a",
    "\u0007&\u0002\u0002\u008a\u0098\u0005\u000e\b\u000b\u008b\u008c\f\t",
    "\u0002\u0002\u008c\u008d\u0007\u000e\u0002\u0002\u008d\u008e\u0005\u001a",
    "\u000e\u0002\u008e\u008f\u0007\u0006\u0002\u0002\u008f\u0090\u0005\u000e",
    "\b\u0002\u0090\u0091\u0007\u0007\u0002\u0002\u0091\u0098\u0003\u0002",
    "\u0002\u0002\u0092\u0093\f\b\u0002\u0002\u0093\u0094\u0007\u0004\u0002",
    "\u0002\u0094\u0095\u0005\"\u0012\u0002\u0095\u0096\u0007\u0005\u0002",
    "\u0002\u0096\u0098\u0003\u0002\u0002\u0002\u0097y\u0003\u0002\u0002",
    "\u0002\u0097|\u0003\u0002\u0002\u0002\u0097\u007f\u0003\u0002\u0002",
    "\u0002\u0097\u0082\u0003\u0002\u0002\u0002\u0097\u0085\u0003\u0002\u0002",
    "\u0002\u0097\u0088\u0003\u0002\u0002\u0002\u0097\u008b\u0003\u0002\u0002",
    "\u0002\u0097\u0092\u0003\u0002\u0002\u0002\u0098\u009b\u0003\u0002\u0002",
    "\u0002\u0099\u0097\u0003\u0002\u0002\u0002\u0099\u009a\u0003\u0002\u0002",
    "\u0002\u009a\u000f\u0003\u0002\u0002\u0002\u009b\u0099\u0003\u0002\u0002",
    "\u0002\u009c\u00b4\u0007\n\u0002\u0002\u009d\u00a1\u0007\b\u0002\u0002",
    "\u009e\u00a0\u0005\u0012\n\u0002\u009f\u009e\u0003\u0002\u0002\u0002",
    "\u00a0\u00a3\u0003\u0002\u0002\u0002\u00a1\u009f\u0003\u0002\u0002\u0002",
    "\u00a1\u00a2\u0003\u0002\u0002\u0002\u00a2\u00a4\u0003\u0002\u0002\u0002",
    "\u00a3\u00a1\u0003\u0002\u0002\u0002\u00a4\u00ae\u0007\t\u0002\u0002",
    "\u00a5\u00a9\u0007\u0004\u0002\u0002\u00a6\u00a8\u0005\u0012\n\u0002",
    "\u00a7\u00a6\u0003\u0002\u0002\u0002\u00a8\u00ab\u0003\u0002\u0002\u0002",
    "\u00a9\u00a7\u0003\u0002\u0002\u0002\u00a9\u00aa\u0003\u0002\u0002\u0002",
    "\u00aa\u00ac\u0003\u0002\u0002\u0002\u00ab\u00a9\u0003\u0002\u0002\u0002",
    "\u00ac\u00ae\u0007\u0005\u0002\u0002\u00ad\u009d\u0003\u0002\u0002\u0002",
    "\u00ad\u00a5\u0003\u0002\u0002\u0002\u00ae\u00b1\u0003\u0002\u0002\u0002",
    "\u00af\u00b0\u0007\u0017\u0002\u0002\u00b0\u00b2\u0005\u0018\r\u0002",
    "\u00b1\u00af\u0003\u0002\u0002\u0002\u00b1\u00b2\u0003\u0002\u0002\u0002",
    "\u00b2\u00b4\u0003\u0002\u0002\u0002\u00b3\u009c\u0003\u0002\u0002\u0002",
    "\u00b3\u00ad\u0003\u0002\u0002\u0002\u00b4\u0011\u0003\u0002\u0002\u0002",
    "\u00b5\u00b7\u0007\n\u0002\u0002\u00b6\u00b8\u0005\u0014\u000b\u0002",
    "\u00b7\u00b6\u0003\u0002\u0002\u0002\u00b7\u00b8\u0003\u0002\u0002\u0002",
    "\u00b8\u0013\u0003\u0002\u0002\u0002\u00b9\u00ba\u00070\u0002\u0002",
    "\u00ba\u00bc\u0007\r\u0002\u0002\u00bb\u00b9\u0003\u0002\u0002\u0002",
    "\u00bb\u00bc\u0003\u0002\u0002\u0002\u00bc\u00bd\u0003\u0002\u0002\u0002",
    "\u00bd\u00c3\u0005\u000e\b\u0002\u00be\u00bf\u0005\u001a\u000e\u0002",
    "\u00bf\u00c0\u0007\r\u0002\u0002\u00c0\u00c1\u0005\u000e\b\u0002\u00c1",
    "\u00c3\u0003\u0002\u0002\u0002\u00c2\u00bb\u0003\u0002\u0002\u0002\u00c2",
    "\u00be\u0003\u0002\u0002\u0002\u00c3\u0015\u0003\u0002\u0002\u0002\u00c4",
    "\u00c5\u0007(\u0002\u0002\u00c5\u00ce\u0005\u000e\b\u0002\u00c6\u00ca",
    "\u0007\u001a\u0002\u0002\u00c7\u00c9\u0005\f\u0007\u0002\u00c8\u00c7",
    "\u0003\u0002\u0002\u0002\u00c9\u00cc\u0003\u0002\u0002\u0002\u00ca\u00c8",
    "\u0003\u0002\u0002\u0002\u00ca\u00cb\u0003\u0002\u0002\u0002\u00cb\u00cd",
    "\u0003\u0002\u0002\u0002\u00cc\u00ca\u0003\u0002\u0002\u0002\u00cd\u00cf",
    "\u0005\u000e\b\u0002\u00ce\u00c6\u0003\u0002\u0002\u0002\u00ce\u00cf",
    "\u0003\u0002\u0002\u0002\u00cf\u00d2\u0003\u0002\u0002\u0002\u00d0\u00d1",
    "\u0007\u001e\u0002\u0002\u00d1\u00d3\u0005\u000e\b\u0002\u00d2\u00d0",
    "\u0003\u0002\u0002\u0002\u00d2\u00d3\u0003\u0002\u0002\u0002\u00d3\u0017",
    "\u0003\u0002\u0002\u0002\u00d4\u00d5\t\u0006\u0002\u0002\u00d5\u0019",
    "\u0003\u0002\u0002\u0002\u00d6\u00dc\u0005\u0018\r\u0002\u00d7\u00dc",
    "\u00077\u0002\u0002\u00d8\u00d9\u00070\u0002\u0002\u00d9\u00da\u0007",
    "\u000e\u0002\u0002\u00da\u00dc\u0005\u001a\u000e\u0002\u00db\u00d6\u0003",
    "\u0002\u0002\u0002\u00db\u00d7\u0003\u0002\u0002\u0002\u00db\u00d8\u0003",
    "\u0002\u0002\u0002\u00dc\u001b\u0003\u0002\u0002\u0002\u00dd\u00e1\u0005",
    "\"\u0012\u0002\u00de\u00e1\u00075\u0002\u0002\u00df\u00e1\u0005 \u0011",
    "\u0002\u00e0\u00dd\u0003\u0002\u0002\u0002\u00e0\u00de\u0003\u0002\u0002",
    "\u0002\u00e0\u00df\u0003\u0002\u0002\u0002\u00e1\u001d\u0003\u0002\u0002",
    "\u0002\u00e2\u00e3\u0005\u0018\r\u0002\u00e3\u00e4\u0007\u000f\u0002",
    "\u0002\u00e4\u00e5\u0005\u0018\r\u0002\u00e5\u001f\u0003\u0002\u0002",
    "\u0002\u00e6\u00e7\t\u0007\u0002\u0002\u00e7!\u0003\u0002\u0002\u0002",
    "\u00e8\u00e9\t\b\u0002\u0002\u00e9#\u0003\u0002\u0002\u0002\u001a(*",
    ";?AGNPw\u0097\u0099\u00a1\u00a9\u00ad\u00b1\u00b3\u00b7\u00bb\u00c2",
    "\u00ca\u00ce\u00d2\u00db\u00e0"].join("");


var atn = new antlr4.atn.ATNDeserializer().deserialize(serializedATN);

var decisionsToDFA = atn.decisionToState.map( function(ds, index) { return new antlr4.dfa.DFA(ds, index); });

var sharedContextCache = new antlr4.PredictionContextCache();

var literalNames = [ null, null, "'['", "']'", "'('", "')'", "'{'", "'}'", 
                     "'@'", "'!='", "'=='", "'='", "'.'", "':'", "';'", 
                     "'>'", "'<'", "'+'", "'-'", "'*'", "'/'", "'#'" ];

var symbolicNames = [ null, "BLOCK_COMMENT", "OPEN_BRACKET", "CLOSE_BRACKET", 
                      "OPEN_PAREN", "CLOSE_PAREN", "OPEN_CURLY", "CLOSE_CURLY", 
                      "AT", "NOT_EQUALS", "EQUALS", "ASSIGN", "DOT", "COLON", 
                      "SEMI", "GREATER_THAN", "LESS_THAN", "PLUS", "MINUS", 
                      "TIMES", "DIV", "SHARP", "DOUBLE_QUOTED_STRING", "SINGLE_QUOTED_STRING", 
                      "WHERE", "URL", "UNIT", "SEVERITY", "RETURNS", "PERIOD", 
                      "OUTPUT", "OR", "NONE", "NAMESPACE", "MESSAGE", "INSTANT", 
                      "IN", "IF", "FILTER", "ENTITY", "ELSE", "DURATION", 
                      "DEBIT", "CUBE", "CREDIT", "CONSTANT", "CONCEPT", 
                      "ASSERT", "AND", "TRUE", "FALSE", "NUMBER", "INTEGER", 
                      "ACCESSOR", "IDENTIFIER", "NAME", "WS", "UNRECOGNIZED_TOKEN", 
                      "ASSERT_UNSATISFIED", "ASSERT_SATISFIED", "ASSERT_RULE_NAME", 
                      "ASSERT_WS" ];

var ruleNames =  [ "xuleFile", "namespaceDeclaration", "output", "assertion", 
                   "constantDeclaration", "assignment", "expression", "factset", 
                   "aspectFilter", "conceptFilter", "filter", "identifier", 
                   "accessor", "literal", "dataType", "booleanLiteral", 
                   "stringLiteral" ];

function XULEParser (input) {
	antlr4.Parser.call(this, input);
    this._interp = new antlr4.atn.ParserATNSimulator(this, atn, decisionsToDFA, sharedContextCache);
    this.ruleNames = ruleNames;
    this.literalNames = literalNames;
    this.symbolicNames = symbolicNames;
    return this;
}

XULEParser.prototype = Object.create(antlr4.Parser.prototype);
XULEParser.prototype.constructor = XULEParser;

Object.defineProperty(XULEParser.prototype, "atn", {
	get : function() {
		return atn;
	}
});

XULEParser.EOF = antlr4.Token.EOF;
XULEParser.BLOCK_COMMENT = 1;
XULEParser.OPEN_BRACKET = 2;
XULEParser.CLOSE_BRACKET = 3;
XULEParser.OPEN_PAREN = 4;
XULEParser.CLOSE_PAREN = 5;
XULEParser.OPEN_CURLY = 6;
XULEParser.CLOSE_CURLY = 7;
XULEParser.AT = 8;
XULEParser.NOT_EQUALS = 9;
XULEParser.EQUALS = 10;
XULEParser.ASSIGN = 11;
XULEParser.DOT = 12;
XULEParser.COLON = 13;
XULEParser.SEMI = 14;
XULEParser.GREATER_THAN = 15;
XULEParser.LESS_THAN = 16;
XULEParser.PLUS = 17;
XULEParser.MINUS = 18;
XULEParser.TIMES = 19;
XULEParser.DIV = 20;
XULEParser.SHARP = 21;
XULEParser.DOUBLE_QUOTED_STRING = 22;
XULEParser.SINGLE_QUOTED_STRING = 23;
XULEParser.WHERE = 24;
XULEParser.URL = 25;
XULEParser.UNIT = 26;
XULEParser.SEVERITY = 27;
XULEParser.RETURNS = 28;
XULEParser.PERIOD = 29;
XULEParser.OUTPUT = 30;
XULEParser.OR = 31;
XULEParser.NONE = 32;
XULEParser.NAMESPACE = 33;
XULEParser.MESSAGE = 34;
XULEParser.INSTANT = 35;
XULEParser.IN = 36;
XULEParser.IF = 37;
XULEParser.FILTER = 38;
XULEParser.ENTITY = 39;
XULEParser.ELSE = 40;
XULEParser.DURATION = 41;
XULEParser.DEBIT = 42;
XULEParser.CUBE = 43;
XULEParser.CREDIT = 44;
XULEParser.CONSTANT = 45;
XULEParser.CONCEPT = 46;
XULEParser.ASSERT = 47;
XULEParser.AND = 48;
XULEParser.TRUE = 49;
XULEParser.FALSE = 50;
XULEParser.NUMBER = 51;
XULEParser.INTEGER = 52;
XULEParser.ACCESSOR = 53;
XULEParser.IDENTIFIER = 54;
XULEParser.NAME = 55;
XULEParser.WS = 56;
XULEParser.UNRECOGNIZED_TOKEN = 57;
XULEParser.ASSERT_UNSATISFIED = 58;
XULEParser.ASSERT_SATISFIED = 59;
XULEParser.ASSERT_RULE_NAME = 60;
XULEParser.ASSERT_WS = 61;

XULEParser.RULE_xuleFile = 0;
XULEParser.RULE_namespaceDeclaration = 1;
XULEParser.RULE_output = 2;
XULEParser.RULE_assertion = 3;
XULEParser.RULE_constantDeclaration = 4;
XULEParser.RULE_assignment = 5;
XULEParser.RULE_expression = 6;
XULEParser.RULE_factset = 7;
XULEParser.RULE_aspectFilter = 8;
XULEParser.RULE_conceptFilter = 9;
XULEParser.RULE_filter = 10;
XULEParser.RULE_identifier = 11;
XULEParser.RULE_accessor = 12;
XULEParser.RULE_literal = 13;
XULEParser.RULE_dataType = 14;
XULEParser.RULE_booleanLiteral = 15;
XULEParser.RULE_stringLiteral = 16;


function XuleFileContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_xuleFile;
    return this;
}

XuleFileContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
XuleFileContext.prototype.constructor = XuleFileContext;

XuleFileContext.prototype.EOF = function() {
    return this.getToken(XULEParser.EOF, 0);
};

XuleFileContext.prototype.constantDeclaration = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ConstantDeclarationContext);
    } else {
        return this.getTypedRuleContext(ConstantDeclarationContext,i);
    }
};

XuleFileContext.prototype.assertion = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AssertionContext);
    } else {
        return this.getTypedRuleContext(AssertionContext,i);
    }
};

XuleFileContext.prototype.output = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(OutputContext);
    } else {
        return this.getTypedRuleContext(OutputContext,i);
    }
};

XuleFileContext.prototype.namespaceDeclaration = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(NamespaceDeclarationContext);
    } else {
        return this.getTypedRuleContext(NamespaceDeclarationContext,i);
    }
};

XuleFileContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterXuleFile(this);
	}
};

XuleFileContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitXuleFile(this);
	}
};




XULEParser.XuleFileContext = XuleFileContext;

XULEParser.prototype.xuleFile = function() {

    var localctx = new XuleFileContext(this, this._ctx, this.state);
    this.enterRule(localctx, 0, XULEParser.RULE_xuleFile);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 40;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while(((((_la - 30)) & ~0x1f) == 0 && ((1 << (_la - 30)) & ((1 << (XULEParser.OUTPUT - 30)) | (1 << (XULEParser.NAMESPACE - 30)) | (1 << (XULEParser.CONSTANT - 30)) | (1 << (XULEParser.ASSERT - 30)))) !== 0)) {
            this.state = 38;
            this._errHandler.sync(this);
            switch(this._input.LA(1)) {
            case XULEParser.CONSTANT:
                this.state = 34;
                this.constantDeclaration();
                break;
            case XULEParser.ASSERT:
                this.state = 35;
                this.assertion();
                break;
            case XULEParser.OUTPUT:
                this.state = 36;
                this.output();
                break;
            case XULEParser.NAMESPACE:
                this.state = 37;
                this.namespaceDeclaration();
                break;
            default:
                throw new antlr4.error.NoViableAltException(this);
            }
            this.state = 42;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
        }
        this.state = 43;
        this.match(XULEParser.EOF);
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function NamespaceDeclarationContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_namespaceDeclaration;
    return this;
}

NamespaceDeclarationContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
NamespaceDeclarationContext.prototype.constructor = NamespaceDeclarationContext;

NamespaceDeclarationContext.prototype.NAMESPACE = function() {
    return this.getToken(XULEParser.NAMESPACE, 0);
};

NamespaceDeclarationContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

NamespaceDeclarationContext.prototype.ASSIGN = function() {
    return this.getToken(XULEParser.ASSIGN, 0);
};

NamespaceDeclarationContext.prototype.URL = function() {
    return this.getToken(XULEParser.URL, 0);
};

NamespaceDeclarationContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterNamespaceDeclaration(this);
	}
};

NamespaceDeclarationContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitNamespaceDeclaration(this);
	}
};




XULEParser.NamespaceDeclarationContext = NamespaceDeclarationContext;

XULEParser.prototype.namespaceDeclaration = function() {

    var localctx = new NamespaceDeclarationContext(this, this._ctx, this.state);
    this.enterRule(localctx, 2, XULEParser.RULE_namespaceDeclaration);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 45;
        this.match(XULEParser.NAMESPACE);
        this.state = 46;
        this.identifier();
        this.state = 47;
        this.match(XULEParser.ASSIGN);
        this.state = 48;
        this.match(XULEParser.URL);
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function OutputContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_output;
    return this;
}

OutputContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
OutputContext.prototype.constructor = OutputContext;

OutputContext.prototype.OUTPUT = function() {
    return this.getToken(XULEParser.OUTPUT, 0);
};

OutputContext.prototype.accessor = function() {
    return this.getTypedRuleContext(AccessorContext,0);
};

OutputContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

OutputContext.prototype.OPEN_BRACKET = function() {
    return this.getToken(XULEParser.OPEN_BRACKET, 0);
};

OutputContext.prototype.AT = function() {
    return this.getToken(XULEParser.AT, 0);
};

OutputContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

OutputContext.prototype.CLOSE_BRACKET = function() {
    return this.getToken(XULEParser.CLOSE_BRACKET, 0);
};

OutputContext.prototype.constantDeclaration = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ConstantDeclarationContext);
    } else {
        return this.getTypedRuleContext(ConstantDeclarationContext,i);
    }
};

OutputContext.prototype.assignment = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AssignmentContext);
    } else {
        return this.getTypedRuleContext(AssignmentContext,i);
    }
};

OutputContext.prototype.MESSAGE = function() {
    return this.getToken(XULEParser.MESSAGE, 0);
};

OutputContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterOutput(this);
	}
};

OutputContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitOutput(this);
	}
};




XULEParser.OutputContext = OutputContext;

XULEParser.prototype.output = function() {

    var localctx = new OutputContext(this, this._ctx, this.state);
    this.enterRule(localctx, 4, XULEParser.RULE_output);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 50;
        this.match(XULEParser.OUTPUT);
        this.state = 51;
        this.accessor();
        this.state = 57;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,2,this._ctx);
        if(la_===1) {
            this.state = 52;
            this.match(XULEParser.OPEN_BRACKET);
            this.state = 53;
            this.match(XULEParser.AT);
            this.state = 54;
            this.identifier();
            this.state = 55;
            this.match(XULEParser.CLOSE_BRACKET);

        }
        this.state = 63;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,4,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 61;
                this._errHandler.sync(this);
                switch(this._input.LA(1)) {
                case XULEParser.CONSTANT:
                    this.state = 59;
                    this.constantDeclaration();
                    break;
                case XULEParser.PERIOD:
                case XULEParser.IDENTIFIER:
                    this.state = 60;
                    this.assignment();
                    break;
                default:
                    throw new antlr4.error.NoViableAltException(this);
                } 
            }
            this.state = 65;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,4,this._ctx);
        }

        this.state = 66;
        this.expression(0);
        this.state = 69;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.MESSAGE) {
            this.state = 67;
            this.match(XULEParser.MESSAGE);
            this.state = 68;
            this.expression(0);
        }

    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function AssertionContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_assertion;
    return this;
}

AssertionContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
AssertionContext.prototype.constructor = AssertionContext;

AssertionContext.prototype.ASSERT = function() {
    return this.getToken(XULEParser.ASSERT, 0);
};

AssertionContext.prototype.ASSERT_RULE_NAME = function() {
    return this.getToken(XULEParser.ASSERT_RULE_NAME, 0);
};

AssertionContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

AssertionContext.prototype.MESSAGE = function() {
    return this.getToken(XULEParser.MESSAGE, 0);
};

AssertionContext.prototype.SEVERITY = function() {
    return this.getToken(XULEParser.SEVERITY, 0);
};

AssertionContext.prototype.ASSERT_SATISFIED = function() {
    return this.getToken(XULEParser.ASSERT_SATISFIED, 0);
};

AssertionContext.prototype.ASSERT_UNSATISFIED = function() {
    return this.getToken(XULEParser.ASSERT_UNSATISFIED, 0);
};

AssertionContext.prototype.constantDeclaration = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ConstantDeclarationContext);
    } else {
        return this.getTypedRuleContext(ConstantDeclarationContext,i);
    }
};

AssertionContext.prototype.assignment = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AssignmentContext);
    } else {
        return this.getTypedRuleContext(AssignmentContext,i);
    }
};

AssertionContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterAssertion(this);
	}
};

AssertionContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitAssertion(this);
	}
};




XULEParser.AssertionContext = AssertionContext;

XULEParser.prototype.assertion = function() {

    var localctx = new AssertionContext(this, this._ctx, this.state);
    this.enterRule(localctx, 6, XULEParser.RULE_assertion);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 71;
        this.match(XULEParser.ASSERT);
        this.state = 72;
        this.match(XULEParser.ASSERT_RULE_NAME);
        this.state = 73;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.ASSERT_UNSATISFIED || _la===XULEParser.ASSERT_SATISFIED)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
        this.state = 78;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,7,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 76;
                this._errHandler.sync(this);
                switch(this._input.LA(1)) {
                case XULEParser.CONSTANT:
                    this.state = 74;
                    this.constantDeclaration();
                    break;
                case XULEParser.PERIOD:
                case XULEParser.IDENTIFIER:
                    this.state = 75;
                    this.assignment();
                    break;
                default:
                    throw new antlr4.error.NoViableAltException(this);
                } 
            }
            this.state = 80;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,7,this._ctx);
        }

        this.state = 81;
        this.expression(0);
        this.state = 82;
        this.match(XULEParser.MESSAGE);
        this.state = 83;
        this.expression(0);
        this.state = 84;
        this.match(XULEParser.SEVERITY);
        this.state = 85;
        this.expression(0);
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function ConstantDeclarationContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_constantDeclaration;
    return this;
}

ConstantDeclarationContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ConstantDeclarationContext.prototype.constructor = ConstantDeclarationContext;

ConstantDeclarationContext.prototype.CONSTANT = function() {
    return this.getToken(XULEParser.CONSTANT, 0);
};

ConstantDeclarationContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

ConstantDeclarationContext.prototype.ASSIGN = function() {
    return this.getToken(XULEParser.ASSIGN, 0);
};

ConstantDeclarationContext.prototype.expression = function() {
    return this.getTypedRuleContext(ExpressionContext,0);
};

ConstantDeclarationContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterConstantDeclaration(this);
	}
};

ConstantDeclarationContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitConstantDeclaration(this);
	}
};




XULEParser.ConstantDeclarationContext = ConstantDeclarationContext;

XULEParser.prototype.constantDeclaration = function() {

    var localctx = new ConstantDeclarationContext(this, this._ctx, this.state);
    this.enterRule(localctx, 8, XULEParser.RULE_constantDeclaration);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 87;
        this.match(XULEParser.CONSTANT);
        this.state = 88;
        this.identifier();
        this.state = 89;
        this.match(XULEParser.ASSIGN);
        this.state = 90;
        this.expression(0);
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function AssignmentContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_assignment;
    return this;
}

AssignmentContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
AssignmentContext.prototype.constructor = AssignmentContext;

AssignmentContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

AssignmentContext.prototype.ASSIGN = function() {
    return this.getToken(XULEParser.ASSIGN, 0);
};

AssignmentContext.prototype.expression = function() {
    return this.getTypedRuleContext(ExpressionContext,0);
};

AssignmentContext.prototype.SEMI = function() {
    return this.getToken(XULEParser.SEMI, 0);
};

AssignmentContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterAssignment(this);
	}
};

AssignmentContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitAssignment(this);
	}
};




XULEParser.AssignmentContext = AssignmentContext;

XULEParser.prototype.assignment = function() {

    var localctx = new AssignmentContext(this, this._ctx, this.state);
    this.enterRule(localctx, 10, XULEParser.RULE_assignment);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 92;
        this.identifier();
        this.state = 93;
        this.match(XULEParser.ASSIGN);
        this.state = 94;
        this.expression(0);
        this.state = 95;
        this.match(XULEParser.SEMI);
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function ExpressionContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_expression;
    return this;
}

ExpressionContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ExpressionContext.prototype.constructor = ExpressionContext;

ExpressionContext.prototype.OPEN_PAREN = function() {
    return this.getToken(XULEParser.OPEN_PAREN, 0);
};

ExpressionContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

ExpressionContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(XULEParser.CLOSE_PAREN, 0);
};

ExpressionContext.prototype.IF = function() {
    return this.getToken(XULEParser.IF, 0);
};

ExpressionContext.prototype.ELSE = function() {
    return this.getToken(XULEParser.ELSE, 0);
};

ExpressionContext.prototype.accessor = function() {
    return this.getTypedRuleContext(AccessorContext,0);
};

ExpressionContext.prototype.literal = function() {
    return this.getTypedRuleContext(LiteralContext,0);
};

ExpressionContext.prototype.factset = function() {
    return this.getTypedRuleContext(FactsetContext,0);
};

ExpressionContext.prototype.filter = function() {
    return this.getTypedRuleContext(FilterContext,0);
};

ExpressionContext.prototype.AND = function() {
    return this.getToken(XULEParser.AND, 0);
};

ExpressionContext.prototype.OR = function() {
    return this.getToken(XULEParser.OR, 0);
};

ExpressionContext.prototype.EQUALS = function() {
    return this.getToken(XULEParser.EQUALS, 0);
};

ExpressionContext.prototype.NOT_EQUALS = function() {
    return this.getToken(XULEParser.NOT_EQUALS, 0);
};

ExpressionContext.prototype.GREATER_THAN = function() {
    return this.getToken(XULEParser.GREATER_THAN, 0);
};

ExpressionContext.prototype.LESS_THAN = function() {
    return this.getToken(XULEParser.LESS_THAN, 0);
};

ExpressionContext.prototype.PLUS = function() {
    return this.getToken(XULEParser.PLUS, 0);
};

ExpressionContext.prototype.MINUS = function() {
    return this.getToken(XULEParser.MINUS, 0);
};

ExpressionContext.prototype.TIMES = function() {
    return this.getToken(XULEParser.TIMES, 0);
};

ExpressionContext.prototype.DIV = function() {
    return this.getToken(XULEParser.DIV, 0);
};

ExpressionContext.prototype.IN = function() {
    return this.getToken(XULEParser.IN, 0);
};

ExpressionContext.prototype.DOT = function() {
    return this.getToken(XULEParser.DOT, 0);
};

ExpressionContext.prototype.OPEN_BRACKET = function() {
    return this.getToken(XULEParser.OPEN_BRACKET, 0);
};

ExpressionContext.prototype.stringLiteral = function() {
    return this.getTypedRuleContext(StringLiteralContext,0);
};

ExpressionContext.prototype.CLOSE_BRACKET = function() {
    return this.getToken(XULEParser.CLOSE_BRACKET, 0);
};

ExpressionContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterExpression(this);
	}
};

ExpressionContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitExpression(this);
	}
};



XULEParser.prototype.expression = function(_p) {
	if(_p===undefined) {
	    _p = 0;
	}
    var _parentctx = this._ctx;
    var _parentState = this.state;
    var localctx = new ExpressionContext(this, this._ctx, _parentState);
    var _prevctx = localctx;
    var _startState = 12;
    this.enterRecursionRule(localctx, 12, XULEParser.RULE_expression, _p);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 117;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,8,this._ctx);
        switch(la_) {
        case 1:
            this.state = 98;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 99;
            this.expression(0);
            this.state = 100;
            this.match(XULEParser.CLOSE_PAREN);
            break;

        case 2:
            this.state = 102;
            this.match(XULEParser.IF);
            this.state = 103;
            this.expression(0);
            this.state = 104;
            this.expression(0);
            this.state = 105;
            this.match(XULEParser.ELSE);
            this.state = 106;
            this.expression(14);
            break;

        case 3:
            this.state = 108;
            this.accessor();
            this.state = 109;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 110;
            this.expression(0);
            this.state = 111;
            this.match(XULEParser.CLOSE_PAREN);
            break;

        case 4:
            this.state = 113;
            this.literal();
            break;

        case 5:
            this.state = 114;
            this.accessor();
            break;

        case 6:
            this.state = 115;
            this.factset();
            break;

        case 7:
            this.state = 116;
            this.filter();
            break;

        }
        this._ctx.stop = this._input.LT(-1);
        this.state = 151;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,10,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                if(this._parseListeners!==null) {
                    this.triggerExitRuleEvent();
                }
                _prevctx = localctx;
                this.state = 149;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,9,this._ctx);
                switch(la_) {
                case 1:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 119;
                    if (!( this.precpred(this._ctx, 13))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 13)");
                    }
                    this.state = 120;
                    this.match(XULEParser.AND);
                    this.state = 121;
                    this.expression(14);
                    break;

                case 2:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 122;
                    if (!( this.precpred(this._ctx, 12))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 12)");
                    }
                    this.state = 123;
                    this.match(XULEParser.OR);
                    this.state = 124;
                    this.expression(13);
                    break;

                case 3:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 125;
                    if (!( this.precpred(this._ctx, 11))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 11)");
                    }
                    this.state = 126;
                    _la = this._input.LA(1);
                    if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.NOT_EQUALS) | (1 << XULEParser.EQUALS) | (1 << XULEParser.GREATER_THAN) | (1 << XULEParser.LESS_THAN))) !== 0))) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 127;
                    this.expression(12);
                    break;

                case 4:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 128;
                    if (!( this.precpred(this._ctx, 10))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 10)");
                    }
                    this.state = 129;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.PLUS || _la===XULEParser.MINUS)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 130;
                    this.expression(11);
                    break;

                case 5:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 131;
                    if (!( this.precpred(this._ctx, 9))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 9)");
                    }
                    this.state = 132;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.TIMES || _la===XULEParser.DIV)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 133;
                    this.expression(10);
                    break;

                case 6:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 134;
                    if (!( this.precpred(this._ctx, 8))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 8)");
                    }
                    this.state = 135;
                    this.match(XULEParser.IN);
                    this.state = 136;
                    this.expression(9);
                    break;

                case 7:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 137;
                    if (!( this.precpred(this._ctx, 7))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 7)");
                    }
                    this.state = 138;
                    this.match(XULEParser.DOT);
                    this.state = 139;
                    this.accessor();
                    this.state = 140;
                    this.match(XULEParser.OPEN_PAREN);
                    this.state = 141;
                    this.expression(0);
                    this.state = 142;
                    this.match(XULEParser.CLOSE_PAREN);
                    break;

                case 8:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 144;
                    if (!( this.precpred(this._ctx, 6))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 6)");
                    }
                    this.state = 145;
                    this.match(XULEParser.OPEN_BRACKET);
                    this.state = 146;
                    this.stringLiteral();
                    this.state = 147;
                    this.match(XULEParser.CLOSE_BRACKET);
                    break;

                } 
            }
            this.state = 153;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,10,this._ctx);
        }

    } catch( error) {
        if(error instanceof antlr4.error.RecognitionException) {
	        localctx.exception = error;
	        this._errHandler.reportError(this, error);
	        this._errHandler.recover(this, error);
	    } else {
	    	throw error;
	    }
    } finally {
        this.unrollRecursionContexts(_parentctx)
    }
    return localctx;
};


function FactsetContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_factset;
    return this;
}

FactsetContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
FactsetContext.prototype.constructor = FactsetContext;

FactsetContext.prototype.AT = function() {
    return this.getToken(XULEParser.AT, 0);
};

FactsetContext.prototype.OPEN_CURLY = function() {
    return this.getToken(XULEParser.OPEN_CURLY, 0);
};

FactsetContext.prototype.CLOSE_CURLY = function() {
    return this.getToken(XULEParser.CLOSE_CURLY, 0);
};

FactsetContext.prototype.OPEN_BRACKET = function() {
    return this.getToken(XULEParser.OPEN_BRACKET, 0);
};

FactsetContext.prototype.CLOSE_BRACKET = function() {
    return this.getToken(XULEParser.CLOSE_BRACKET, 0);
};

FactsetContext.prototype.SHARP = function() {
    return this.getToken(XULEParser.SHARP, 0);
};

FactsetContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

FactsetContext.prototype.aspectFilter = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AspectFilterContext);
    } else {
        return this.getTypedRuleContext(AspectFilterContext,i);
    }
};

FactsetContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterFactset(this);
	}
};

FactsetContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitFactset(this);
	}
};




XULEParser.FactsetContext = FactsetContext;

XULEParser.prototype.factset = function() {

    var localctx = new FactsetContext(this, this._ctx, this.state);
    this.enterRule(localctx, 14, XULEParser.RULE_factset);
    var _la = 0; // Token type
    try {
        this.state = 177;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.AT:
            this.enterOuterAlt(localctx, 1);
            this.state = 154;
            this.match(XULEParser.AT);
            break;
        case XULEParser.OPEN_BRACKET:
        case XULEParser.OPEN_CURLY:
            this.enterOuterAlt(localctx, 2);
            this.state = 171;
            this._errHandler.sync(this);
            switch(this._input.LA(1)) {
            case XULEParser.OPEN_CURLY:
                this.state = 155;
                this.match(XULEParser.OPEN_CURLY);
                this.state = 159;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
                while(_la===XULEParser.AT) {
                    this.state = 156;
                    this.aspectFilter();
                    this.state = 161;
                    this._errHandler.sync(this);
                    _la = this._input.LA(1);
                }
                this.state = 162;
                this.match(XULEParser.CLOSE_CURLY);
                break;
            case XULEParser.OPEN_BRACKET:
                this.state = 163;
                this.match(XULEParser.OPEN_BRACKET);
                this.state = 167;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
                while(_la===XULEParser.AT) {
                    this.state = 164;
                    this.aspectFilter();
                    this.state = 169;
                    this._errHandler.sync(this);
                    _la = this._input.LA(1);
                }
                this.state = 170;
                this.match(XULEParser.CLOSE_BRACKET);
                break;
            default:
                throw new antlr4.error.NoViableAltException(this);
            }
            this.state = 175;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,14,this._ctx);
            if(la_===1) {
                this.state = 173;
                this.match(XULEParser.SHARP);
                this.state = 174;
                this.identifier();

            }
            break;
        default:
            throw new antlr4.error.NoViableAltException(this);
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function AspectFilterContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_aspectFilter;
    return this;
}

AspectFilterContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
AspectFilterContext.prototype.constructor = AspectFilterContext;

AspectFilterContext.prototype.AT = function() {
    return this.getToken(XULEParser.AT, 0);
};

AspectFilterContext.prototype.conceptFilter = function() {
    return this.getTypedRuleContext(ConceptFilterContext,0);
};

AspectFilterContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterAspectFilter(this);
	}
};

AspectFilterContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitAspectFilter(this);
	}
};




XULEParser.AspectFilterContext = AspectFilterContext;

XULEParser.prototype.aspectFilter = function() {

    var localctx = new AspectFilterContext(this, this._ctx, this.state);
    this.enterRule(localctx, 16, XULEParser.RULE_aspectFilter);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 179;
        this.match(XULEParser.AT);
        this.state = 181;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,16,this._ctx);
        if(la_===1) {
            this.state = 180;
            this.conceptFilter();

        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function ConceptFilterContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_conceptFilter;
    return this;
}

ConceptFilterContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ConceptFilterContext.prototype.constructor = ConceptFilterContext;

ConceptFilterContext.prototype.expression = function() {
    return this.getTypedRuleContext(ExpressionContext,0);
};

ConceptFilterContext.prototype.CONCEPT = function() {
    return this.getToken(XULEParser.CONCEPT, 0);
};

ConceptFilterContext.prototype.ASSIGN = function() {
    return this.getToken(XULEParser.ASSIGN, 0);
};

ConceptFilterContext.prototype.accessor = function() {
    return this.getTypedRuleContext(AccessorContext,0);
};

ConceptFilterContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterConceptFilter(this);
	}
};

ConceptFilterContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitConceptFilter(this);
	}
};




XULEParser.ConceptFilterContext = ConceptFilterContext;

XULEParser.prototype.conceptFilter = function() {

    var localctx = new ConceptFilterContext(this, this._ctx, this.state);
    this.enterRule(localctx, 18, XULEParser.RULE_conceptFilter);
    try {
        this.state = 192;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,18,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 185;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,17,this._ctx);
            if(la_===1) {
                this.state = 183;
                this.match(XULEParser.CONCEPT);
                this.state = 184;
                this.match(XULEParser.ASSIGN);

            }
            this.state = 187;
            this.expression(0);
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 188;
            this.accessor();
            this.state = 189;
            this.match(XULEParser.ASSIGN);
            this.state = 190;
            this.expression(0);
            break;

        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function FilterContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_filter;
    return this;
}

FilterContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
FilterContext.prototype.constructor = FilterContext;

FilterContext.prototype.FILTER = function() {
    return this.getToken(XULEParser.FILTER, 0);
};

FilterContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

FilterContext.prototype.WHERE = function() {
    return this.getToken(XULEParser.WHERE, 0);
};

FilterContext.prototype.RETURNS = function() {
    return this.getToken(XULEParser.RETURNS, 0);
};

FilterContext.prototype.assignment = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AssignmentContext);
    } else {
        return this.getTypedRuleContext(AssignmentContext,i);
    }
};

FilterContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterFilter(this);
	}
};

FilterContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitFilter(this);
	}
};




XULEParser.FilterContext = FilterContext;

XULEParser.prototype.filter = function() {

    var localctx = new FilterContext(this, this._ctx, this.state);
    this.enterRule(localctx, 20, XULEParser.RULE_filter);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 194;
        this.match(XULEParser.FILTER);
        this.state = 195;
        this.expression(0);
        this.state = 204;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,20,this._ctx);
        if(la_===1) {
            this.state = 196;
            this.match(XULEParser.WHERE);
            this.state = 200;
            this._errHandler.sync(this);
            var _alt = this._interp.adaptivePredict(this._input,19,this._ctx)
            while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
                if(_alt===1) {
                    this.state = 197;
                    this.assignment(); 
                }
                this.state = 202;
                this._errHandler.sync(this);
                _alt = this._interp.adaptivePredict(this._input,19,this._ctx);
            }

            this.state = 203;
            this.expression(0);

        }
        this.state = 208;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,21,this._ctx);
        if(la_===1) {
            this.state = 206;
            this.match(XULEParser.RETURNS);
            this.state = 207;
            this.expression(0);

        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function IdentifierContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_identifier;
    return this;
}

IdentifierContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
IdentifierContext.prototype.constructor = IdentifierContext;

IdentifierContext.prototype.IDENTIFIER = function() {
    return this.getToken(XULEParser.IDENTIFIER, 0);
};

IdentifierContext.prototype.PERIOD = function() {
    return this.getToken(XULEParser.PERIOD, 0);
};

IdentifierContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterIdentifier(this);
	}
};

IdentifierContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitIdentifier(this);
	}
};




XULEParser.IdentifierContext = IdentifierContext;

XULEParser.prototype.identifier = function() {

    var localctx = new IdentifierContext(this, this._ctx, this.state);
    this.enterRule(localctx, 22, XULEParser.RULE_identifier);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 210;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.PERIOD || _la===XULEParser.IDENTIFIER)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function AccessorContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_accessor;
    return this;
}

AccessorContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
AccessorContext.prototype.constructor = AccessorContext;

AccessorContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

AccessorContext.prototype.ACCESSOR = function() {
    return this.getToken(XULEParser.ACCESSOR, 0);
};

AccessorContext.prototype.CONCEPT = function() {
    return this.getToken(XULEParser.CONCEPT, 0);
};

AccessorContext.prototype.DOT = function() {
    return this.getToken(XULEParser.DOT, 0);
};

AccessorContext.prototype.accessor = function() {
    return this.getTypedRuleContext(AccessorContext,0);
};

AccessorContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterAccessor(this);
	}
};

AccessorContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitAccessor(this);
	}
};




XULEParser.AccessorContext = AccessorContext;

XULEParser.prototype.accessor = function() {

    var localctx = new AccessorContext(this, this._ctx, this.state);
    this.enterRule(localctx, 24, XULEParser.RULE_accessor);
    try {
        this.state = 217;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.PERIOD:
        case XULEParser.IDENTIFIER:
            this.enterOuterAlt(localctx, 1);
            this.state = 212;
            this.identifier();
            break;
        case XULEParser.ACCESSOR:
            this.enterOuterAlt(localctx, 2);
            this.state = 213;
            this.match(XULEParser.ACCESSOR);
            break;
        case XULEParser.CONCEPT:
            this.enterOuterAlt(localctx, 3);
            this.state = 214;
            this.match(XULEParser.CONCEPT);
            this.state = 215;
            this.match(XULEParser.DOT);
            this.state = 216;
            this.accessor();
            break;
        default:
            throw new antlr4.error.NoViableAltException(this);
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function LiteralContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_literal;
    return this;
}

LiteralContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
LiteralContext.prototype.constructor = LiteralContext;

LiteralContext.prototype.stringLiteral = function() {
    return this.getTypedRuleContext(StringLiteralContext,0);
};

LiteralContext.prototype.NUMBER = function() {
    return this.getToken(XULEParser.NUMBER, 0);
};

LiteralContext.prototype.booleanLiteral = function() {
    return this.getTypedRuleContext(BooleanLiteralContext,0);
};

LiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterLiteral(this);
	}
};

LiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitLiteral(this);
	}
};




XULEParser.LiteralContext = LiteralContext;

XULEParser.prototype.literal = function() {

    var localctx = new LiteralContext(this, this._ctx, this.state);
    this.enterRule(localctx, 26, XULEParser.RULE_literal);
    try {
        this.state = 222;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
            this.enterOuterAlt(localctx, 1);
            this.state = 219;
            this.stringLiteral();
            break;
        case XULEParser.NUMBER:
            this.enterOuterAlt(localctx, 2);
            this.state = 220;
            this.match(XULEParser.NUMBER);
            break;
        case XULEParser.TRUE:
        case XULEParser.FALSE:
            this.enterOuterAlt(localctx, 3);
            this.state = 221;
            this.booleanLiteral();
            break;
        default:
            throw new antlr4.error.NoViableAltException(this);
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function DataTypeContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_dataType;
    return this;
}

DataTypeContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
DataTypeContext.prototype.constructor = DataTypeContext;

DataTypeContext.prototype.identifier = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(IdentifierContext);
    } else {
        return this.getTypedRuleContext(IdentifierContext,i);
    }
};

DataTypeContext.prototype.COLON = function() {
    return this.getToken(XULEParser.COLON, 0);
};

DataTypeContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterDataType(this);
	}
};

DataTypeContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitDataType(this);
	}
};




XULEParser.DataTypeContext = DataTypeContext;

XULEParser.prototype.dataType = function() {

    var localctx = new DataTypeContext(this, this._ctx, this.state);
    this.enterRule(localctx, 28, XULEParser.RULE_dataType);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 224;
        this.identifier();
        this.state = 225;
        this.match(XULEParser.COLON);
        this.state = 226;
        this.identifier();
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function BooleanLiteralContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_booleanLiteral;
    return this;
}

BooleanLiteralContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
BooleanLiteralContext.prototype.constructor = BooleanLiteralContext;

BooleanLiteralContext.prototype.TRUE = function() {
    return this.getToken(XULEParser.TRUE, 0);
};

BooleanLiteralContext.prototype.FALSE = function() {
    return this.getToken(XULEParser.FALSE, 0);
};

BooleanLiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterBooleanLiteral(this);
	}
};

BooleanLiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitBooleanLiteral(this);
	}
};




XULEParser.BooleanLiteralContext = BooleanLiteralContext;

XULEParser.prototype.booleanLiteral = function() {

    var localctx = new BooleanLiteralContext(this, this._ctx, this.state);
    this.enterRule(localctx, 30, XULEParser.RULE_booleanLiteral);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 228;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.TRUE || _la===XULEParser.FALSE)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function StringLiteralContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_stringLiteral;
    return this;
}

StringLiteralContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
StringLiteralContext.prototype.constructor = StringLiteralContext;

StringLiteralContext.prototype.DOUBLE_QUOTED_STRING = function() {
    return this.getToken(XULEParser.DOUBLE_QUOTED_STRING, 0);
};

StringLiteralContext.prototype.SINGLE_QUOTED_STRING = function() {
    return this.getToken(XULEParser.SINGLE_QUOTED_STRING, 0);
};

StringLiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterStringLiteral(this);
	}
};

StringLiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitStringLiteral(this);
	}
};




XULEParser.StringLiteralContext = StringLiteralContext;

XULEParser.prototype.stringLiteral = function() {

    var localctx = new StringLiteralContext(this, this._ctx, this.state);
    this.enterRule(localctx, 32, XULEParser.RULE_stringLiteral);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 230;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.DOUBLE_QUOTED_STRING || _la===XULEParser.SINGLE_QUOTED_STRING)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


XULEParser.prototype.sempred = function(localctx, ruleIndex, predIndex) {
	switch(ruleIndex) {
	case 6:
			return this.expression_sempred(localctx, predIndex);
    default:
        throw "No predicate with index:" + ruleIndex;
   }
};

XULEParser.prototype.expression_sempred = function(localctx, predIndex) {
	switch(predIndex) {
		case 0:
			return this.precpred(this._ctx, 13);
		case 1:
			return this.precpred(this._ctx, 12);
		case 2:
			return this.precpred(this._ctx, 11);
		case 3:
			return this.precpred(this._ctx, 10);
		case 4:
			return this.precpred(this._ctx, 9);
		case 5:
			return this.precpred(this._ctx, 8);
		case 6:
			return this.precpred(this._ctx, 7);
		case 7:
			return this.precpred(this._ctx, 6);
		default:
			throw "No predicate with index:" + predIndex;
	}
};


exports.XULEParser = XULEParser;
