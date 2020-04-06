// Generated from XULEParser.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');
var XULEParserListener = require('./XULEParserListener').XULEParserListener;
var grammarFileName = "XULEParser.g4";


var serializedATN = ["\u0003\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964",
    "\u0003D\u011f\u0004\u0002\t\u0002\u0004\u0003\t\u0003\u0004\u0004\t",
    "\u0004\u0004\u0005\t\u0005\u0004\u0006\t\u0006\u0004\u0007\t\u0007\u0004",
    "\b\t\b\u0004\t\t\t\u0004\n\t\n\u0004\u000b\t\u000b\u0004\f\t\f\u0004",
    "\r\t\r\u0004\u000e\t\u000e\u0004\u000f\t\u000f\u0004\u0010\t\u0010\u0004",
    "\u0011\t\u0011\u0004\u0012\t\u0012\u0004\u0013\t\u0013\u0004\u0014\t",
    "\u0014\u0004\u0015\t\u0015\u0003\u0002\u0003\u0002\u0003\u0002\u0007",
    "\u0002.\n\u0002\f\u0002\u000e\u00021\u000b\u0002\u0003\u0002\u0003\u0002",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0005\u00038\n\u0003\u0003\u0004",
    "\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0005\u0003\u0005",
    "\u0003\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0005\u0005",
    "F\n\u0005\u0003\u0005\u0003\u0005\u0007\u0005J\n\u0005\f\u0005\u000e",
    "\u0005M\u000b\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0005\u0005",
    "R\n\u0005\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006",
    "\u0007\u0006Y\n\u0006\f\u0006\u000e\u0006\\\u000b\u0006\u0003\u0006",
    "\u0003\u0006\u0003\u0006\u0005\u0006a\n\u0006\u0003\u0006\u0003\u0006",
    "\u0005\u0006e\n\u0006\u0003\u0007\u0003\u0007\u0003\u0007\u0003\u0007",
    "\u0003\u0007\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0007\b",
    "r\n\b\f\b\u000e\bu\u000b\b\u0003\b\u0003\b\u0007\by\n\b\f\b\u000e\b",
    "|\u000b\b\u0003\b\u0003\b\u0003\t\u0003\t\u0003\t\u0003\t\u0003\t\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0005",
    "\n\u0097\n\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n",
    "\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0007\n\u00bc\n\n\f\n\u000e\n\u00bf\u000b\n\u0003\u000b\u0003",
    "\u000b\u0003\u000b\u0003\u000b\u0007\u000b\u00c5\n\u000b\f\u000b\u000e",
    "\u000b\u00c8\u000b\u000b\u0005\u000b\u00ca\n\u000b\u0003\u000b\u0003",
    "\u000b\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0007",
    "\f\u00d5\n\f\f\f\u000e\f\u00d8\u000b\f\u0003\f\u0005\f\u00db\n\f\u0003",
    "\r\u0007\r\u00de\n\r\f\r\u000e\r\u00e1\u000b\r\u0003\u000e\u0003\u000e",
    "\u0003\u000e\u0005\u000e\u00e6\n\u000e\u0003\u000e\u0003\u000e\u0005",
    "\u000e\u00ea\n\u000e\u0003\u000e\u0003\u000e\u0003\u000e\u0003\u000e",
    "\u0003\u000e\u0005\u000e\u00f1\n\u000e\u0003\u000e\u0003\u000e\u0005",
    "\u000e\u00f5\n\u000e\u0005\u000e\u00f7\n\u000e\u0003\u000f\u0003\u000f",
    "\u0003\u000f\u0003\u000f\u0007\u000f\u00fd\n\u000f\f\u000f\u000e\u000f",
    "\u0100\u000b\u000f\u0003\u000f\u0005\u000f\u0103\n\u000f\u0003\u000f",
    "\u0003\u000f\u0005\u000f\u0107\n\u000f\u0003\u0010\u0003\u0010\u0003",
    "\u0011\u0003\u0011\u0003\u0011\u0003\u0011\u0003\u0011\u0005\u0011\u0110",
    "\n\u0011\u0003\u0012\u0003\u0012\u0003\u0012\u0005\u0012\u0115\n\u0012",
    "\u0003\u0013\u0003\u0013\u0003\u0013\u0003\u0013\u0003\u0014\u0003\u0014",
    "\u0003\u0015\u0003\u0015\u0003\u0015\u0002\u0003\u0012\u0016\u0002\u0004",
    "\u0006\b\n\f\u000e\u0010\u0012\u0014\u0016\u0018\u001a\u001c\u001e ",
    "\"$&(\u0002\t\u0003\u0002AB\u0004\u0002\u000b\f\u0011\u0012\u0003\u0002",
    "\u0014\u0015\u0003\u0002\u0016\u0017\u0004\u0002!!==\u0003\u000289\u0003",
    "\u0002\u001a\u001b\u0002\u013b\u0002/\u0003\u0002\u0002\u0002\u0004",
    "7\u0003\u0002\u0002\u0002\u00069\u0003\u0002\u0002\u0002\b>\u0003\u0002",
    "\u0002\u0002\nS\u0003\u0002\u0002\u0002\ff\u0003\u0002\u0002\u0002\u000e",
    "k\u0003\u0002\u0002\u0002\u0010\u007f\u0003\u0002\u0002\u0002\u0012",
    "\u0096\u0003\u0002\u0002\u0002\u0014\u00c0\u0003\u0002\u0002\u0002\u0016",
    "\u00da\u0003\u0002\u0002\u0002\u0018\u00df\u0003\u0002\u0002\u0002\u001a",
    "\u00f6\u0003\u0002\u0002\u0002\u001c\u00f8\u0003\u0002\u0002\u0002\u001e",
    "\u0108\u0003\u0002\u0002\u0002 \u010f\u0003\u0002\u0002\u0002\"\u0114",
    "\u0003\u0002\u0002\u0002$\u0116\u0003\u0002\u0002\u0002&\u011a\u0003",
    "\u0002\u0002\u0002(\u011c\u0003\u0002\u0002\u0002*.\u0005\u0004\u0003",
    "\u0002+.\u0005\n\u0006\u0002,.\u0005\b\u0005\u0002-*\u0003\u0002\u0002",
    "\u0002-+\u0003\u0002\u0002\u0002-,\u0003\u0002\u0002\u0002.1\u0003\u0002",
    "\u0002\u0002/-\u0003\u0002\u0002\u0002/0\u0003\u0002\u0002\u000202\u0003",
    "\u0002\u0002\u00021/\u0003\u0002\u0002\u000223\u0007\u0002\u0002\u0003",
    "3\u0003\u0003\u0002\u0002\u000248\u0005\u0006\u0004\u000258\u0005\f",
    "\u0007\u000268\u0005\u000e\b\u000274\u0003\u0002\u0002\u000275\u0003",
    "\u0002\u0002\u000276\u0003\u0002\u0002\u00028\u0005\u0003\u0002\u0002",
    "\u00029:\u0007&\u0002\u0002:;\u0005\u001e\u0010\u0002;<\u0007\r\u0002",
    "\u0002<=\u0007\u001d\u0002\u0002=\u0007\u0003\u0002\u0002\u0002>?\u0007",
    "\"\u0002\u0002?E\u0005 \u0011\u0002@A\u0007\u0004\u0002\u0002AB\u0007",
    "\n\u0002\u0002BC\u0005\u001e\u0010\u0002CD\u0007\u0005\u0002\u0002D",
    "F\u0003\u0002\u0002\u0002E@\u0003\u0002\u0002\u0002EF\u0003\u0002\u0002",
    "\u0002FK\u0003\u0002\u0002\u0002GJ\u0005\f\u0007\u0002HJ\u0005\u0010",
    "\t\u0002IG\u0003\u0002\u0002\u0002IH\u0003\u0002\u0002\u0002JM\u0003",
    "\u0002\u0002\u0002KI\u0003\u0002\u0002\u0002KL\u0003\u0002\u0002\u0002",
    "LN\u0003\u0002\u0002\u0002MK\u0003\u0002\u0002\u0002NQ\u0005\u0012\n",
    "\u0002OP\u0007\'\u0002\u0002PR\u0005\u0012\n\u0002QO\u0003\u0002\u0002",
    "\u0002QR\u0003\u0002\u0002\u0002R\t\u0003\u0002\u0002\u0002ST\u0007",
    "5\u0002\u0002TU\u0007C\u0002\u0002UZ\t\u0002\u0002\u0002VY\u0005\f\u0007",
    "\u0002WY\u0005\u0010\t\u0002XV\u0003\u0002\u0002\u0002XW\u0003\u0002",
    "\u0002\u0002Y\\\u0003\u0002\u0002\u0002ZX\u0003\u0002\u0002\u0002Z[",
    "\u0003\u0002\u0002\u0002[]\u0003\u0002\u0002\u0002\\Z\u0003\u0002\u0002",
    "\u0002]`\u0005\u0012\n\u0002^_\u0007\'\u0002\u0002_a\u0005\u0012\n\u0002",
    "`^\u0003\u0002\u0002\u0002`a\u0003\u0002\u0002\u0002ad\u0003\u0002\u0002",
    "\u0002bc\u0007\u001f\u0002\u0002ce\u0005\u0012\n\u0002db\u0003\u0002",
    "\u0002\u0002de\u0003\u0002\u0002\u0002e\u000b\u0003\u0002\u0002\u0002",
    "fg\u00073\u0002\u0002gh\u0005\u001e\u0010\u0002hi\u0007\r\u0002\u0002",
    "ij\u0005\u0012\n\u0002j\r\u0003\u0002\u0002\u0002kl\u0007+\u0002\u0002",
    "lm\u0005\u001e\u0010\u0002mn\u0007\u0006\u0002\u0002ns\u0005\u001e\u0010",
    "\u0002op\u0007\u0019\u0002\u0002pr\u0005\u001e\u0010\u0002qo\u0003\u0002",
    "\u0002\u0002ru\u0003\u0002\u0002\u0002sq\u0003\u0002\u0002\u0002st\u0003",
    "\u0002\u0002\u0002tv\u0003\u0002\u0002\u0002us\u0003\u0002\u0002\u0002",
    "vz\u0007\u0007\u0002\u0002wy\u0005\u0010\t\u0002xw\u0003\u0002\u0002",
    "\u0002y|\u0003\u0002\u0002\u0002zx\u0003\u0002\u0002\u0002z{\u0003\u0002",
    "\u0002\u0002{}\u0003\u0002\u0002\u0002|z\u0003\u0002\u0002\u0002}~\u0005",
    "\u0012\n\u0002~\u000f\u0003\u0002\u0002\u0002\u007f\u0080\u0005\u001e",
    "\u0010\u0002\u0080\u0081\u0007\r\u0002\u0002\u0081\u0082\u0005\u0012",
    "\n\u0002\u0082\u0083\u0007\u0010\u0002\u0002\u0083\u0011\u0003\u0002",
    "\u0002\u0002\u0084\u0085\b\n\u0001\u0002\u0085\u0086\u0007\u0006\u0002",
    "\u0002\u0086\u0087\u0005\u0012\n\u0002\u0087\u0088\u0007\u0007\u0002",
    "\u0002\u0088\u0097\u0003\u0002\u0002\u0002\u0089\u008a\u0007*\u0002",
    "\u0002\u008a\u008b\u0005\u0012\n\u0002\u008b\u008c\u0005\u0012\n\u0002",
    "\u008c\u008d\u0007.\u0002\u0002\u008d\u008e\u0005\u0012\n\u0011\u008e",
    "\u0097\u0003\u0002\u0002\u0002\u008f\u0090\u0005 \u0011\u0002\u0090",
    "\u0091\u0005\u0014\u000b\u0002\u0091\u0097\u0003\u0002\u0002\u0002\u0092",
    "\u0097\u0005\"\u0012\u0002\u0093\u0097\u0005 \u0011\u0002\u0094\u0097",
    "\u0005\u0016\f\u0002\u0095\u0097\u0005\u001c\u000f\u0002\u0096\u0084",
    "\u0003\u0002\u0002\u0002\u0096\u0089\u0003\u0002\u0002\u0002\u0096\u008f",
    "\u0003\u0002\u0002\u0002\u0096\u0092\u0003\u0002\u0002\u0002\u0096\u0093",
    "\u0003\u0002\u0002\u0002\u0096\u0094\u0003\u0002\u0002\u0002\u0096\u0095",
    "\u0003\u0002\u0002\u0002\u0097\u00bd\u0003\u0002\u0002\u0002\u0098\u0099",
    "\f\u0010\u0002\u0002\u0099\u009a\u00077\u0002\u0002\u009a\u00bc\u0005",
    "\u0012\n\u0011\u009b\u009c\f\u000f\u0002\u0002\u009c\u009d\u0007#\u0002",
    "\u0002\u009d\u00bc\u0005\u0012\n\u0010\u009e\u009f\f\u000e\u0002\u0002",
    "\u009f\u00a0\t\u0003\u0002\u0002\u00a0\u00bc\u0005\u0012\n\u000f\u00a1",
    "\u00a2\f\r\u0002\u0002\u00a2\u00a3\u0007$\u0002\u0002\u00a3\u00a4\u0007",
    ")\u0002\u0002\u00a4\u00bc\u0005\u0012\n\u000e\u00a5\u00a6\f\f\u0002",
    "\u0002\u00a6\u00a7\t\u0004\u0002\u0002\u00a7\u00bc\u0005\u0012\n\r\u00a8",
    "\u00a9\f\u000b\u0002\u0002\u00a9\u00aa\t\u0005\u0002\u0002\u00aa\u00bc",
    "\u0005\u0012\n\f\u00ab\u00ac\f\n\u0002\u0002\u00ac\u00ad\u0007\u0013",
    "\u0002\u0002\u00ad\u00bc\u0005\u0012\n\u000b\u00ae\u00af\f\u0013\u0002",
    "\u0002\u00af\u00b0\u0007\u0018\u0002\u0002\u00b0\u00bc\u0005\u001e\u0010",
    "\u0002\u00b1\u00b2\f\t\u0002\u0002\u00b2\u00b3\u0007\u000e\u0002\u0002",
    "\u00b3\u00b4\u0005 \u0011\u0002\u00b4\u00b5\u0005\u0014\u000b\u0002",
    "\u00b5\u00bc\u0003\u0002\u0002\u0002\u00b6\u00b7\f\b\u0002\u0002\u00b7",
    "\u00b8\u0007\u0004\u0002\u0002\u00b8\u00b9\u0005(\u0015\u0002\u00b9",
    "\u00ba\u0007\u0005\u0002\u0002\u00ba\u00bc\u0003\u0002\u0002\u0002\u00bb",
    "\u0098\u0003\u0002\u0002\u0002\u00bb\u009b\u0003\u0002\u0002\u0002\u00bb",
    "\u009e\u0003\u0002\u0002\u0002\u00bb\u00a1\u0003\u0002\u0002\u0002\u00bb",
    "\u00a5\u0003\u0002\u0002\u0002\u00bb\u00a8\u0003\u0002\u0002\u0002\u00bb",
    "\u00ab\u0003\u0002\u0002\u0002\u00bb\u00ae\u0003\u0002\u0002\u0002\u00bb",
    "\u00b1\u0003\u0002\u0002\u0002\u00bb\u00b6\u0003\u0002\u0002\u0002\u00bc",
    "\u00bf\u0003\u0002\u0002\u0002\u00bd\u00bb\u0003\u0002\u0002\u0002\u00bd",
    "\u00be\u0003\u0002\u0002\u0002\u00be\u0013\u0003\u0002\u0002\u0002\u00bf",
    "\u00bd\u0003\u0002\u0002\u0002\u00c0\u00c9\u0007\u0006\u0002\u0002\u00c1",
    "\u00c6\u0005\u0012\n\u0002\u00c2\u00c3\u0007\u0019\u0002\u0002\u00c3",
    "\u00c5\u0005\u0012\n\u0002\u00c4\u00c2\u0003\u0002\u0002\u0002\u00c5",
    "\u00c8\u0003\u0002\u0002\u0002\u00c6\u00c4\u0003\u0002\u0002\u0002\u00c6",
    "\u00c7\u0003\u0002\u0002\u0002\u00c7\u00ca\u0003\u0002\u0002\u0002\u00c8",
    "\u00c6\u0003\u0002\u0002\u0002\u00c9\u00c1\u0003\u0002\u0002\u0002\u00c9",
    "\u00ca\u0003\u0002\u0002\u0002\u00ca\u00cb\u0003\u0002\u0002\u0002\u00cb",
    "\u00cc\u0007\u0007\u0002\u0002\u00cc\u0015\u0003\u0002\u0002\u0002\u00cd",
    "\u00db\u0005\u0018\r\u0002\u00ce\u00cf\u0007\b\u0002\u0002\u00cf\u00d0",
    "\u0005\u0018\r\u0002\u00d0\u00d1\u0007\t\u0002\u0002\u00d1\u00db\u0003",
    "\u0002\u0002\u0002\u00d2\u00d6\u0007\u0004\u0002\u0002\u00d3\u00d5\u0005",
    "\u001a\u000e\u0002\u00d4\u00d3\u0003\u0002\u0002\u0002\u00d5\u00d8\u0003",
    "\u0002\u0002\u0002\u00d6\u00d4\u0003\u0002\u0002\u0002\u00d6\u00d7\u0003",
    "\u0002\u0002\u0002\u00d7\u00d9\u0003\u0002\u0002\u0002\u00d8\u00d6\u0003",
    "\u0002\u0002\u0002\u00d9\u00db\u0007\u0005\u0002\u0002\u00da\u00cd\u0003",
    "\u0002\u0002\u0002\u00da\u00ce\u0003\u0002\u0002\u0002\u00da\u00d2\u0003",
    "\u0002\u0002\u0002\u00db\u0017\u0003\u0002\u0002\u0002\u00dc\u00de\u0005",
    "\u001a\u000e\u0002\u00dd\u00dc\u0003\u0002\u0002\u0002\u00de\u00e1\u0003",
    "\u0002\u0002\u0002\u00df\u00dd\u0003\u0002\u0002\u0002\u00df\u00e0\u0003",
    "\u0002\u0002\u0002\u00e0\u0019\u0003\u0002\u0002\u0002\u00e1\u00df\u0003",
    "\u0002\u0002\u0002\u00e2\u00f7\u0007\n\u0002\u0002\u00e3\u00e5\u0007",
    "\n\u0002\u0002\u00e4\u00e6\u0007\n\u0002\u0002\u00e5\u00e4\u0003\u0002",
    "\u0002\u0002\u00e5\u00e6\u0003\u0002\u0002\u0002\u00e6\u00f0\u0003\u0002",
    "\u0002\u0002\u00e7\u00e8\u00074\u0002\u0002\u00e8\u00ea\u0007\r\u0002",
    "\u0002\u00e9\u00e7\u0003\u0002\u0002\u0002\u00e9\u00ea\u0003\u0002\u0002",
    "\u0002\u00ea\u00eb\u0003\u0002\u0002\u0002\u00eb\u00f1\u0005\u0012\n",
    "\u0002\u00ec\u00ed\u0005 \u0011\u0002\u00ed\u00ee\u0007\r\u0002\u0002",
    "\u00ee\u00ef\u0005\u0012\n\u0002\u00ef\u00f1\u0003\u0002\u0002\u0002",
    "\u00f0\u00e9\u0003\u0002\u0002\u0002\u00f0\u00ec\u0003\u0002\u0002\u0002",
    "\u00f1\u00f4\u0003\u0002\u0002\u0002\u00f2\u00f3\u00076\u0002\u0002",
    "\u00f3\u00f5\u0005\u001e\u0010\u0002\u00f4\u00f2\u0003\u0002\u0002\u0002",
    "\u00f4\u00f5\u0003\u0002\u0002\u0002\u00f5\u00f7\u0003\u0002\u0002\u0002",
    "\u00f6\u00e2\u0003\u0002\u0002\u0002\u00f6\u00e3\u0003\u0002\u0002\u0002",
    "\u00f7\u001b\u0003\u0002\u0002\u0002\u00f8\u00f9\u0007,\u0002\u0002",
    "\u00f9\u0102\u0005\u0012\n\u0002\u00fa\u00fe\u0007\u001c\u0002\u0002",
    "\u00fb\u00fd\u0005\u0010\t\u0002\u00fc\u00fb\u0003\u0002\u0002\u0002",
    "\u00fd\u0100\u0003\u0002\u0002\u0002\u00fe\u00fc\u0003\u0002\u0002\u0002",
    "\u00fe\u00ff\u0003\u0002\u0002\u0002\u00ff\u0101\u0003\u0002\u0002\u0002",
    "\u0100\u00fe\u0003\u0002\u0002\u0002\u0101\u0103\u0005\u0012\n\u0002",
    "\u0102\u00fa\u0003\u0002\u0002\u0002\u0102\u0103\u0003\u0002\u0002\u0002",
    "\u0103\u0106\u0003\u0002\u0002\u0002\u0104\u0105\u0007 \u0002\u0002",
    "\u0105\u0107\u0005\u0012\n\u0002\u0106\u0104\u0003\u0002\u0002\u0002",
    "\u0106\u0107\u0003\u0002\u0002\u0002\u0107\u001d\u0003\u0002\u0002\u0002",
    "\u0108\u0109\t\u0006\u0002\u0002\u0109\u001f\u0003\u0002\u0002\u0002",
    "\u010a\u0110\u0005\u001e\u0010\u0002\u010b\u0110\u0007<\u0002\u0002",
    "\u010c\u010d\u00074\u0002\u0002\u010d\u010e\u0007\u000e\u0002\u0002",
    "\u010e\u0110\u0005 \u0011\u0002\u010f\u010a\u0003\u0002\u0002\u0002",
    "\u010f\u010b\u0003\u0002\u0002\u0002\u010f\u010c\u0003\u0002\u0002\u0002",
    "\u0110!\u0003\u0002\u0002\u0002\u0111\u0115\u0005(\u0015\u0002\u0112",
    "\u0115\u0007:\u0002\u0002\u0113\u0115\u0005&\u0014\u0002\u0114\u0111",
    "\u0003\u0002\u0002\u0002\u0114\u0112\u0003\u0002\u0002\u0002\u0114\u0113",
    "\u0003\u0002\u0002\u0002\u0115#\u0003\u0002\u0002\u0002\u0116\u0117",
    "\u0005\u001e\u0010\u0002\u0117\u0118\u0007\u000f\u0002\u0002\u0118\u0119",
    "\u0005\u001e\u0010\u0002\u0119%\u0003\u0002\u0002\u0002\u011a\u011b",
    "\t\u0007\u0002\u0002\u011b\'\u0003\u0002\u0002\u0002\u011c\u011d\t\b",
    "\u0002\u0002\u011d)\u0003\u0002\u0002\u0002!-/7EIKQXZ`dsz\u0096\u00bb",
    "\u00bd\u00c6\u00c9\u00d6\u00da\u00df\u00e5\u00e9\u00f0\u00f4\u00f6\u00fe",
    "\u0102\u0106\u010f\u0114"].join("");


