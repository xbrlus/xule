// Generated from XULEParser.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');
var XULEParserListener = require('./XULEParserListener').XULEParserListener;
var grammarFileName = "XULEParser.g4";


var serializedATN = ["\u0003\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964",
    "\u0003Q\u0171\u0004\u0002\t\u0002\u0004\u0003\t\u0003\u0004\u0004\t",
    "\u0004\u0004\u0005\t\u0005\u0004\u0006\t\u0006\u0004\u0007\t\u0007\u0004",
    "\b\t\b\u0004\t\t\t\u0004\n\t\n\u0004\u000b\t\u000b\u0004\f\t\f\u0004",
    "\r\t\r\u0004\u000e\t\u000e\u0004\u000f\t\u000f\u0004\u0010\t\u0010\u0004",
    "\u0011\t\u0011\u0004\u0012\t\u0012\u0004\u0013\t\u0013\u0004\u0014\t",
    "\u0014\u0004\u0015\t\u0015\u0004\u0016\t\u0016\u0004\u0017\t\u0017\u0004",
    "\u0018\t\u0018\u0003\u0002\u0003\u0002\u0003\u0002\u0007\u00024\n\u0002",
    "\f\u0002\u000e\u00027\u000b\u0002\u0003\u0002\u0003\u0002\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0005\u0003>\n\u0003\u0003\u0004\u0003\u0004",
    "\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0005\u0003\u0005\u0003\u0005",
    "\u0003\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0005\u0005L\n\u0005",
    "\u0003\u0005\u0003\u0005\u0007\u0005P\n\u0005\f\u0005\u000e\u0005S\u000b",
    "\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0005\u0005X\n\u0005\u0003",
    "\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0007\u0006_",
    "\n\u0006\f\u0006\u000e\u0006b\u000b\u0006\u0003\u0006\u0003\u0006\u0003",
    "\u0006\u0005\u0006g\n\u0006\u0003\u0006\u0003\u0006\u0005\u0006k\n\u0006",
    "\u0003\u0007\u0003\u0007\u0003\u0007\u0003\u0007\u0003\u0007\u0003\b",
    "\u0003\b\u0003\b\u0003\b\u0003\b\u0003\b\u0007\bx\n\b\f\b\u000e\b{\u000b",
    "\b\u0003\b\u0003\b\u0007\b\u007f\n\b\f\b\u000e\b\u0082\u000b\b\u0003",
    "\b\u0003\b\u0003\t\u0003\t\u0003\t\u0003\t\u0003\t\u0003\n\u0003\n\u0003",
    "\n\u0005\n\u008e\n\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n",
    "\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0005",
    "\n\u009e\n\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n",
    "\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0007\n\u00c3\n\n\f\n\u000e\n\u00c6\u000b\n\u0003\u000b\u0003",
    "\u000b\u0003\u000b\u0003\u000b\u0007\u000b\u00cc\n\u000b\f\u000b\u000e",
    "\u000b\u00cf\u000b\u000b\u0005\u000b\u00d1\n\u000b\u0003\u000b\u0003",
    "\u000b\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0003",
    "\f\u0003\f\u0005\f\u00de\n\f\u0003\r\u0003\r\u0007\r\u00e2\n\r\f\r\u000e",
    "\r\u00e5\u000b\r\u0005\r\u00e7\n\r\u0003\u000e\u0003\u000e\u0005\u000e",
    "\u00eb\n\u000e\u0003\u000e\u0003\u000e\u0005\u000e\u00ef\n\u000e\u0003",
    "\u000e\u0003\u000e\u0003\u000e\u0005\u000e\u00f4\n\u000e\u0003\u000e",
    "\u0003\u000e\u0005\u000e\u00f8\n\u000e\u0003\u000e\u0003\u000e\u0005",
    "\u000e\u00fc\n\u000e\u0003\u000f\u0003\u000f\u0003\u000f\u0003\u000f",
    "\u0007\u000f\u0102\n\u000f\f\u000f\u000e\u000f\u0105\u000b\u000f\u0003",
    "\u000f\u0005\u000f\u0108\n\u000f\u0003\u000f\u0003\u000f\u0005\u000f",
    "\u010c\n\u000f\u0003\u0010\u0003\u0010\u0005\u0010\u0110\n\u0010\u0003",
    "\u0010\u0005\u0010\u0113\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010",
    "\u0117\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u011b\n\u0010\u0003",
    "\u0010\u0003\u0010\u0005\u0010\u011f\n\u0010\u0003\u0010\u0003\u0010",
    "\u0005\u0010\u0123\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u0127",
    "\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u012b\n\u0010\u0003\u0010",
    "\u0003\u0010\u0005\u0010\u012f\n\u0010\u0003\u0010\u0003\u0010\u0003",
    "\u0010\u0005\u0010\u0134\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010",
    "\u0138\n\u0010\u0003\u0010\u0003\u0010\u0003\u0010\u0003\u0010\u0005",
    "\u0010\u013e\n\u0010\u0003\u0010\u0005\u0010\u0141\n\u0010\u0003\u0010",
    "\u0003\u0010\u0005\u0010\u0145\n\u0010\u0005\u0010\u0147\n\u0010\u0003",
    "\u0011\u0003\u0011\u0003\u0011\u0003\u0011\u0003\u0011\u0007\u0011\u014e",
    "\n\u0011\f\u0011\u000e\u0011\u0151\u000b\u0011\u0003\u0011\u0003\u0011",
    "\u0005\u0011\u0155\n\u0011\u0003\u0012\u0003\u0012\u0005\u0012\u0159",
    "\n\u0012\u0003\u0013\u0003\u0013\u0003\u0014\u0003\u0014\u0003\u0014",
    "\u0003\u0014\u0003\u0014\u0005\u0014\u0162\n\u0014\u0003\u0015\u0003",
    "\u0015\u0003\u0015\u0005\u0015\u0167\n\u0015\u0003\u0016\u0003\u0016",
    "\u0003\u0016\u0003\u0016\u0003\u0017\u0003\u0017\u0003\u0018\u0003\u0018",
    "\u0003\u0018\u0002\u0003\u0012\u0019\u0002\u0004\u0006\b\n\f\u000e\u0010",
    "\u0012\u0014\u0016\u0018\u001a\u001c\u001e \"$&(*,.\u0002\t\u0003\u0002",
    "NO\u0004\u0002\u000b\f\u0011\u0012\u0003\u0002\u0014\u0015\u0003\u0002",
    "\u0016\u0017\u0006\u0002\"\"((BBJJ\u0004\u0002  88\u0003\u0002\u001a",
    "\u001b\u0002\u019d\u00025\u0003\u0002\u0002\u0002\u0004=\u0003\u0002",
    "\u0002\u0002\u0006?\u0003\u0002\u0002\u0002\bD\u0003\u0002\u0002\u0002",
    "\nY\u0003\u0002\u0002\u0002\fl\u0003\u0002\u0002\u0002\u000eq\u0003",
    "\u0002\u0002\u0002\u0010\u0085\u0003\u0002\u0002\u0002\u0012\u009d\u0003",
    "\u0002\u0002\u0002\u0014\u00c7\u0003\u0002\u0002\u0002\u0016\u00dd\u0003",
    "\u0002\u0002\u0002\u0018\u00e6\u0003\u0002\u0002\u0002\u001a\u00e8\u0003",
    "\u0002\u0002\u0002\u001c\u00fd\u0003\u0002\u0002\u0002\u001e\u010d\u0003",
    "\u0002\u0002\u0002 \u0154\u0003\u0002\u0002\u0002\"\u0158\u0003\u0002",
    "\u0002\u0002$\u015a\u0003\u0002\u0002\u0002&\u0161\u0003\u0002\u0002",
    "\u0002(\u0166\u0003\u0002\u0002\u0002*\u0168\u0003\u0002\u0002\u0002",
    ",\u016c\u0003\u0002\u0002\u0002.\u016e\u0003\u0002\u0002\u000204\u0005",
    "\u0004\u0003\u000214\u0005\n\u0006\u000224\u0005\b\u0005\u000230\u0003",
    "\u0002\u0002\u000231\u0003\u0002\u0002\u000232\u0003\u0002\u0002\u0002",
    "47\u0003\u0002\u0002\u000253\u0003\u0002\u0002\u000256\u0003\u0002\u0002",
    "\u000268\u0003\u0002\u0002\u000275\u0003\u0002\u0002\u000289\u0007\u0002",
    "\u0002\u00039\u0003\u0003\u0002\u0002\u0002:>\u0005\u0006\u0004\u0002",
    ";>\u0005\f\u0007\u0002<>\u0005\u000e\b\u0002=:\u0003\u0002\u0002\u0002",
    "=;\u0003\u0002\u0002\u0002=<\u0003\u0002\u0002\u0002>\u0005\u0003\u0002",
    "\u0002\u0002?@\u0007/\u0002\u0002@A\u0005$\u0013\u0002AB\u0007\r\u0002",
    "\u0002BC\u0007\u001e\u0002\u0002C\u0007\u0003\u0002\u0002\u0002DE\u0007",
    ")\u0002\u0002EK\u0005&\u0014\u0002FG\u0007\u0004\u0002\u0002GH\u0007",
    "\n\u0002\u0002HI\u0005$\u0013\u0002IJ\u0007\u0005\u0002\u0002JL\u0003",
    "\u0002\u0002\u0002KF\u0003\u0002\u0002\u0002KL\u0003\u0002\u0002\u0002",
    "LQ\u0003\u0002\u0002\u0002MP\u0005\f\u0007\u0002NP\u0005\u0010\t\u0002",
    "OM\u0003\u0002\u0002\u0002ON\u0003\u0002\u0002\u0002PS\u0003\u0002\u0002",
    "\u0002QO\u0003\u0002\u0002\u0002QR\u0003\u0002\u0002\u0002RT\u0003\u0002",
    "\u0002\u0002SQ\u0003\u0002\u0002\u0002TW\u0005\u0012\n\u0002UV\u0007",
    "0\u0002\u0002VX\u0005\u0012\n\u0002WU\u0003\u0002\u0002\u0002WX\u0003",
    "\u0002\u0002\u0002X\t\u0003\u0002\u0002\u0002YZ\u0007D\u0002\u0002Z",
    "[\u0007P\u0002\u0002[`\t\u0002\u0002\u0002\\_\u0005\f\u0007\u0002]_",
    "\u0005\u0010\t\u0002^\\\u0003\u0002\u0002\u0002^]\u0003\u0002\u0002",
    "\u0002_b\u0003\u0002\u0002\u0002`^\u0003\u0002\u0002\u0002`a\u0003\u0002",
    "\u0002\u0002ac\u0003\u0002\u0002\u0002b`\u0003\u0002\u0002\u0002cf\u0005",
    "\u0012\n\u0002de\u00070\u0002\u0002eg\u0005\u0012\n\u0002fd\u0003\u0002",
    "\u0002\u0002fg\u0003\u0002\u0002\u0002gj\u0003\u0002\u0002\u0002hi\u0007",
    "%\u0002\u0002ik\u0005\u0012\n\u0002jh\u0003\u0002\u0002\u0002jk\u0003",
    "\u0002\u0002\u0002k\u000b\u0003\u0002\u0002\u0002lm\u0007A\u0002\u0002",
    "mn\u0005$\u0013\u0002no\u0007\r\u0002\u0002op\u0005\u0012\n\u0002p\r",
    "\u0003\u0002\u0002\u0002qr\u00075\u0002\u0002rs\u0005$\u0013\u0002s",
    "t\u0007\u0006\u0002\u0002ty\u0005$\u0013\u0002uv\u0007\u0019\u0002\u0002",
    "vx\u0005$\u0013\u0002wu\u0003\u0002\u0002\u0002x{\u0003\u0002\u0002",
    "\u0002yw\u0003\u0002\u0002\u0002yz\u0003\u0002\u0002\u0002z|\u0003\u0002",
    "\u0002\u0002{y\u0003\u0002\u0002\u0002|\u0080\u0007\u0007\u0002\u0002",
    "}\u007f\u0005\u0010\t\u0002~}\u0003\u0002\u0002\u0002\u007f\u0082\u0003",
    "\u0002\u0002\u0002\u0080~\u0003\u0002\u0002\u0002\u0080\u0081\u0003",
    "\u0002\u0002\u0002\u0081\u0083\u0003\u0002\u0002\u0002\u0082\u0080\u0003",
    "\u0002\u0002\u0002\u0083\u0084\u0005\u0012\n\u0002\u0084\u000f\u0003",
    "\u0002\u0002\u0002\u0085\u0086\u0005$\u0013\u0002\u0086\u0087\u0007",
    "\r\u0002\u0002\u0087\u0088\u0005\u0012\n\u0002\u0088\u0089\u0007\u0010",
    "\u0002\u0002\u0089\u0011\u0003\u0002\u0002\u0002\u008a\u008b\b\n\u0001",
    "\u0002\u008b\u008d\u0005&\u0014\u0002\u008c\u008e\u0005\u0014\u000b",
    "\u0002\u008d\u008c\u0003\u0002\u0002\u0002\u008d\u008e\u0003\u0002\u0002",
    "\u0002\u008e\u009e\u0003\u0002\u0002\u0002\u008f\u009e\u0005(\u0015",
    "\u0002\u0090\u009e\u0005\u001e\u0010\u0002\u0091\u009e\u0005\u0016\f",
    "\u0002\u0092\u009e\u0005\u001c\u000f\u0002\u0093\u0094\u0007\u0006\u0002",
    "\u0002\u0094\u0095\u0005\u0012\n\u0002\u0095\u0096\u0007\u0007\u0002",
    "\u0002\u0096\u009e\u0003\u0002\u0002\u0002\u0097\u0098\u00074\u0002",
    "\u0002\u0098\u0099\u0005\u0012\n\u0002\u0099\u009a\u0005\u0012\n\u0002",
    "\u009a\u009b\u0007:\u0002\u0002\u009b\u009c\u0005\u0012\n\f\u009c\u009e",
    "\u0003\u0002\u0002\u0002\u009d\u008a\u0003\u0002\u0002\u0002\u009d\u008f",
    "\u0003\u0002\u0002\u0002\u009d\u0090\u0003\u0002\u0002\u0002\u009d\u0091",
    "\u0003\u0002\u0002\u0002\u009d\u0092\u0003\u0002\u0002\u0002\u009d\u0093",
    "\u0003\u0002\u0002\u0002\u009d\u0097\u0003\u0002\u0002\u0002\u009e\u00c4",
    "\u0003\u0002\u0002\u0002\u009f\u00a0\f\u000b\u0002\u0002\u00a0\u00a1",
    "\u0007F\u0002\u0002\u00a1\u00c3\u0005\u0012\n\f\u00a2\u00a3\f\n\u0002",
    "\u0002\u00a3\u00a4\u0007*\u0002\u0002\u00a4\u00c3\u0005\u0012\n\u000b",
    "\u00a5\u00a6\f\t\u0002\u0002\u00a6\u00a7\t\u0003\u0002\u0002\u00a7\u00c3",
    "\u0005\u0012\n\n\u00a8\u00a9\f\b\u0002\u0002\u00a9\u00aa\u0007+\u0002",
    "\u0002\u00aa\u00ab\u00073\u0002\u0002\u00ab\u00c3\u0005\u0012\n\t\u00ac",
    "\u00ad\f\u0007\u0002\u0002\u00ad\u00ae\t\u0004\u0002\u0002\u00ae\u00c3",
    "\u0005\u0012\n\b\u00af\u00b0\f\u0006\u0002\u0002\u00b0\u00b1\t\u0005",
    "\u0002\u0002\u00b1\u00c3\u0005\u0012\n\u0007\u00b2\u00b3\f\u0005\u0002",
    "\u0002\u00b3\u00b4\u0007\u0013\u0002\u0002\u00b4\u00c3\u0005\u0012\n",
    "\u0006\u00b5\u00b6\f\u000e\u0002\u0002\u00b6\u00b7\u0007\u0018\u0002",
    "\u0002\u00b7\u00c3\u0005$\u0013\u0002\u00b8\u00b9\f\u0004\u0002\u0002",
    "\u00b9\u00ba\u0007\u000e\u0002\u0002\u00ba\u00bb\u0005&\u0014\u0002",
    "\u00bb\u00bc\u0005\u0014\u000b\u0002\u00bc\u00c3\u0003\u0002\u0002\u0002",
    "\u00bd\u00be\f\u0003\u0002\u0002\u00be\u00bf\u0007\u0004\u0002\u0002",
    "\u00bf\u00c0\u0005.\u0018\u0002\u00c0\u00c1\u0007\u0005\u0002\u0002",
    "\u00c1\u00c3\u0003\u0002\u0002\u0002\u00c2\u009f\u0003\u0002\u0002\u0002",
    "\u00c2\u00a2\u0003\u0002\u0002\u0002\u00c2\u00a5\u0003\u0002\u0002\u0002",
    "\u00c2\u00a8\u0003\u0002\u0002\u0002\u00c2\u00ac\u0003\u0002\u0002\u0002",
    "\u00c2\u00af\u0003\u0002\u0002\u0002\u00c2\u00b2\u0003\u0002\u0002\u0002",
    "\u00c2\u00b5\u0003\u0002\u0002\u0002\u00c2\u00b8\u0003\u0002\u0002\u0002",
    "\u00c2\u00bd\u0003\u0002\u0002\u0002\u00c3\u00c6\u0003\u0002\u0002\u0002",
    "\u00c4\u00c2\u0003\u0002\u0002\u0002\u00c4\u00c5\u0003\u0002\u0002\u0002",
    "\u00c5\u0013\u0003\u0002\u0002\u0002\u00c6\u00c4\u0003\u0002\u0002\u0002",
    "\u00c7\u00d0\u0007\u0006\u0002\u0002\u00c8\u00cd\u0005\u0012\n\u0002",
    "\u00c9\u00ca\u0007\u0019\u0002\u0002\u00ca\u00cc\u0005\u0012\n\u0002",
    "\u00cb\u00c9\u0003\u0002\u0002\u0002\u00cc\u00cf\u0003\u0002\u0002\u0002",
    "\u00cd\u00cb\u0003\u0002\u0002\u0002\u00cd\u00ce\u0003\u0002\u0002\u0002",
    "\u00ce\u00d1\u0003\u0002\u0002\u0002\u00cf\u00cd\u0003\u0002\u0002\u0002",
    "\u00d0\u00c8\u0003\u0002\u0002\u0002\u00d0\u00d1\u0003\u0002\u0002\u0002",
    "\u00d1\u00d2\u0003\u0002\u0002\u0002\u00d2\u00d3\u0007\u0007\u0002\u0002",
    "\u00d3\u0015\u0003\u0002\u0002\u0002\u00d4\u00de\u0005\u0018\r\u0002",
    "\u00d5\u00d6\u0007\b\u0002\u0002\u00d6\u00d7\u0005\u0018\r\u0002\u00d7",
    "\u00d8\u0007\t\u0002\u0002\u00d8\u00de\u0003\u0002\u0002\u0002\u00d9",
    "\u00da\u0007\u0004\u0002\u0002\u00da\u00db\u0005\u0018\r\u0002\u00db",
    "\u00dc\u0007\u0005\u0002\u0002\u00dc\u00de\u0003\u0002\u0002\u0002\u00dd",
    "\u00d4\u0003\u0002\u0002\u0002\u00dd\u00d5\u0003\u0002\u0002\u0002\u00dd",
    "\u00d9\u0003\u0002\u0002\u0002\u00de\u0017\u0003\u0002\u0002\u0002\u00df",
    "\u00e7\u0007\n\u0002\u0002\u00e0\u00e2\u0005\u001a\u000e\u0002\u00e1",
    "\u00e0\u0003\u0002\u0002\u0002\u00e2\u00e5\u0003\u0002\u0002\u0002\u00e3",
    "\u00e1\u0003\u0002\u0002\u0002\u00e3\u00e4\u0003\u0002\u0002\u0002\u00e4",
    "\u00e7\u0003\u0002\u0002\u0002\u00e5\u00e3\u0003\u0002\u0002\u0002\u00e6",
    "\u00df\u0003\u0002\u0002\u0002\u00e6\u00e3\u0003\u0002\u0002\u0002\u00e7",
    "\u0019\u0003\u0002\u0002\u0002\u00e8\u00ea\u0007\n\u0002\u0002\u00e9",
    "\u00eb\u0007\n\u0002\u0002\u00ea\u00e9\u0003\u0002\u0002\u0002\u00ea",
    "\u00eb\u0003\u0002\u0002\u0002\u00eb\u00f3\u0003\u0002\u0002\u0002\u00ec",
    "\u00ed\u0007B\u0002\u0002\u00ed\u00ef\u0007\r\u0002\u0002\u00ee\u00ec",
    "\u0003\u0002\u0002\u0002\u00ee\u00ef\u0003\u0002\u0002\u0002\u00ef\u00f4",
    "\u0003\u0002\u0002\u0002\u00f0\u00f1\u0005&\u0014\u0002\u00f1\u00f2",
    "\u0007\r\u0002\u0002\u00f2\u00f4\u0003\u0002\u0002\u0002\u00f3\u00ee",
    "\u0003\u0002\u0002\u0002\u00f3\u00f0\u0003\u0002\u0002\u0002\u00f4\u00f7",
    "\u0003\u0002\u0002\u0002\u00f5\u00f8\u0005\u0012\n\u0002\u00f6\u00f8",
    "\u0007\u0016\u0002\u0002\u00f7\u00f5\u0003\u0002\u0002\u0002\u00f7\u00f6",
    "\u0003\u0002\u0002\u0002\u00f8\u00fb\u0003\u0002\u0002\u0002\u00f9\u00fa",
    "\u0007E\u0002\u0002\u00fa\u00fc\u0005$\u0013\u0002\u00fb\u00f9\u0003",
    "\u0002\u0002\u0002\u00fb\u00fc\u0003\u0002\u0002\u0002\u00fc\u001b\u0003",
    "\u0002\u0002\u0002\u00fd\u00fe\u00077\u0002\u0002\u00fe\u0107\u0005",
    "\u0012\n\u0002\u00ff\u0103\u0007\u001c\u0002\u0002\u0100\u0102\u0005",
    "\u0010\t\u0002\u0101\u0100\u0003\u0002\u0002\u0002\u0102\u0105\u0003",
    "\u0002\u0002\u0002\u0103\u0101\u0003\u0002\u0002\u0002\u0103\u0104\u0003",
    "\u0002\u0002\u0002\u0104\u0106\u0003\u0002\u0002\u0002\u0105\u0103\u0003",
    "\u0002\u0002\u0002\u0106\u0108\u0005\u0012\n\u0002\u0107\u00ff\u0003",
    "\u0002\u0002\u0002\u0107\u0108\u0003\u0002\u0002\u0002\u0108\u010b\u0003",
    "\u0002\u0002\u0002\u0109\u010a\u0007\'\u0002\u0002\u010a\u010c\u0005",
    "\u0012\n\u0002\u010b\u0109\u0003\u0002\u0002\u0002\u010b\u010c\u0003",
    "\u0002\u0002\u0002\u010c\u001d\u0003\u0002\u0002\u0002\u010d\u010f\u0007",
    ".\u0002\u0002\u010e\u0110\u0007<\u0002\u0002\u010f\u010e\u0003\u0002",
    "\u0002\u0002\u010f\u0110\u0003\u0002\u0002\u0002\u0110\u0112\u0003\u0002",
    "\u0002\u0002\u0111\u0113\u0005\"\u0012\u0002\u0112\u0111\u0003\u0002",
    "\u0002\u0002\u0112\u0113\u0003\u0002\u0002\u0002\u0113\u0114\u0003\u0002",
    "\u0002\u0002\u0114\u0116\u0005$\u0013\u0002\u0115\u0117\u0007H\u0002",
    "\u0002\u0116\u0115\u0003\u0002\u0002\u0002\u0116\u0117\u0003\u0002\u0002",
    "\u0002\u0117\u011a\u0003\u0002\u0002\u0002\u0118\u0119\u00072\u0002",
    "\u0002\u0119\u011b\u0007$\u0002\u0002\u011a\u0118\u0003\u0002\u0002",
    "\u0002\u011a\u011b\u0003\u0002\u0002\u0002\u011b\u011e\u0003\u0002\u0002",
    "\u0002\u011c\u011d\u0007&\u0002\u0002\u011d\u011f\u0005\"\u0012\u0002",
    "\u011e\u011c\u0003\u0002\u0002\u0002\u011e\u011f\u0003\u0002\u0002\u0002",
    "\u011f\u0122\u0003\u0002\u0002\u0002\u0120\u0121\u00076\u0002\u0002",
    "\u0121\u0123\u0005$\u0013\u0002\u0122\u0120\u0003\u0002\u0002\u0002",
    "\u0122\u0123\u0003\u0002\u0002\u0002\u0123\u0126\u0003\u0002\u0002\u0002",
    "\u0124\u0125\u0007\"\u0002\u0002\u0125\u0127\u0005\u0012\n\u0002\u0126",
    "\u0124\u0003\u0002\u0002\u0002\u0126\u0127\u0003\u0002\u0002\u0002\u0127",
    "\u012a\u0003\u0002\u0002\u0002\u0128\u0129\u0007?\u0002\u0002\u0129",
    "\u012b\u0005$\u0013\u0002\u012a\u0128\u0003\u0002\u0002\u0002\u012a",
    "\u012b\u0003\u0002\u0002\u0002\u012b\u012e\u0003\u0002\u0002\u0002\u012c",
    "\u012d\u0007!\u0002\u0002\u012d\u012f\u0005$\u0013\u0002\u012e\u012c",
    "\u0003\u0002\u0002\u0002\u012e\u012f\u0003\u0002\u0002\u0002\u012f\u0133",
    "\u0003\u0002\u0002\u0002\u0130\u0131\u0007#\u0002\u0002\u0131\u0132",
    "\u0007\u001d\u0002\u0002\u0132\u0134\u0005\u0012\n\u0002\u0133\u0130",
    "\u0003\u0002\u0002\u0002\u0133\u0134\u0003\u0002\u0002\u0002\u0134\u0137",
    "\u0003\u0002\u0002\u0002\u0135\u0136\u0007\u001c\u0002\u0002\u0136\u0138",
    "\u0005\u0012\n\u0002\u0137\u0135\u0003\u0002\u0002\u0002\u0137\u0138",
    "\u0003\u0002\u0002\u0002\u0138\u0146\u0003\u0002\u0002\u0002\u0139\u0140",
    "\u0007\'\u0002\u0002\u013a\u013b\u0007C\u0002\u0002\u013b\u013d\u0007",
    "-\u0002\u0002\u013c\u013e\u0005 \u0011\u0002\u013d\u013c\u0003\u0002",
    "\u0002\u0002\u013d\u013e\u0003\u0002\u0002\u0002\u013e\u0141\u0003\u0002",
    "\u0002\u0002\u013f\u0141\u0005 \u0011\u0002\u0140\u013a\u0003\u0002",
    "\u0002\u0002\u0140\u013f\u0003\u0002\u0002\u0002\u0141\u0144\u0003\u0002",
    "\u0002\u0002\u0142\u0143\u0007E\u0002\u0002\u0143\u0145\u0007=\u0002",
    "\u0002\u0144\u0142\u0003\u0002\u0002\u0002\u0144\u0145\u0003\u0002\u0002",
    "\u0002\u0145\u0147\u0003\u0002\u0002\u0002\u0146\u0139\u0003\u0002\u0002",
    "\u0002\u0146\u0147\u0003\u0002\u0002\u0002\u0147\u001f\u0003\u0002\u0002",
    "\u0002\u0148\u0155\u0005\u0012\n\u0002\u0149\u014a\u0007\u0006\u0002",
    "\u0002\u014a\u014f\u0005\u0012\n\u0002\u014b\u014c\u0007\u0019\u0002",
    "\u0002\u014c\u014e\u0005\u0012\n\u0002\u014d\u014b\u0003\u0002\u0002",
    "\u0002\u014e\u0151\u0003\u0002\u0002\u0002\u014f\u014d\u0003\u0002\u0002",
    "\u0002\u014f\u0150\u0003\u0002\u0002\u0002\u0150\u0152\u0003\u0002\u0002",
    "\u0002\u0151\u014f\u0003\u0002\u0002\u0002\u0152\u0153\u0007\u0007\u0002",
    "\u0002\u0153\u0155\u0003\u0002\u0002\u0002\u0154\u0148\u0003\u0002\u0002",
    "\u0002\u0154\u0149\u0003\u0002\u0002\u0002\u0155!\u0003\u0002\u0002",
    "\u0002\u0156\u0159\u0005$\u0013\u0002\u0157\u0159\u0005.\u0018\u0002",
    "\u0158\u0156\u0003\u0002\u0002\u0002\u0158\u0157\u0003\u0002\u0002\u0002",
    "\u0159#\u0003\u0002\u0002\u0002\u015a\u015b\t\u0006\u0002\u0002\u015b",
    "%\u0003\u0002\u0002\u0002\u015c\u0162\u0005$\u0013\u0002\u015d\u0162",
    "\u0007I\u0002\u0002\u015e\u015f\u0007B\u0002\u0002\u015f\u0160\u0007",
    "\u000e\u0002\u0002\u0160\u0162\u0005&\u0014\u0002\u0161\u015c\u0003",
    "\u0002\u0002\u0002\u0161\u015d\u0003\u0002\u0002\u0002\u0161\u015e\u0003",
    "\u0002\u0002\u0002\u0162\'\u0003\u0002\u0002\u0002\u0163\u0167\u0005",
    ".\u0018\u0002\u0164\u0167\u0007G\u0002\u0002\u0165\u0167\u0005,\u0017",
    "\u0002\u0166\u0163\u0003\u0002\u0002\u0002\u0166\u0164\u0003\u0002\u0002",
    "\u0002\u0166\u0165\u0003\u0002\u0002\u0002\u0167)\u0003\u0002\u0002",
    "\u0002\u0168\u0169\u0005$\u0013\u0002\u0169\u016a\u0007\u000f\u0002",
    "\u0002\u016a\u016b\u0005$\u0013\u0002\u016b+\u0003\u0002\u0002\u0002",
    "\u016c\u016d\t\u0007\u0002\u0002\u016d-\u0003\u0002\u0002\u0002\u016e",
    "\u016f\t\b\u0002\u0002\u016f/\u0003\u0002\u0002\u0002435=KOQW^`fjy\u0080",
    "\u008d\u009d\u00c2\u00c4\u00cd\u00d0\u00dd\u00e3\u00e6\u00ea\u00ee\u00f3",
    "\u00f7\u00fb\u0103\u0107\u010b\u010f\u0112\u0116\u011a\u011e\u0122\u0126",
    "\u012a\u012e\u0133\u0137\u013d\u0140\u0144\u0146\u014f\u0154\u0158\u0161",
    "\u0166"].join("");


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
                      "SINGLE_QUOTED_STRING", "WHERE", "WHEN", "URL", "UNIT", 
                      "TRUE", "TO", "TAXONOMY", "STOP", "START", "SEVERITY", 
                      "ROLE", "RETURNS", "PERIOD", "OUTPUT", "OR", "NOT", 
                      "NONE", "NETWORK", "NAVIGATE", "NAMESPACE", "MESSAGE", 
                      "INSTANT", "INCLUDE", "IN", "IF", "FUNCTION", "FROM", 
                      "FILTER", "FALSE", "ENTITY", "ELSE", "DURATION", "DIMENSIONS", 
                      "DICTIONARY", "DEBIT", "CUBE", "CREDIT", "CONSTANT", 
                      "CONCEPT", "BY", "ASSERT", "AS", "AND", "NUMBER", 
                      "INTEGER", "ACCESSOR", "IDENTIFIER", "NAME", "WS", 
                      "UNRECOGNIZED_TOKEN", "ASSERT_UNSATISFIED", "ASSERT_SATISFIED", 
                      "ASSERT_RULE_NAME", "ASSERT_WS" ];