var atn = new antlr4.atn.ATNDeserializer().deserialize(serializedATN);

var decisionsToDFA = atn.decisionToState.map( function(ds, index) { return new antlr4.dfa.DFA(ds, index); });

var sharedContextCache = new antlr4.PredictionContextCache();

var literalNames = [ null, null, "'['", "']'", "'('", "')'", "'{'", "'}'", 
                     "'@'", "'!='", "'=='", "'='", "'.'", "':'", "';'", 
                     "'>'", "'<'", "'^'", "'+'", "'-'", "'*'", "'/'", "'#'", 
                     "','" ];

var symbolicNames = [ null, "BLOCK_COMMENT", "OPEN_BRACKET", "CLOSE_BRACKET", 
                      "OPEN_PAREN", "CLOSE_PAREN", "OPEN_CURLY", "CLOSE_CURLY", 
                      "AT", "NOT_EQUALS", "EQUALS", "ASSIGN", "DOT", "COLON", 
                      "SEMI", "GREATER_THAN", "LESS_THAN", "EXP", "PLUS", 
                      "MINUS", "TIMES", "DIV", "SHARP", "COMMA", "DOUBLE_QUOTED_STRING", 
                      "SINGLE_QUOTED_STRING", "WHERE", "URL", "UNIT", "SEVERITY", 
                      "RETURNS", "PERIOD", "OUTPUT", "OR", "NOT", "NONE", 
                      "NAMESPACE", "MESSAGE", "INSTANT", "IN", "IF", "FUNCTION", 
                      "FILTER", "ENTITY", "ELSE", "DURATION", "DEBIT", "CUBE", 
                      "CREDIT", "CONSTANT", "CONCEPT", "ASSERT", "AS", "AND", 
                      "TRUE", "FALSE", "NUMBER", "INTEGER", "ACCESSOR", 
                      "IDENTIFIER", "NAME", "WS", "UNRECOGNIZED_TOKEN", 
                      "ASSERT_UNSATISFIED", "ASSERT_SATISFIED", "ASSERT_RULE_NAME", 
                      "ASSERT_WS" ];

var ruleNames =  [ "xuleFile", "declaration", "namespaceDeclaration", "output", 
                   "assertion", "constantDeclaration", "functionDeclaration", 
                   "assignment", "expression", "parametersList", "factset", 
                   "factsetBody", "aspectFilter", "filter", "identifier", 
                   "access", "literal", "dataType", "booleanLiteral", "stringLiteral" ];

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
XULEParser.EXP = 17;
XULEParser.PLUS = 18;
XULEParser.MINUS = 19;
XULEParser.TIMES = 20;
XULEParser.DIV = 21;
XULEParser.SHARP = 22;
XULEParser.COMMA = 23;
XULEParser.DOUBLE_QUOTED_STRING = 24;
XULEParser.SINGLE_QUOTED_STRING = 25;
XULEParser.WHERE = 26;
XULEParser.URL = 27;
XULEParser.UNIT = 28;
XULEParser.SEVERITY = 29;
XULEParser.RETURNS = 30;
XULEParser.PERIOD = 31;
XULEParser.OUTPUT = 32;
XULEParser.OR = 33;
XULEParser.NOT = 34;
XULEParser.NONE = 35;
XULEParser.NAMESPACE = 36;
XULEParser.MESSAGE = 37;
XULEParser.INSTANT = 38;
XULEParser.IN = 39;
XULEParser.IF = 40;
XULEParser.FUNCTION = 41;
XULEParser.FILTER = 42;
XULEParser.ENTITY = 43;
XULEParser.ELSE = 44;
XULEParser.DURATION = 45;
XULEParser.DEBIT = 46;
XULEParser.CUBE = 47;
XULEParser.CREDIT = 48;
XULEParser.CONSTANT = 49;
XULEParser.CONCEPT = 50;
XULEParser.ASSERT = 51;
XULEParser.AS = 52;
XULEParser.AND = 53;
XULEParser.TRUE = 54;
XULEParser.FALSE = 55;
XULEParser.NUMBER = 56;
XULEParser.INTEGER = 57;
XULEParser.ACCESSOR = 58;
XULEParser.IDENTIFIER = 59;
XULEParser.NAME = 60;
XULEParser.WS = 61;
XULEParser.UNRECOGNIZED_TOKEN = 62;
XULEParser.ASSERT_UNSATISFIED = 63;
XULEParser.ASSERT_SATISFIED = 64;
XULEParser.ASSERT_RULE_NAME = 65;
XULEParser.ASSERT_WS = 66;