var ruleNames =  [ "xuleFile", "declaration", "namespaceDeclaration", "output", 
                   "assertion", "constantDeclaration", "functionDeclaration", 
                   "assignment", "expression", "parametersList", "factset", 
                   "factsetBody", "aspectFilter", "filter", "navigation", 
                   "returnExpression", "role", "identifier", "access", "literal", 
                   "dataType", "booleanLiteral", "stringLiteral" ];

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
XULEParser.WHEN = 27;
XULEParser.URL = 28;
XULEParser.UNIT = 29;
XULEParser.TRUE = 30;
XULEParser.TO = 31;
XULEParser.TAXONOMY = 32;
XULEParser.STOP = 33;
XULEParser.START = 34;
XULEParser.SEVERITY = 35;
XULEParser.ROLE = 36;
XULEParser.RETURNS = 37;
XULEParser.PERIOD = 38;
XULEParser.OUTPUT = 39;
XULEParser.OR = 40;
XULEParser.NOT = 41;
XULEParser.NONE = 42;
XULEParser.NETWORK = 43;
XULEParser.NAVIGATE = 44;
XULEParser.NAMESPACE = 45;
XULEParser.MESSAGE = 46;
XULEParser.INSTANT = 47;
XULEParser.INCLUDE = 48;
XULEParser.IN = 49;
XULEParser.IF = 50;
XULEParser.FUNCTION = 51;
XULEParser.FROM = 52;
XULEParser.FILTER = 53;
XULEParser.FALSE = 54;
XULEParser.ENTITY = 55;
XULEParser.ELSE = 56;
XULEParser.DURATION = 57;
XULEParser.DIMENSIONS = 58;
XULEParser.DICTIONARY = 59;
XULEParser.DEBIT = 60;
XULEParser.CUBE = 61;
XULEParser.CREDIT = 62;
XULEParser.CONSTANT = 63;
XULEParser.CONCEPT = 64;
XULEParser.BY = 65;
XULEParser.ASSERT = 66;
XULEParser.AS = 67;
XULEParser.AND = 68;
XULEParser.NUMBER = 69;
XULEParser.INTEGER = 70;
XULEParser.ACCESSOR = 71;
XULEParser.IDENTIFIER = 72;
XULEParser.NAME = 73;
XULEParser.WS = 74;
XULEParser.UNRECOGNIZED_TOKEN = 75;
XULEParser.ASSERT_UNSATISFIED = 76;
XULEParser.ASSERT_SATISFIED = 77;
XULEParser.ASSERT_RULE_NAME = 78;
XULEParser.ASSERT_WS = 79;

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
XULEParser.RULE_navigation = 14;
XULEParser.RULE_returnExpression = 15;
XULEParser.RULE_role = 16;
XULEParser.RULE_identifier = 17;
XULEParser.RULE_access = 18;
XULEParser.RULE_literal = 19;
XULEParser.RULE_dataType = 20;
XULEParser.RULE_booleanLiteral = 21;
XULEParser.RULE_stringLiteral = 22;


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
        this.state = 51;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while(((((_la - 39)) & ~0x1f) == 0 && ((1 << (_la - 39)) & ((1 << (XULEParser.OUTPUT - 39)) | (1 << (XULEParser.NAMESPACE - 39)) | (1 << (XULEParser.FUNCTION - 39)) | (1 << (XULEParser.CONSTANT - 39)) | (1 << (XULEParser.ASSERT - 39)))) !== 0)) {
            this.state = 49;
            this._errHandler.sync(this);
            switch(this._input.LA(1)) {
            case XULEParser.NAMESPACE:
            case XULEParser.FUNCTION:
            case XULEParser.CONSTANT:
                this.state = 46;
                this.declaration();
                break;
            case XULEParser.ASSERT:
                this.state = 47;
                this.assertion();
                break;
            case XULEParser.OUTPUT:
                this.state = 48;
                this.output();
                break;
            default:
                throw new antlr4.error.NoViableAltException(this);
            }
            this.state = 53;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
        }
        this.state = 54;
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
        this.state = 59;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.NAMESPACE:
            this.enterOuterAlt(localctx, 1);
            this.state = 56;
            this.namespaceDeclaration();
            break;
        case XULEParser.CONSTANT:
            this.enterOuterAlt(localctx, 2);
            this.state = 57;
            this.constantDeclaration();
            break;
        case XULEParser.FUNCTION:
            this.enterOuterAlt(localctx, 3);
            this.state = 58;
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
        this.state = 61;
        this.match(XULEParser.NAMESPACE);
        this.state = 62;
        this.identifier();
        this.state = 63;
        this.match(XULEParser.ASSIGN);
        this.state = 64;
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
        this.state = 66;
        this.match(XULEParser.OUTPUT);
        this.state = 67;
        this.access();
        this.state = 73;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,3,this._ctx);
        if(la_===1) {
            this.state = 68;
            this.match(XULEParser.OPEN_BRACKET);
            this.state = 69;
            this.match(XULEParser.AT);
            this.state = 70;
            this.identifier();
            this.state = 71;
            this.match(XULEParser.CLOSE_BRACKET);

        }
        this.state = 79;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,5,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 77;
                this._errHandler.sync(this);
                switch(this._input.LA(1)) {
                case XULEParser.CONSTANT:
                    this.state = 75;
                    this.constantDeclaration();
                    break;
                case XULEParser.TAXONOMY:
                case XULEParser.PERIOD:
                case XULEParser.CONCEPT:
                case XULEParser.IDENTIFIER:
                    this.state = 76;
                    this.assignment();
                    break;
                default:
                    throw new antlr4.error.NoViableAltException(this);
                } 
            }
            this.state = 81;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,5,this._ctx);
        }

        this.state = 82;
        this.expression(0);
        this.state = 85;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.MESSAGE) {
            this.state = 83;
            this.match(XULEParser.MESSAGE);
            this.state = 84;
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
        this.state = 87;
        this.match(XULEParser.ASSERT);
        this.state = 88;
        this.match(XULEParser.ASSERT_RULE_NAME);
        this.state = 89;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.ASSERT_UNSATISFIED || _la===XULEParser.ASSERT_SATISFIED)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
        this.state = 94;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,8,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 92;
                this._errHandler.sync(this);
                switch(this._input.LA(1)) {
                case XULEParser.CONSTANT:
                    this.state = 90;
                    this.constantDeclaration();
                    break;
                case XULEParser.TAXONOMY:
                case XULEParser.PERIOD:
                case XULEParser.CONCEPT:
                case XULEParser.IDENTIFIER:
                    this.state = 91;
                    this.assignment();
                    break;
                default:
                    throw new antlr4.error.NoViableAltException(this);
                } 
            }
            this.state = 96;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,8,this._ctx);
        }

        this.state = 97;
        this.expression(0);
        this.state = 100;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.MESSAGE) {
            this.state = 98;
            this.match(XULEParser.MESSAGE);
            this.state = 99;
            this.expression(0);
        }

        this.state = 104;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.SEVERITY) {
            this.state = 102;
            this.match(XULEParser.SEVERITY);
            this.state = 103;
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
        this.state = 106;
        this.match(XULEParser.CONSTANT);
        this.state = 107;
        this.identifier();
        this.state = 108;
        this.match(XULEParser.ASSIGN);
        this.state = 109;
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
        this.state = 111;
        this.match(XULEParser.FUNCTION);
        this.state = 112;
        this.identifier();
        this.state = 113;
        this.match(XULEParser.OPEN_PAREN);
        this.state = 114;
        this.identifier();
        this.state = 119;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while(_la===XULEParser.COMMA) {
            this.state = 115;
            this.match(XULEParser.COMMA);
            this.state = 116;
            this.identifier();
            this.state = 121;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
        }
        this.state = 122;
        this.match(XULEParser.CLOSE_PAREN);
        this.state = 126;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,12,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 123;
                this.assignment(); 
            }
            this.state = 128;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,12,this._ctx);
        }

        this.state = 129;
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
        this.state = 131;
        this.identifier();
        this.state = 132;
        this.match(XULEParser.ASSIGN);
        this.state = 133;
        this.expression(0);
        this.state = 134;
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