XULEParser.RULE_xuleFile = 0;
XULEParser.RULE_declaration = 1;
XULEParser.RULE_namespaceDeclaration = 2;
XULEParser.RULE_output = 3;
XULEParser.RULE_assertion = 4;
XULEParser.RULE_constantDeclaration = 5;
XULEParser.RULE_functionDeclaration = 6;
XULEParser.RULE_assignment = 7;
XULEParser.RULE_expression = 8;
XULEParser.RULE_parametersList = 9;
XULEParser.RULE_factset = 10;
XULEParser.RULE_factsetBody = 11;
XULEParser.RULE_aspectFilter = 12;
XULEParser.RULE_filter = 13;
XULEParser.RULE_identifier = 14;
XULEParser.RULE_access = 15;
XULEParser.RULE_literal = 16;
XULEParser.RULE_dataType = 17;
XULEParser.RULE_booleanLiteral = 18;
XULEParser.RULE_stringLiteral = 19;


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

XuleFileContext.prototype.declaration = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(DeclarationContext);
    } else {
        return this.getTypedRuleContext(DeclarationContext,i);
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
        this.state = 45;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while(((((_la - 32)) & ~0x1f) == 0 && ((1 << (_la - 32)) & ((1 << (XULEParser.OUTPUT - 32)) | (1 << (XULEParser.NAMESPACE - 32)) | (1 << (XULEParser.FUNCTION - 32)) | (1 << (XULEParser.CONSTANT - 32)) | (1 << (XULEParser.ASSERT - 32)))) !== 0)) {
            this.state = 43;
            this._errHandler.sync(this);
            switch(this._input.LA(1)) {
            case XULEParser.NAMESPACE:
            case XULEParser.FUNCTION:
            case XULEParser.CONSTANT:
                this.state = 40;
                this.declaration();
                break;
            case XULEParser.ASSERT:
                this.state = 41;
                this.assertion();
                break;
            case XULEParser.OUTPUT:
                this.state = 42;
                this.output();
                break;
            default:
                throw new antlr4.error.NoViableAltException(this);
            }
            this.state = 47;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
        }
        this.state = 48;
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


function DeclarationContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_declaration;
    return this;
}

DeclarationContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
DeclarationContext.prototype.constructor = DeclarationContext;

DeclarationContext.prototype.namespaceDeclaration = function() {
    return this.getTypedRuleContext(NamespaceDeclarationContext,0);
};

DeclarationContext.prototype.constantDeclaration = function() {
    return this.getTypedRuleContext(ConstantDeclarationContext,0);
};

DeclarationContext.prototype.functionDeclaration = function() {
    return this.getTypedRuleContext(FunctionDeclarationContext,0);
};

DeclarationContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterDeclaration(this);
	}
};

DeclarationContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitDeclaration(this);
	}
};




XULEParser.DeclarationContext = DeclarationContext;

XULEParser.prototype.declaration = function() {

    var localctx = new DeclarationContext(this, this._ctx, this.state);
    this.enterRule(localctx, 2, XULEParser.RULE_declaration);
    try {
        this.state = 53;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.NAMESPACE:
            this.enterOuterAlt(localctx, 1);
            this.state = 50;
            this.namespaceDeclaration();
            break;
        case XULEParser.CONSTANT:
            this.enterOuterAlt(localctx, 2);
            this.state = 51;
            this.constantDeclaration();
            break;
        case XULEParser.FUNCTION:
            this.enterOuterAlt(localctx, 3);
            this.state = 52;
            this.functionDeclaration();
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
    this.enterRule(localctx, 4, XULEParser.RULE_namespaceDeclaration);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 55;
        this.match(XULEParser.NAMESPACE);
        this.state = 56;
        this.identifier();
        this.state = 57;
        this.match(XULEParser.ASSIGN);
        this.state = 58;
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

OutputContext.prototype.access = function() {
    return this.getTypedRuleContext(AccessContext,0);
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
    this.enterRule(localctx, 6, XULEParser.RULE_output);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 60;
        this.match(XULEParser.OUTPUT);
        this.state = 61;
        this.access();
        this.state = 67;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,3,this._ctx);
        if(la_===1) {
            this.state = 62;
            this.match(XULEParser.OPEN_BRACKET);
            this.state = 63;
            this.match(XULEParser.AT);
            this.state = 64;
            this.identifier();
            this.state = 65;
            this.match(XULEParser.CLOSE_BRACKET);

        }
        this.state = 73;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,5,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 71;
                this._errHandler.sync(this);
                switch(this._input.LA(1)) {
                case XULEParser.CONSTANT:
                    this.state = 69;
                    this.constantDeclaration();
                    break;
                case XULEParser.PERIOD:
                case XULEParser.IDENTIFIER:
                    this.state = 70;
                    this.assignment();
                    break;
                default:
                    throw new antlr4.error.NoViableAltException(this);
                } 
            }
            this.state = 75;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,5,this._ctx);
        }

        this.state = 76;
        this.expression(0);
        this.state = 79;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.MESSAGE) {
            this.state = 77;
            this.match(XULEParser.MESSAGE);
            this.state = 78;
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

AssertionContext.prototype.MESSAGE = function() {
    return this.getToken(XULEParser.MESSAGE, 0);
};

AssertionContext.prototype.SEVERITY = function() {
    return this.getToken(XULEParser.SEVERITY, 0);
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
    this.enterRule(localctx, 8, XULEParser.RULE_assertion);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 81;
        this.match(XULEParser.ASSERT);
        this.state = 82;
        this.match(XULEParser.ASSERT_RULE_NAME);
        this.state = 83;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.ASSERT_UNSATISFIED || _la===XULEParser.ASSERT_SATISFIED)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
        this.state = 88;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,8,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 86;
                this._errHandler.sync(this);
                switch(this._input.LA(1)) {
                case XULEParser.CONSTANT:
                    this.state = 84;
                    this.constantDeclaration();
                    break;
                case XULEParser.PERIOD:
                case XULEParser.IDENTIFIER:
                    this.state = 85;
                    this.assignment();
                    break;
                default:
                    throw new antlr4.error.NoViableAltException(this);
                } 
            }
            this.state = 90;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,8,this._ctx);
        }

        this.state = 91;
        this.expression(0);
        this.state = 94;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.MESSAGE) {
            this.state = 92;
            this.match(XULEParser.MESSAGE);
            this.state = 93;
            this.expression(0);
        }

        this.state = 98;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.SEVERITY) {
            this.state = 96;
            this.match(XULEParser.SEVERITY);
            this.state = 97;
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
    this.enterRule(localctx, 10, XULEParser.RULE_constantDeclaration);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 100;
        this.match(XULEParser.CONSTANT);
        this.state = 101;
        this.identifier();
        this.state = 102;
        this.match(XULEParser.ASSIGN);
        this.state = 103;
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


function FunctionDeclarationContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_functionDeclaration;
    return this;
}

FunctionDeclarationContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
FunctionDeclarationContext.prototype.constructor = FunctionDeclarationContext;

FunctionDeclarationContext.prototype.FUNCTION = function() {
    return this.getToken(XULEParser.FUNCTION, 0);
};

FunctionDeclarationContext.prototype.identifier = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(IdentifierContext);
    } else {
        return this.getTypedRuleContext(IdentifierContext,i);
    }
};

FunctionDeclarationContext.prototype.OPEN_PAREN = function() {
    return this.getToken(XULEParser.OPEN_PAREN, 0);
};

FunctionDeclarationContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(XULEParser.CLOSE_PAREN, 0);
};

FunctionDeclarationContext.prototype.expression = function() {
    return this.getTypedRuleContext(ExpressionContext,0);
};

FunctionDeclarationContext.prototype.COMMA = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.COMMA);
    } else {
        return this.getToken(XULEParser.COMMA, i);
    }
};


FunctionDeclarationContext.prototype.assignment = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AssignmentContext);
    } else {
        return this.getTypedRuleContext(AssignmentContext,i);
    }
};

FunctionDeclarationContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterFunctionDeclaration(this);
	}
};

FunctionDeclarationContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitFunctionDeclaration(this);
	}
};




XULEParser.FunctionDeclarationContext = FunctionDeclarationContext;

XULEParser.prototype.functionDeclaration = function() {

    var localctx = new FunctionDeclarationContext(this, this._ctx, this.state);
    this.enterRule(localctx, 12, XULEParser.RULE_functionDeclaration);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 105;
        this.match(XULEParser.FUNCTION);
        this.state = 106;
        this.identifier();
        this.state = 107;
        this.match(XULEParser.OPEN_PAREN);
        this.state = 108;
        this.identifier();
        this.state = 113;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while(_la===XULEParser.COMMA) {
            this.state = 109;
            this.match(XULEParser.COMMA);
            this.state = 110;
            this.identifier();
            this.state = 115;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
        }
        this.state = 116;
        this.match(XULEParser.CLOSE_PAREN);
        this.state = 120;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,12,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 117;
                this.assignment(); 
            }
            this.state = 122;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,12,this._ctx);
        }

        this.state = 123;
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
    this.enterRule(localctx, 14, XULEParser.RULE_assignment);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 125;
        this.identifier();
        this.state = 126;
        this.match(XULEParser.ASSIGN);
        this.state = 127;
        this.expression(0);
        this.state = 128;
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

ExpressionContext.prototype.access = function() {
    return this.getTypedRuleContext(AccessContext,0);
};

ExpressionContext.prototype.parametersList = function() {
    return this.getTypedRuleContext(ParametersListContext,0);
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

ExpressionContext.prototype.IN = function() {
    return this.getToken(XULEParser.IN, 0);
};

ExpressionContext.prototype.NOT = function() {
    return this.getToken(XULEParser.NOT, 0);
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

ExpressionContext.prototype.EXP = function() {
    return this.getToken(XULEParser.EXP, 0);
};

ExpressionContext.prototype.SHARP = function() {
    return this.getToken(XULEParser.SHARP, 0);
};

ExpressionContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
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
    var _startState = 16;
    this.enterRecursionRule(localctx, 16, XULEParser.RULE_expression, _p);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 148;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,13,this._ctx);
        switch(la_) {
        case 1:
            this.state = 131;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 132;
            this.expression(0);
            this.state = 133;
            this.match(XULEParser.CLOSE_PAREN);
            break;

        case 2:
            this.state = 135;
            this.match(XULEParser.IF);
            this.state = 136;
            this.expression(0);
            this.state = 137;
            this.expression(0);
            this.state = 138;
            this.match(XULEParser.ELSE);
            this.state = 139;
            this.expression(15);
            break;

        case 3:
            this.state = 141;
            this.access();
            this.state = 142;
            this.parametersList();
            break;

        case 4:
            this.state = 144;
            this.literal();
            break;

        case 5:
            this.state = 145;
            this.access();
            break;

        case 6:
            this.state = 146;
            this.factset();
            break;

        case 7:
            this.state = 147;
            this.filter();
            break;

        }
        this._ctx.stop = this._input.LT(-1);
        this.state = 187;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,15,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                if(this._parseListeners!==null) {
                    this.triggerExitRuleEvent();
                }
                _prevctx = localctx;
                this.state = 185;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,14,this._ctx);
                switch(la_) {
                case 1:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 150;
                    if (!( this.precpred(this._ctx, 14))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 14)");
                    }
                    this.state = 151;
                    this.match(XULEParser.AND);
                    this.state = 152;
                    this.expression(15);
                    break;

                case 2:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 153;
                    if (!( this.precpred(this._ctx, 13))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 13)");
                    }
                    this.state = 154;
                    this.match(XULEParser.OR);
                    this.state = 155;
                    this.expression(14);
                    break;

                case 3:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 156;
                    if (!( this.precpred(this._ctx, 12))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 12)");
                    }
                    this.state = 157;
                    _la = this._input.LA(1);
                    if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.NOT_EQUALS) | (1 << XULEParser.EQUALS) | (1 << XULEParser.GREATER_THAN) | (1 << XULEParser.LESS_THAN))) !== 0))) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 158;
                    this.expression(13);
                    break;

                case 4:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 159;
                    if (!( this.precpred(this._ctx, 11))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 11)");
                    }

                    this.state = 160;
                    this.match(XULEParser.NOT);
                    this.state = 161;
                    this.match(XULEParser.IN);
                    this.state = 162;
                    this.expression(12);
                    break;

                case 5:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 163;
                    if (!( this.precpred(this._ctx, 10))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 10)");
                    }
                    this.state = 164;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.PLUS || _la===XULEParser.MINUS)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 165;
                    this.expression(11);
                    break;

                case 6:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 166;
                    if (!( this.precpred(this._ctx, 9))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 9)");
                    }
                    this.state = 167;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.TIMES || _la===XULEParser.DIV)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 168;
                    this.expression(10);
                    break;

                case 7:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 169;
                    if (!( this.precpred(this._ctx, 8))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 8)");
                    }
                    this.state = 170;
                    this.match(XULEParser.EXP);
                    this.state = 171;
                    this.expression(9);
                    break;

                case 8:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 172;
                    if (!( this.precpred(this._ctx, 17))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 17)");
                    }
                    this.state = 173;
                    this.match(XULEParser.SHARP);
                    this.state = 174;
                    this.identifier();
                    break;

                case 9:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 175;
                    if (!( this.precpred(this._ctx, 7))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 7)");
                    }
                    this.state = 176;
                    this.match(XULEParser.DOT);
                    this.state = 177;
                    this.access();
                    this.state = 178;
                    this.parametersList();
                    break;

                case 10:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 180;
                    if (!( this.precpred(this._ctx, 6))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 6)");
                    }
                    this.state = 181;
                    this.match(XULEParser.OPEN_BRACKET);
                    this.state = 182;
                    this.stringLiteral();
                    this.state = 183;
                    this.match(XULEParser.CLOSE_BRACKET);
                    break;

                } 
            }
            this.state = 189;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,15,this._ctx);
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


function ParametersListContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_parametersList;
    return this;
}

ParametersListContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ParametersListContext.prototype.constructor = ParametersListContext;

ParametersListContext.prototype.OPEN_PAREN = function() {
    return this.getToken(XULEParser.OPEN_PAREN, 0);
};

ParametersListContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(XULEParser.CLOSE_PAREN, 0);
};

ParametersListContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

ParametersListContext.prototype.COMMA = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.COMMA);
    } else {
        return this.getToken(XULEParser.COMMA, i);
    }
};


ParametersListContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterParametersList(this);
	}
};

ParametersListContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitParametersList(this);
	}
};




XULEParser.ParametersListContext = ParametersListContext;

XULEParser.prototype.parametersList = function() {

    var localctx = new ParametersListContext(this, this._ctx, this.state);
    this.enterRule(localctx, 18, XULEParser.RULE_parametersList);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 190;
        this.match(XULEParser.OPEN_PAREN);
        this.state = 199;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,17,this._ctx);
        if(la_===1) {
            this.state = 191;
            this.expression(0);
            this.state = 196;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.COMMA) {
                this.state = 192;
                this.match(XULEParser.COMMA);
                this.state = 193;
                this.expression(0);
                this.state = 198;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }

        }
        this.state = 201;
        this.match(XULEParser.CLOSE_PAREN);
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

FactsetContext.prototype.factsetBody = function() {
    return this.getTypedRuleContext(FactsetBodyContext,0);
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
    this.enterRule(localctx, 20, XULEParser.RULE_factset);
    var _la = 0; // Token type
    try {
        this.state = 216;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,19,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 203;
            this.factsetBody();
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 204;
            this.match(XULEParser.OPEN_CURLY);
            this.state = 205;
            this.factsetBody();
            this.state = 206;
            this.match(XULEParser.CLOSE_CURLY);
            break;

        case 3:
            this.enterOuterAlt(localctx, 3);
            this.state = 208;
            this.match(XULEParser.OPEN_BRACKET);
            this.state = 212;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.AT) {
                this.state = 209;
                this.aspectFilter();
                this.state = 214;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }
            this.state = 215;
            this.match(XULEParser.CLOSE_BRACKET);
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


function FactsetBodyContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_factsetBody;
    return this;
}

FactsetBodyContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
FactsetBodyContext.prototype.constructor = FactsetBodyContext;

FactsetBodyContext.prototype.aspectFilter = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(AspectFilterContext);
    } else {
        return this.getTypedRuleContext(AspectFilterContext,i);
    }
};

FactsetBodyContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterFactsetBody(this);
	}
};

FactsetBodyContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitFactsetBody(this);
	}
};




XULEParser.FactsetBodyContext = FactsetBodyContext;