ExpressionContext.prototype.access = function() {
    return this.getTypedRuleContext(AccessContext,0);
};

ExpressionContext.prototype.parametersList = function() {
    return this.getTypedRuleContext(ParametersListContext,0);
};

ExpressionContext.prototype.literal = function() {
    return this.getTypedRuleContext(LiteralContext,0);
};

ExpressionContext.prototype.navigation = function() {
    return this.getTypedRuleContext(NavigationContext,0);
};

ExpressionContext.prototype.factset = function() {
    return this.getTypedRuleContext(FactsetContext,0);
};

ExpressionContext.prototype.filter = function() {
    return this.getTypedRuleContext(FilterContext,0);
};

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
        this.state = 155;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,14,this._ctx);
        switch(la_) {
        case 1:
            this.state = 137;
            this.access();
            this.state = 139;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,13,this._ctx);
            if(la_===1) {
                this.state = 138;
                this.parametersList();

            }
            break;

        case 2:
            this.state = 141;
            this.literal();
            break;

        case 3:
            this.state = 142;
            this.navigation();
            break;

        case 4:
            this.state = 143;
            this.factset();
            break;

        case 5:
            this.state = 144;
            this.filter();
            break;

        case 6:
            this.state = 145;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 146;
            this.expression(0);
            this.state = 147;
            this.match(XULEParser.CLOSE_PAREN);
            break;

        case 7:
            this.state = 149;
            this.match(XULEParser.IF);
            this.state = 150;
            this.expression(0);
            this.state = 151;
            this.expression(0);
            this.state = 152;
            this.match(XULEParser.ELSE);
            this.state = 153;
            this.expression(10);
            break;

        }
        this._ctx.stop = this._input.LT(-1);
        this.state = 194;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,16,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                if(this._parseListeners!==null) {
                    this.triggerExitRuleEvent();
                }
                _prevctx = localctx;
                this.state = 192;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,15,this._ctx);
                switch(la_) {
                case 1:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 157;
                    if (!( this.precpred(this._ctx, 9))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 9)");
                    }
                    this.state = 158;
                    this.match(XULEParser.AND);
                    this.state = 159;
                    this.expression(10);
                    break;

                case 2:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 160;
                    if (!( this.precpred(this._ctx, 8))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 8)");
                    }
                    this.state = 161;
                    this.match(XULEParser.OR);
                    this.state = 162;
                    this.expression(9);
                    break;

                case 3:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 163;
                    if (!( this.precpred(this._ctx, 7))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 7)");
                    }
                    this.state = 164;
                    _la = this._input.LA(1);
                    if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.NOT_EQUALS) | (1 << XULEParser.EQUALS) | (1 << XULEParser.GREATER_THAN) | (1 << XULEParser.LESS_THAN))) !== 0))) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 165;
                    this.expression(8);
                    break;

                case 4:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 166;
                    if (!( this.precpred(this._ctx, 6))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 6)");
                    }

                    this.state = 167;
                    this.match(XULEParser.NOT);
                    this.state = 168;
                    this.match(XULEParser.IN);
                    this.state = 169;
                    this.expression(7);
                    break;

                case 5:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 170;
                    if (!( this.precpred(this._ctx, 5))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 5)");
                    }
                    this.state = 171;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.PLUS || _la===XULEParser.MINUS)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 172;
                    this.expression(6);
                    break;

                case 6:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 173;
                    if (!( this.precpred(this._ctx, 4))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 4)");
                    }
                    this.state = 174;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.TIMES || _la===XULEParser.DIV)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 175;
                    this.expression(5);
                    break;

                case 7:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 176;
                    if (!( this.precpred(this._ctx, 3))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 3)");
                    }
                    this.state = 177;
                    this.match(XULEParser.EXP);
                    this.state = 178;
                    this.expression(4);
                    break;

                case 8:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 179;
                    if (!( this.precpred(this._ctx, 12))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 12)");
                    }
                    this.state = 180;
                    this.match(XULEParser.SHARP);
                    this.state = 181;
                    this.identifier();
                    break;

                case 9:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 182;
                    if (!( this.precpred(this._ctx, 2))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 2)");
                    }
                    this.state = 183;
                    this.match(XULEParser.DOT);
                    this.state = 184;
                    this.access();
                    this.state = 185;
                    this.parametersList();
                    break;

                case 10:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 187;
                    if (!( this.precpred(this._ctx, 1))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 1)");
                    }
                    this.state = 188;
                    this.match(XULEParser.OPEN_BRACKET);
                    this.state = 189;
                    this.stringLiteral();
                    this.state = 190;
                    this.match(XULEParser.CLOSE_BRACKET);
                    break;

                } 
            }
            this.state = 196;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,16,this._ctx);
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
        this.state = 197;
        this.match(XULEParser.OPEN_PAREN);
        this.state = 206;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,18,this._ctx);
        if(la_===1) {
            this.state = 198;
            this.expression(0);
            this.state = 203;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.COMMA) {
                this.state = 199;
                this.match(XULEParser.COMMA);
                this.state = 200;
                this.expression(0);
                this.state = 205;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }

        }
        this.state = 208;
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
    try {
        this.state = 219;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,19,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 210;
            this.factsetBody();
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 211;
            this.match(XULEParser.OPEN_CURLY);
            this.state = 212;
            this.factsetBody();
            this.state = 213;
            this.match(XULEParser.CLOSE_CURLY);
            break;

        case 3:
            this.enterOuterAlt(localctx, 3);
            this.state = 215;
            this.match(XULEParser.OPEN_BRACKET);
            this.state = 216;
            this.factsetBody();
            this.state = 217;
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

FactsetBodyContext.prototype.AT = function() {
    return this.getToken(XULEParser.AT, 0);
};

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
        this.state = 228;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,21,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 221;
            this.match(XULEParser.AT);
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 225;
            this._errHandler.sync(this);
            var _alt = this._interp.adaptivePredict(this._input,20,this._ctx)
            while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
                if(_alt===1) {
                    this.state = 222;
                    this.aspectFilter(); 
                }
                this.state = 227;
                this._errHandler.sync(this);
                _alt = this._interp.adaptivePredict(this._input,20,this._ctx);
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


AspectFilterContext.prototype.access = function() {
    return this.getTypedRuleContext(AccessContext,0);
};

AspectFilterContext.prototype.ASSIGN = function() {
    return this.getToken(XULEParser.ASSIGN, 0);
};

AspectFilterContext.prototype.expression = function() {
    return this.getTypedRuleContext(ExpressionContext,0);
};

AspectFilterContext.prototype.TIMES = function() {
    return this.getToken(XULEParser.TIMES, 0);
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
        this.enterOuterAlt(localctx, 1);
        this.state = 230;
        this.match(XULEParser.AT);
        this.state = 232;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,22,this._ctx);
        if(la_===1) {
            this.state = 231;
            this.match(XULEParser.AT);

        }
        this.state = 241;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,24,this._ctx);
        switch(la_) {
        case 1:
            this.state = 236;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,23,this._ctx);
            if(la_===1) {
                this.state = 234;
                this.match(XULEParser.CONCEPT);
                this.state = 235;
                this.match(XULEParser.ASSIGN);

            }
            break;

        case 2:
            this.state = 238;
            this.access();
            this.state = 239;
            this.match(XULEParser.ASSIGN);
            break;

        }
        this.state = 245;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,25,this._ctx);
        switch(la_) {
        case 1:
            this.state = 243;
            this.expression(0);
            break;

        case 2:
            this.state = 244;
            this.match(XULEParser.TIMES);
            break;

        }
        this.state = 249;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,26,this._ctx);
        if(la_===1) {
            this.state = 247;
            this.match(XULEParser.AS);
            this.state = 248;
            this.identifier();

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
        this.state = 251;
        this.match(XULEParser.FILTER);
        this.state = 252;
        this.expression(0);
        this.state = 261;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,28,this._ctx);
        if(la_===1) {
            this.state = 253;
            this.match(XULEParser.WHERE);
            this.state = 257;
            this._errHandler.sync(this);
            var _alt = this._interp.adaptivePredict(this._input,27,this._ctx)
            while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
                if(_alt===1) {
                    this.state = 254;
                    this.assignment(); 
                }
                this.state = 259;
                this._errHandler.sync(this);
                _alt = this._interp.adaptivePredict(this._input,27,this._ctx);
            }

            this.state = 260;
            this.expression(0);

        }
        this.state = 265;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,29,this._ctx);
        if(la_===1) {
            this.state = 263;
            this.match(XULEParser.RETURNS);
            this.state = 264;
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


function NavigationContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_navigation;
    this.arcrole = null; // RoleContext
    this.direction = null; // IdentifierContext
    this.levels = null; // Token
    return this;
}

NavigationContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
NavigationContext.prototype.constructor = NavigationContext;

NavigationContext.prototype.NAVIGATE = function() {
    return this.getToken(XULEParser.NAVIGATE, 0);
};

NavigationContext.prototype.identifier = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(IdentifierContext);
    } else {
        return this.getTypedRuleContext(IdentifierContext,i);
    }
};

NavigationContext.prototype.DIMENSIONS = function() {
    return this.getToken(XULEParser.DIMENSIONS, 0);
};

NavigationContext.prototype.INCLUDE = function() {
    return this.getToken(XULEParser.INCLUDE, 0);
};

NavigationContext.prototype.START = function() {
    return this.getToken(XULEParser.START, 0);
};

NavigationContext.prototype.ROLE = function() {
    return this.getToken(XULEParser.ROLE, 0);
};

NavigationContext.prototype.role = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(RoleContext);
    } else {
        return this.getTypedRuleContext(RoleContext,i);
    }
};

NavigationContext.prototype.FROM = function() {
    return this.getToken(XULEParser.FROM, 0);
};

NavigationContext.prototype.TAXONOMY = function() {
    return this.getToken(XULEParser.TAXONOMY, 0);
};

NavigationContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

NavigationContext.prototype.CUBE = function() {
    return this.getToken(XULEParser.CUBE, 0);
};

NavigationContext.prototype.TO = function() {
    return this.getToken(XULEParser.TO, 0);
};

NavigationContext.prototype.STOP = function() {
    return this.getToken(XULEParser.STOP, 0);
};

NavigationContext.prototype.WHEN = function() {
    return this.getToken(XULEParser.WHEN, 0);
};

NavigationContext.prototype.WHERE = function() {
    return this.getToken(XULEParser.WHERE, 0);
};

NavigationContext.prototype.RETURNS = function() {
    return this.getToken(XULEParser.RETURNS, 0);
};

NavigationContext.prototype.INTEGER = function() {
    return this.getToken(XULEParser.INTEGER, 0);
};

NavigationContext.prototype.returnExpression = function() {
    return this.getTypedRuleContext(ReturnExpressionContext,0);
};

NavigationContext.prototype.AS = function() {
    return this.getToken(XULEParser.AS, 0);
};

NavigationContext.prototype.DICTIONARY = function() {
    return this.getToken(XULEParser.DICTIONARY, 0);
};

NavigationContext.prototype.BY = function() {
    return this.getToken(XULEParser.BY, 0);
};

NavigationContext.prototype.NETWORK = function() {
    return this.getToken(XULEParser.NETWORK, 0);
};

NavigationContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterNavigation(this);
	}
};

NavigationContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitNavigation(this);
	}
};




XULEParser.NavigationContext = NavigationContext;

XULEParser.prototype.navigation = function() {

    var localctx = new NavigationContext(this, this._ctx, this.state);
    this.enterRule(localctx, 28, XULEParser.RULE_navigation);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 267;
        this.match(XULEParser.NAVIGATE);
        this.state = 269;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.DIMENSIONS) {
            this.state = 268;
            this.match(XULEParser.DIMENSIONS);
        }

        this.state = 272;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,31,this._ctx);
        if(la_===1) {
            this.state = 271;
            localctx.arcrole = this.role();

        }
        this.state = 274;
        localctx.direction = this.identifier();
        this.state = 276;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,32,this._ctx);
        if(la_===1) {
            this.state = 275;
            localctx.levels = this.match(XULEParser.INTEGER);

        }
        this.state = 280;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,33,this._ctx);
        if(la_===1) {
            this.state = 278;
            this.match(XULEParser.INCLUDE);
            this.state = 279;
            this.match(XULEParser.START);

        }
        this.state = 284;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,34,this._ctx);
        if(la_===1) {
            this.state = 282;
            this.match(XULEParser.ROLE);
            this.state = 283;
            this.role();

        }
        this.state = 288;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,35,this._ctx);
        if(la_===1) {
            this.state = 286;
            this.match(XULEParser.FROM);
            this.state = 287;
            this.identifier();

        }
        this.state = 292;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,36,this._ctx);
        if(la_===1) {
            this.state = 290;
            this.match(XULEParser.TAXONOMY);
            this.state = 291;
            this.expression(0);

        }
        this.state = 296;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,37,this._ctx);
        if(la_===1) {
            this.state = 294;
            this.match(XULEParser.CUBE);
            this.state = 295;
            this.identifier();

        }
        this.state = 300;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,38,this._ctx);
        if(la_===1) {
            this.state = 298;
            this.match(XULEParser.TO);
            this.state = 299;
            this.identifier();

        }
        this.state = 305;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,39,this._ctx);
        if(la_===1) {
            this.state = 302;
            this.match(XULEParser.STOP);
            this.state = 303;
            this.match(XULEParser.WHEN);
            this.state = 304;
            this.expression(0);

        }
        this.state = 309;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,40,this._ctx);
        if(la_===1) {
            this.state = 307;
            this.match(XULEParser.WHERE);
            this.state = 308;
            this.expression(0);

        }
        this.state = 324;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,44,this._ctx);
        if(la_===1) {
            this.state = 311;
            this.match(XULEParser.RETURNS);
            this.state = 318;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,42,this._ctx);
            switch(la_) {
            case 1:
                this.state = 312;
                this.match(XULEParser.BY);
                this.state = 313;
                this.match(XULEParser.NETWORK);
                this.state = 315;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,41,this._ctx);
                if(la_===1) {
                    this.state = 314;
                    this.returnExpression();

                }
                break;

            case 2:
                this.state = 317;
                this.returnExpression();
                break;

            }
            this.state = 322;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,43,this._ctx);
            if(la_===1) {
                this.state = 320;
                this.match(XULEParser.AS);
                this.state = 321;
                this.match(XULEParser.DICTIONARY);

            }

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


function ReturnExpressionContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_returnExpression;
    return this;
}

ReturnExpressionContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ReturnExpressionContext.prototype.constructor = ReturnExpressionContext;

ReturnExpressionContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
};

ReturnExpressionContext.prototype.OPEN_PAREN = function() {
    return this.getToken(XULEParser.OPEN_PAREN, 0);
};

ReturnExpressionContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(XULEParser.CLOSE_PAREN, 0);
};

ReturnExpressionContext.prototype.COMMA = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.COMMA);
    } else {
        return this.getToken(XULEParser.COMMA, i);
    }
};


ReturnExpressionContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterReturnExpression(this);
	}
};

ReturnExpressionContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitReturnExpression(this);
	}
};




XULEParser.ReturnExpressionContext = ReturnExpressionContext;

XULEParser.prototype.returnExpression = function() {

    var localctx = new ReturnExpressionContext(this, this._ctx, this.state);
    this.enterRule(localctx, 30, XULEParser.RULE_returnExpression);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 338;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,46,this._ctx);
        switch(la_) {
        case 1:
            this.state = 326;
            this.expression(0);
            break;

        case 2:
            this.state = 327;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 328;
            this.expression(0);
            this.state = 333;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.COMMA) {
                this.state = 329;
                this.match(XULEParser.COMMA);
                this.state = 330;
                this.expression(0);
                this.state = 335;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }
            this.state = 336;
            this.match(XULEParser.CLOSE_PAREN);
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


function RoleContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_role;
    return this;
}

RoleContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
RoleContext.prototype.constructor = RoleContext;

RoleContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

RoleContext.prototype.stringLiteral = function() {
    return this.getTypedRuleContext(StringLiteralContext,0);
};

RoleContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterRole(this);
	}
};

RoleContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitRole(this);
	}
};




XULEParser.RoleContext = RoleContext;

XULEParser.prototype.role = function() {

    var localctx = new RoleContext(this, this._ctx, this.state);
    this.enterRule(localctx, 32, XULEParser.RULE_role);
    try {
        this.state = 342;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.TAXONOMY:
        case XULEParser.PERIOD:
        case XULEParser.CONCEPT:
        case XULEParser.IDENTIFIER:
            this.enterOuterAlt(localctx, 1);
            this.state = 340;
            this.identifier();
            break;
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
            this.enterOuterAlt(localctx, 2);
            this.state = 341;
            this.stringLiteral();
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

IdentifierContext.prototype.CONCEPT = function() {
    return this.getToken(XULEParser.CONCEPT, 0);
};

IdentifierContext.prototype.PERIOD = function() {
    return this.getToken(XULEParser.PERIOD, 0);
};

IdentifierContext.prototype.TAXONOMY = function() {
    return this.getToken(XULEParser.TAXONOMY, 0);
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
    this.enterRule(localctx, 34, XULEParser.RULE_identifier);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 344;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.TAXONOMY || _la===XULEParser.PERIOD || _la===XULEParser.CONCEPT || _la===XULEParser.IDENTIFIER)) {
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
    this.enterRule(localctx, 36, XULEParser.RULE_access);
    try {
        this.state = 351;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,48,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 346;
            this.identifier();
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 347;
            this.match(XULEParser.ACCESSOR);
            break;

        case 3:
            this.enterOuterAlt(localctx, 3);
            this.state = 348;
            this.match(XULEParser.CONCEPT);
            this.state = 349;
            this.match(XULEParser.DOT);
            this.state = 350;
            this.access();
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
    this.enterRule(localctx, 38, XULEParser.RULE_literal);
    try {
        this.state = 356;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
            this.enterOuterAlt(localctx, 1);
            this.state = 353;
            this.stringLiteral();
            break;
        case XULEParser.NUMBER:
            this.enterOuterAlt(localctx, 2);
            this.state = 354;
            this.match(XULEParser.NUMBER);
            break;
        case XULEParser.TRUE:
        case XULEParser.FALSE:
            this.enterOuterAlt(localctx, 3);
            this.state = 355;
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
    this.enterRule(localctx, 40, XULEParser.RULE_dataType);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 358;
        this.identifier();
        this.state = 359;
        this.match(XULEParser.COLON);
        this.state = 360;
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
    this.enterRule(localctx, 42, XULEParser.RULE_booleanLiteral);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 362;
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
    this.enterRule(localctx, 44, XULEParser.RULE_stringLiteral);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 364;
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
			return this.precpred(this._ctx, 9);
		case 1:
			return this.precpred(this._ctx, 8);
		case 2:
			return this.precpred(this._ctx, 7);
		case 3:
			return this.precpred(this._ctx, 6);
		case 4:
			return this.precpred(this._ctx, 5);
		case 5:
			return this.precpred(this._ctx, 4);
		case 6:
			return this.precpred(this._ctx, 3);
		case 7:
			return this.precpred(this._ctx, 12);
		case 8:
			return this.precpred(this._ctx, 2);
		case 9:
			return this.precpred(this._ctx, 1);
		default:
			throw "No predicate with index:" + predIndex;
	}
};


exports.XULEParser = XULEParser;