XULEParser.prototype.factsetBody = function() {

    var localctx = new FactsetBodyContext(this, this._ctx, this.state);
    this.enterRule(localctx, 22, XULEParser.RULE_factsetBody);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 221;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,20,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 218;
                this.aspectFilter(); 
            }
            this.state = 223;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,20,this._ctx);
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

AspectFilterContext.prototype.AT = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.AT);
    } else {
        return this.getToken(XULEParser.AT, i);
    }
};


AspectFilterContext.prototype.expression = function() {
    return this.getTypedRuleContext(ExpressionContext,0);
};

AspectFilterContext.prototype.access = function() {
    return this.getTypedRuleContext(AccessContext,0);
};

AspectFilterContext.prototype.ASSIGN = function() {
    return this.getToken(XULEParser.ASSIGN, 0);
};

AspectFilterContext.prototype.AS = function() {
    return this.getToken(XULEParser.AS, 0);
};

AspectFilterContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

AspectFilterContext.prototype.CONCEPT = function() {
    return this.getToken(XULEParser.CONCEPT, 0);
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
    this.enterRule(localctx, 24, XULEParser.RULE_aspectFilter);
    try {
        this.state = 244;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,25,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 224;
            this.match(XULEParser.AT);
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 225;
            this.match(XULEParser.AT);
            this.state = 227;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,21,this._ctx);
            if(la_===1) {
                this.state = 226;
                this.match(XULEParser.AT);

            }
            this.state = 238;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,23,this._ctx);
            switch(la_) {
            case 1:
                this.state = 231;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,22,this._ctx);
                if(la_===1) {
                    this.state = 229;
                    this.match(XULEParser.CONCEPT);
                    this.state = 230;
                    this.match(XULEParser.ASSIGN);

                }
                this.state = 233;
                this.expression(0);
                break;

            case 2:
                this.state = 234;
                this.access();
                this.state = 235;
                this.match(XULEParser.ASSIGN);
                this.state = 236;
                this.expression(0);
                break;

            }
            this.state = 242;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,24,this._ctx);
            if(la_===1) {
                this.state = 240;
                this.match(XULEParser.AS);
                this.state = 241;
                this.identifier();

            }
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
    this.enterRule(localctx, 26, XULEParser.RULE_filter);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 246;
        this.match(XULEParser.FILTER);
        this.state = 247;
        this.expression(0);
        this.state = 256;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,27,this._ctx);
        if(la_===1) {
            this.state = 248;
            this.match(XULEParser.WHERE);
            this.state = 252;
            this._errHandler.sync(this);
            var _alt = this._interp.adaptivePredict(this._input,26,this._ctx)
            while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
                if(_alt===1) {
                    this.state = 249;
                    this.assignment(); 
                }
                this.state = 254;
                this._errHandler.sync(this);
                _alt = this._interp.adaptivePredict(this._input,26,this._ctx);
            }

            this.state = 255;
            this.expression(0);

        }
        this.state = 260;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,28,this._ctx);
        if(la_===1) {
            this.state = 258;
            this.match(XULEParser.RETURNS);
            this.state = 259;
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
    this.enterRule(localctx, 28, XULEParser.RULE_identifier);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 262;
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


function AccessContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_access;
    return this;
}

AccessContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
AccessContext.prototype.constructor = AccessContext;

AccessContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

AccessContext.prototype.ACCESSOR = function() {
    return this.getToken(XULEParser.ACCESSOR, 0);
};

AccessContext.prototype.CONCEPT = function() {
    return this.getToken(XULEParser.CONCEPT, 0);
};

AccessContext.prototype.DOT = function() {
    return this.getToken(XULEParser.DOT, 0);
};

AccessContext.prototype.access = function() {
    return this.getTypedRuleContext(AccessContext,0);
};

AccessContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterAccess(this);
	}
};

AccessContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitAccess(this);
	}
};




XULEParser.AccessContext = AccessContext;

XULEParser.prototype.access = function() {

    var localctx = new AccessContext(this, this._ctx, this.state);
    this.enterRule(localctx, 30, XULEParser.RULE_access);
    try {
        this.state = 269;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.PERIOD:
        case XULEParser.IDENTIFIER:
            this.enterOuterAlt(localctx, 1);
            this.state = 264;
            this.identifier();
            break;
        case XULEParser.ACCESSOR:
            this.enterOuterAlt(localctx, 2);
            this.state = 265;
            this.match(XULEParser.ACCESSOR);
            break;
        case XULEParser.CONCEPT:
            this.enterOuterAlt(localctx, 3);
            this.state = 266;
            this.match(XULEParser.CONCEPT);
            this.state = 267;
            this.match(XULEParser.DOT);
            this.state = 268;
            this.access();
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
    this.enterRule(localctx, 32, XULEParser.RULE_literal);
    try {
        this.state = 274;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
            this.enterOuterAlt(localctx, 1);
            this.state = 271;
            this.stringLiteral();
            break;
        case XULEParser.NUMBER:
            this.enterOuterAlt(localctx, 2);
            this.state = 272;
            this.match(XULEParser.NUMBER);
            break;
        case XULEParser.TRUE:
        case XULEParser.FALSE:
            this.enterOuterAlt(localctx, 3);
            this.state = 273;
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
    this.enterRule(localctx, 34, XULEParser.RULE_dataType);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 276;
        this.identifier();
        this.state = 277;
        this.match(XULEParser.COLON);
        this.state = 278;
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
    this.enterRule(localctx, 36, XULEParser.RULE_booleanLiteral);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 280;
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
    this.enterRule(localctx, 38, XULEParser.RULE_stringLiteral);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 282;
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
	case 8:
			return this.expression_sempred(localctx, predIndex);
    default:
        throw "No predicate with index:" + ruleIndex;
   }
};

XULEParser.prototype.expression_sempred = function(localctx, predIndex) {
	switch(predIndex) {
		case 0:
			return this.precpred(this._ctx, 14);
		case 1:
			return this.precpred(this._ctx, 13);
		case 2:
			return this.precpred(this._ctx, 12);
		case 3:
			return this.precpred(this._ctx, 11);
		case 4:
			return this.precpred(this._ctx, 10);
		case 5:
			return this.precpred(this._ctx, 9);
		case 6:
			return this.precpred(this._ctx, 8);
		case 7:
			return this.precpred(this._ctx, 17);
		case 8:
			return this.precpred(this._ctx, 7);
		case 9:
			return this.precpred(this._ctx, 6);
		default:
			throw "No predicate with index:" + predIndex;
	}
};


exports.XULEParser = XULEParser;
