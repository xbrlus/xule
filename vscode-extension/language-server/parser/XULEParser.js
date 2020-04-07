// Generated from XULEParser.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');
var XULEParserListener = require('./XULEParserListener').XULEParserListener;
var grammarFileName = "XULEParser.g4";


var serializedATN = ["\u0003\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964",
    "\u0003P\u017f\u0004\u0002\t\u0002\u0004\u0003\t\u0003\u0004\u0004\t",
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
    "\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0003\u0005\u0005\u0005Y",
    "\n\u0005\u0005\u0005[\n\u0005\u0003\u0006\u0003\u0006\u0003\u0006\u0003",
    "\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0003\u0006\u0005",
    "\u0006f\n\u0006\u0005\u0006h\n\u0006\u0003\u0006\u0003\u0006\u0005\u0006",
    "l\n\u0006\u0006\u0006n\n\u0006\r\u0006\u000e\u0006o\u0003\u0007\u0003",
    "\u0007\u0003\u0007\u0003\u0007\u0003\u0007\u0003\b\u0003\b\u0003\b\u0003",
    "\b\u0003\b\u0003\b\u0007\b}\n\b\f\b\u000e\b\u0080\u000b\b\u0003\b\u0003",
    "\b\u0007\b\u0084\n\b\f\b\u000e\b\u0087\u000b\b\u0003\b\u0003\b\u0003",
    "\t\u0003\t\u0003\t\u0003\t\u0003\t\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0005\n\u009f\n\n\u0003\n\u0003\n\u0003\n\u0003\n\u0005\n",
    "\u00a5\n\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0005\n\u00b2\n\n\u0003\n\u0003\n\u0003\n",
    "\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003",
    "\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0005\n\u00c6\n\n",
    "\u0003\n\u0003\n\u0003\n\u0003\n\u0003\n\u0007\n\u00cd\n\n\f\n\u000e",
    "\n\u00d0\u000b\n\u0003\u000b\u0003\u000b\u0003\u000b\u0003\u000b\u0007",
    "\u000b\u00d6\n\u000b\f\u000b\u000e\u000b\u00d9\u000b\u000b\u0005\u000b",
    "\u00db\n\u000b\u0003\u000b\u0003\u000b\u0003\f\u0003\f\u0003\f\u0003",
    "\f\u0003\f\u0003\f\u0003\f\u0003\f\u0003\f\u0005\f\u00e8\n\f\u0003\r",
    "\u0003\r\u0007\r\u00ec\n\r\f\r\u000e\r\u00ef\u000b\r\u0005\r\u00f1\n",
    "\r\u0003\u000e\u0003\u000e\u0005\u000e\u00f5\n\u000e\u0003\u000e\u0003",
    "\u000e\u0005\u000e\u00f9\n\u000e\u0003\u000e\u0003\u000e\u0003\u000e",
    "\u0005\u000e\u00fe\n\u000e\u0003\u000e\u0003\u000e\u0005\u000e\u0102",
    "\n\u000e\u0003\u000e\u0003\u000e\u0005\u000e\u0106\n\u000e\u0003\u000e",
    "\u0003\u000e\u0005\u000e\u010a\n\u000e\u0003\u000f\u0003\u000f\u0003",
    "\u000f\u0003\u000f\u0007\u000f\u0110\n\u000f\f\u000f\u000e\u000f\u0113",
    "\u000b\u000f\u0003\u000f\u0005\u000f\u0116\n\u000f\u0003\u000f\u0003",
    "\u000f\u0005\u000f\u011a\n\u000f\u0003\u0010\u0003\u0010\u0005\u0010",
    "\u011e\n\u0010\u0003\u0010\u0005\u0010\u0121\n\u0010\u0003\u0010\u0003",
    "\u0010\u0005\u0010\u0125\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010",
    "\u0129\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u012d\n\u0010\u0003",
    "\u0010\u0003\u0010\u0005\u0010\u0131\n\u0010\u0003\u0010\u0003\u0010",
    "\u0005\u0010\u0135\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u0139",
    "\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u013d\n\u0010\u0003\u0010",
    "\u0003\u0010\u0003\u0010\u0005\u0010\u0142\n\u0010\u0003\u0010\u0003",
    "\u0010\u0005\u0010\u0146\n\u0010\u0003\u0010\u0003\u0010\u0003\u0010",
    "\u0003\u0010\u0005\u0010\u014c\n\u0010\u0003\u0010\u0005\u0010\u014f",
    "\n\u0010\u0003\u0010\u0003\u0010\u0005\u0010\u0153\n\u0010\u0005\u0010",
    "\u0155\n\u0010\u0003\u0011\u0003\u0011\u0003\u0011\u0003\u0011\u0003",
    "\u0011\u0007\u0011\u015c\n\u0011\f\u0011\u000e\u0011\u015f\u000b\u0011",
    "\u0003\u0011\u0003\u0011\u0005\u0011\u0163\n\u0011\u0003\u0012\u0003",
    "\u0012\u0005\u0012\u0167\n\u0012\u0003\u0013\u0003\u0013\u0003\u0014",
    "\u0003\u0014\u0003\u0014\u0003\u0014\u0003\u0014\u0005\u0014\u0170\n",
    "\u0014\u0003\u0015\u0003\u0015\u0003\u0015\u0005\u0015\u0175\n\u0015",
    "\u0003\u0016\u0003\u0016\u0003\u0016\u0003\u0016\u0003\u0017\u0003\u0017",
    "\u0003\u0018\u0003\u0018\u0003\u0018\u0002\u0003\u0012\u0019\u0002\u0004",
    "\u0006\b\n\f\u000e\u0010\u0012\u0014\u0016\u0018\u001a\u001c\u001e ",
    "\"$&(*,.\u0002\n\u0003\u0002MN\u0004\u0002\u0014\u0015++\u0004\u0002",
    "\u000b\f\u0011\u0012\u0003\u0002\u0014\u0015\u0003\u0002\u0016\u0017",
    "\u0006\u0002\"\"((AAII\u0004\u0002  88\u0003\u0002\u001a\u001b\u0002",
    "\u01b2\u00025\u0003\u0002\u0002\u0002\u0004=\u0003\u0002\u0002\u0002",
    "\u0006?\u0003\u0002\u0002\u0002\bD\u0003\u0002\u0002\u0002\n\\\u0003",
    "\u0002\u0002\u0002\fq\u0003\u0002\u0002\u0002\u000ev\u0003\u0002\u0002",
    "\u0002\u0010\u008a\u0003\u0002\u0002\u0002\u0012\u00a4\u0003\u0002\u0002",
    "\u0002\u0014\u00d1\u0003\u0002\u0002\u0002\u0016\u00e7\u0003\u0002\u0002",
    "\u0002\u0018\u00f0\u0003\u0002\u0002\u0002\u001a\u00f2\u0003\u0002\u0002",
    "\u0002\u001c\u010b\u0003\u0002\u0002\u0002\u001e\u011b\u0003\u0002\u0002",
    "\u0002 \u0162\u0003\u0002\u0002\u0002\"\u0166\u0003\u0002\u0002\u0002",
    "$\u0168\u0003\u0002\u0002\u0002&\u016f\u0003\u0002\u0002\u0002(\u0174",
    "\u0003\u0002\u0002\u0002*\u0176\u0003\u0002\u0002\u0002,\u017a\u0003",
    "\u0002\u0002\u0002.\u017c\u0003\u0002\u0002\u000204\u0005\u0004\u0003",
    "\u000214\u0005\n\u0006\u000224\u0005\b\u0005\u000230\u0003\u0002\u0002",
    "\u000231\u0003\u0002\u0002\u000232\u0003\u0002\u0002\u000247\u0003\u0002",
    "\u0002\u000253\u0003\u0002\u0002\u000256\u0003\u0002\u0002\u000268\u0003",
    "\u0002\u0002\u000275\u0003\u0002\u0002\u000289\u0007\u0002\u0002\u0003",
    "9\u0003\u0003\u0002\u0002\u0002:>\u0005\u0006\u0004\u0002;>\u0005\f",
    "\u0007\u0002<>\u0005\u000e\b\u0002=:\u0003\u0002\u0002\u0002=;\u0003",
    "\u0002\u0002\u0002=<\u0003\u0002\u0002\u0002>\u0005\u0003\u0002\u0002",
    "\u0002?@\u0007/\u0002\u0002@A\u0005$\u0013\u0002AB\u0007\r\u0002\u0002",
    "BC\u0007\u001e\u0002\u0002C\u0007\u0003\u0002\u0002\u0002DE\u0007)\u0002",
    "\u0002EK\u0005&\u0014\u0002FG\u0007\u0004\u0002\u0002GH\u0007\n\u0002",
    "\u0002HI\u0005$\u0013\u0002IJ\u0007\u0005\u0002\u0002JL\u0003\u0002",
    "\u0002\u0002KF\u0003\u0002\u0002\u0002KL\u0003\u0002\u0002\u0002LQ\u0003",
    "\u0002\u0002\u0002MP\u0005\f\u0007\u0002NP\u0005\u0010\t\u0002OM\u0003",
    "\u0002\u0002\u0002ON\u0003\u0002\u0002\u0002PS\u0003\u0002\u0002\u0002",
    "QO\u0003\u0002\u0002\u0002QR\u0003\u0002\u0002\u0002RT\u0003\u0002\u0002",
    "\u0002SQ\u0003\u0002\u0002\u0002TZ\u0005\u0012\n\u0002UV\u00070\u0002",
    "\u0002VX\u0005\u0012\n\u0002WY\u0007\u0010\u0002\u0002XW\u0003\u0002",
    "\u0002\u0002XY\u0003\u0002\u0002\u0002Y[\u0003\u0002\u0002\u0002ZU\u0003",
    "\u0002\u0002\u0002Z[\u0003\u0002\u0002\u0002[\t\u0003\u0002\u0002\u0002",
    "\\]\u0007C\u0002\u0002]^\u0007O\u0002\u0002^m\t\u0002\u0002\u0002_n",
    "\u0005\f\u0007\u0002`n\u0005\u0010\t\u0002ag\u0005\u0012\n\u0002bc\u0007",
    "0\u0002\u0002ce\u0005\u0012\n\u0002df\u0007\u0010\u0002\u0002ed\u0003",
    "\u0002\u0002\u0002ef\u0003\u0002\u0002\u0002fh\u0003\u0002\u0002\u0002",
    "gb\u0003\u0002\u0002\u0002gh\u0003\u0002\u0002\u0002hk\u0003\u0002\u0002",
    "\u0002ij\u0007%\u0002\u0002jl\u0005\u0012\n\u0002ki\u0003\u0002\u0002",
    "\u0002kl\u0003\u0002\u0002\u0002ln\u0003\u0002\u0002\u0002m_\u0003\u0002",
    "\u0002\u0002m`\u0003\u0002\u0002\u0002ma\u0003\u0002\u0002\u0002no\u0003",
    "\u0002\u0002\u0002om\u0003\u0002\u0002\u0002op\u0003\u0002\u0002\u0002",
    "p\u000b\u0003\u0002\u0002\u0002qr\u0007@\u0002\u0002rs\u0005$\u0013",
    "\u0002st\u0007\r\u0002\u0002tu\u0005\u0012\n\u0002u\r\u0003\u0002\u0002",
    "\u0002vw\u00075\u0002\u0002wx\u0005$\u0013\u0002xy\u0007\u0006\u0002",
    "\u0002y~\u0005$\u0013\u0002z{\u0007\u0019\u0002\u0002{}\u0005$\u0013",
    "\u0002|z\u0003\u0002\u0002\u0002}\u0080\u0003\u0002\u0002\u0002~|\u0003",
    "\u0002\u0002\u0002~\u007f\u0003\u0002\u0002\u0002\u007f\u0081\u0003",
    "\u0002\u0002\u0002\u0080~\u0003\u0002\u0002\u0002\u0081\u0085\u0007",
    "\u0007\u0002\u0002\u0082\u0084\u0005\u0010\t\u0002\u0083\u0082\u0003",
    "\u0002\u0002\u0002\u0084\u0087\u0003\u0002\u0002\u0002\u0085\u0083\u0003",
    "\u0002\u0002\u0002\u0085\u0086\u0003\u0002\u0002\u0002\u0086\u0088\u0003",
    "\u0002\u0002\u0002\u0087\u0085\u0003\u0002\u0002\u0002\u0088\u0089\u0005",
    "\u0012\n\u0002\u0089\u000f\u0003\u0002\u0002\u0002\u008a\u008b\u0005",
    "$\u0013\u0002\u008b\u008c\u0007\r\u0002\u0002\u008c\u008d\u0005\u0012",
    "\n\u0002\u008d\u008e\u0007\u0010\u0002\u0002\u008e\u0011\u0003\u0002",
    "\u0002\u0002\u008f\u0090\b\n\u0001\u0002\u0090\u0091\u0007\u0006\u0002",
    "\u0002\u0091\u0092\u0005\u0012\n\u0002\u0092\u0093\u0007\u0007\u0002",
    "\u0002\u0093\u00a5\u0003\u0002\u0002\u0002\u0094\u0095\u00074\u0002",
    "\u0002\u0095\u0096\u0005\u0012\n\u0002\u0096\u0097\u0005\u0012\n\u0002",
    "\u0097\u0098\u0007:\u0002\u0002\u0098\u0099\u0005\u0012\n\u0012\u0099",
    "\u00a5\u0003\u0002\u0002\u0002\u009a\u009b\t\u0003\u0002\u0002\u009b",
    "\u00a5\u0005\u0012\n\n\u009c\u009e\u0005&\u0014\u0002\u009d\u009f\u0005",
    "\u0014\u000b\u0002\u009e\u009d\u0003\u0002\u0002\u0002\u009e\u009f\u0003",
    "\u0002\u0002\u0002\u009f\u00a5\u0003\u0002\u0002\u0002\u00a0\u00a5\u0005",
    "(\u0015\u0002\u00a1\u00a5\u0005\u0016\f\u0002\u00a2\u00a5\u0005\u001c",
    "\u000f\u0002\u00a3\u00a5\u0005\u001e\u0010\u0002\u00a4\u008f\u0003\u0002",
    "\u0002\u0002\u00a4\u0094\u0003\u0002\u0002\u0002\u00a4\u009a\u0003\u0002",
    "\u0002\u0002\u00a4\u009c\u0003\u0002\u0002\u0002\u00a4\u00a0\u0003\u0002",
    "\u0002\u0002\u00a4\u00a1\u0003\u0002\u0002\u0002\u00a4\u00a2\u0003\u0002",
    "\u0002\u0002\u00a4\u00a3\u0003\u0002\u0002\u0002\u00a5\u00ce\u0003\u0002",
    "\u0002\u0002\u00a6\u00a7\f\u0011\u0002\u0002\u00a7\u00a8\u0007E\u0002",
    "\u0002\u00a8\u00cd\u0005\u0012\n\u0012\u00a9\u00aa\f\u0010\u0002\u0002",
    "\u00aa\u00ab\u0007*\u0002\u0002\u00ab\u00cd\u0005\u0012\n\u0011\u00ac",
    "\u00ad\f\u000f\u0002\u0002\u00ad\u00ae\t\u0004\u0002\u0002\u00ae\u00cd",
    "\u0005\u0012\n\u0010\u00af\u00b1\f\u000e\u0002\u0002\u00b0\u00b2\u0007",
    "+\u0002\u0002\u00b1\u00b0\u0003\u0002\u0002\u0002\u00b1\u00b2\u0003",
    "\u0002\u0002\u0002\u00b2\u00b3\u0003\u0002\u0002\u0002\u00b3\u00b4\u0007",
    "3\u0002\u0002\u00b4\u00cd\u0005\u0012\n\u000f\u00b5\u00b6\f\r\u0002",
    "\u0002\u00b6\u00b7\t\u0005\u0002\u0002\u00b7\u00cd\u0005\u0012\n\u000e",
    "\u00b8\u00b9\f\f\u0002\u0002\u00b9\u00ba\t\u0006\u0002\u0002\u00ba\u00cd",
    "\u0005\u0012\n\r\u00bb\u00bc\f\u000b\u0002\u0002\u00bc\u00bd\u0007\u0013",
    "\u0002\u0002\u00bd\u00cd\u0005\u0012\n\f\u00be\u00bf\f\u0013\u0002\u0002",
    "\u00bf\u00c0\u0007\u0018\u0002\u0002\u00c0\u00cd\u0005$\u0013\u0002",
    "\u00c1\u00c2\f\t\u0002\u0002\u00c2\u00c3\u0007\u000e\u0002\u0002\u00c3",
    "\u00c5\u0005&\u0014\u0002\u00c4\u00c6\u0005\u0014\u000b\u0002\u00c5",
    "\u00c4\u0003\u0002\u0002\u0002\u00c5\u00c6\u0003\u0002\u0002\u0002\u00c6",
    "\u00cd\u0003\u0002\u0002\u0002\u00c7\u00c8\f\u0007\u0002\u0002\u00c8",
    "\u00c9\u0007\u0004\u0002\u0002\u00c9\u00ca\u0005.\u0018\u0002\u00ca",
    "\u00cb\u0007\u0005\u0002\u0002\u00cb\u00cd\u0003\u0002\u0002\u0002\u00cc",
    "\u00a6\u0003\u0002\u0002\u0002\u00cc\u00a9\u0003\u0002\u0002\u0002\u00cc",
    "\u00ac\u0003\u0002\u0002\u0002\u00cc\u00af\u0003\u0002\u0002\u0002\u00cc",
    "\u00b5\u0003\u0002\u0002\u0002\u00cc\u00b8\u0003\u0002\u0002\u0002\u00cc",
    "\u00bb\u0003\u0002\u0002\u0002\u00cc\u00be\u0003\u0002\u0002\u0002\u00cc",
    "\u00c1\u0003\u0002\u0002\u0002\u00cc\u00c7\u0003\u0002\u0002\u0002\u00cd",
    "\u00d0\u0003\u0002\u0002\u0002\u00ce\u00cc\u0003\u0002\u0002\u0002\u00ce",
    "\u00cf\u0003\u0002\u0002\u0002\u00cf\u0013\u0003\u0002\u0002\u0002\u00d0",
    "\u00ce\u0003\u0002\u0002\u0002\u00d1\u00da\u0007\u0006\u0002\u0002\u00d2",
    "\u00d7\u0005\u0012\n\u0002\u00d3\u00d4\u0007\u0019\u0002\u0002\u00d4",
    "\u00d6\u0005\u0012\n\u0002\u00d5\u00d3\u0003\u0002\u0002\u0002\u00d6",
    "\u00d9\u0003\u0002\u0002\u0002\u00d7\u00d5\u0003\u0002\u0002\u0002\u00d7",
    "\u00d8\u0003\u0002\u0002\u0002\u00d8\u00db\u0003\u0002\u0002\u0002\u00d9",
    "\u00d7\u0003\u0002\u0002\u0002\u00da\u00d2\u0003\u0002\u0002\u0002\u00da",
    "\u00db\u0003\u0002\u0002\u0002\u00db\u00dc\u0003\u0002\u0002\u0002\u00dc",
    "\u00dd\u0007\u0007\u0002\u0002\u00dd\u0015\u0003\u0002\u0002\u0002\u00de",
    "\u00e8\u0007\n\u0002\u0002\u00df\u00e0\u0007\b\u0002\u0002\u00e0\u00e1",
    "\u0005\u0018\r\u0002\u00e1\u00e2\u0007\t\u0002\u0002\u00e2\u00e8\u0003",
    "\u0002\u0002\u0002\u00e3\u00e4\u0007\u0004\u0002\u0002\u00e4\u00e5\u0005",
    "\u0018\r\u0002\u00e5\u00e6\u0007\u0005\u0002\u0002\u00e6\u00e8\u0003",
    "\u0002\u0002\u0002\u00e7\u00de\u0003\u0002\u0002\u0002\u00e7\u00df\u0003",
    "\u0002\u0002\u0002\u00e7\u00e3\u0003\u0002\u0002\u0002\u00e8\u0017\u0003",
    "\u0002\u0002\u0002\u00e9\u00f1\u0007\n\u0002\u0002\u00ea\u00ec\u0005",
    "\u001a\u000e\u0002\u00eb\u00ea\u0003\u0002\u0002\u0002\u00ec\u00ef\u0003",
    "\u0002\u0002\u0002\u00ed\u00eb\u0003\u0002\u0002\u0002\u00ed\u00ee\u0003",
    "\u0002\u0002\u0002\u00ee\u00f1\u0003\u0002\u0002\u0002\u00ef\u00ed\u0003",
    "\u0002\u0002\u0002\u00f0\u00e9\u0003\u0002\u0002\u0002\u00f0\u00ed\u0003",
    "\u0002\u0002\u0002\u00f1\u0019\u0003\u0002\u0002\u0002\u00f2\u00f4\u0007",
    "\n\u0002\u0002\u00f3\u00f5\u0007\n\u0002\u0002\u00f4\u00f3\u0003\u0002",
    "\u0002\u0002\u00f4\u00f5\u0003\u0002\u0002\u0002\u00f5\u00fd\u0003\u0002",
    "\u0002\u0002\u00f6\u00f7\u0007A\u0002\u0002\u00f7\u00f9\u0007\r\u0002",
    "\u0002\u00f8\u00f6\u0003\u0002\u0002\u0002\u00f8\u00f9\u0003\u0002\u0002",
    "\u0002\u00f9\u00fe\u0003\u0002\u0002\u0002\u00fa\u00fb\u0005&\u0014",
    "\u0002\u00fb\u00fc\u0007\r\u0002\u0002\u00fc\u00fe\u0003\u0002\u0002",
    "\u0002\u00fd\u00f8\u0003\u0002\u0002\u0002\u00fd\u00fa\u0003\u0002\u0002",
    "\u0002\u00fe\u0101\u0003\u0002\u0002\u0002\u00ff\u0102\u0005\u0012\n",
    "\u0002\u0100\u0102\u0007\u0016\u0002\u0002\u0101\u00ff\u0003\u0002\u0002",
    "\u0002\u0101\u0100\u0003\u0002\u0002\u0002\u0102\u0105\u0003\u0002\u0002",
    "\u0002\u0103\u0104\u0007D\u0002\u0002\u0104\u0106\u0005$\u0013\u0002",
    "\u0105\u0103\u0003\u0002\u0002\u0002\u0105\u0106\u0003\u0002\u0002\u0002",
    "\u0106\u0109\u0003\u0002\u0002\u0002\u0107\u0108\u0007\u001c\u0002\u0002",
    "\u0108\u010a\u0005\u0012\n\u0002\u0109\u0107\u0003\u0002\u0002\u0002",
    "\u0109\u010a\u0003\u0002\u0002\u0002\u010a\u001b\u0003\u0002\u0002\u0002",
    "\u010b\u010c\u00077\u0002\u0002\u010c\u0115\u0005\u0012\n\u0002\u010d",
    "\u0111\u0007\u001c\u0002\u0002\u010e\u0110\u0005\u0010\t\u0002\u010f",
    "\u010e\u0003\u0002\u0002\u0002\u0110\u0113\u0003\u0002\u0002\u0002\u0111",
    "\u010f\u0003\u0002\u0002\u0002\u0111\u0112\u0003\u0002\u0002\u0002\u0112",
    "\u0114\u0003\u0002\u0002\u0002\u0113\u0111\u0003\u0002\u0002\u0002\u0114",
    "\u0116\u0005\u0012\n\u0002\u0115\u010d\u0003\u0002\u0002\u0002\u0115",
    "\u0116\u0003\u0002\u0002\u0002\u0116\u0119\u0003\u0002\u0002\u0002\u0117",
    "\u0118\u0007\'\u0002\u0002\u0118\u011a\u0005\u0012\n\u0002\u0119\u0117",
    "\u0003\u0002\u0002\u0002\u0119\u011a\u0003\u0002\u0002\u0002\u011a\u001d",
    "\u0003\u0002\u0002\u0002\u011b\u011d\u0007.\u0002\u0002\u011c\u011e",
    "\u0007;\u0002\u0002\u011d\u011c\u0003\u0002\u0002\u0002\u011d\u011e",
    "\u0003\u0002\u0002\u0002\u011e\u0120\u0003\u0002\u0002\u0002\u011f\u0121",
    "\u0005\"\u0012\u0002\u0120\u011f\u0003\u0002\u0002\u0002\u0120\u0121",
    "\u0003\u0002\u0002\u0002\u0121\u0122\u0003\u0002\u0002\u0002\u0122\u0124",
    "\u0005$\u0013\u0002\u0123\u0125\u0007G\u0002\u0002\u0124\u0123\u0003",
    "\u0002\u0002\u0002\u0124\u0125\u0003\u0002\u0002\u0002\u0125\u0128\u0003",
    "\u0002\u0002\u0002\u0126\u0127\u00072\u0002\u0002\u0127\u0129\u0007",
    "$\u0002\u0002\u0128\u0126\u0003\u0002\u0002\u0002\u0128\u0129\u0003",
    "\u0002\u0002\u0002\u0129\u012c\u0003\u0002\u0002\u0002\u012a\u012b\u0007",
    "&\u0002\u0002\u012b\u012d\u0005\"\u0012\u0002\u012c\u012a\u0003\u0002",
    "\u0002\u0002\u012c\u012d\u0003\u0002\u0002\u0002\u012d\u0130\u0003\u0002",
    "\u0002\u0002\u012e\u012f\u00076\u0002\u0002\u012f\u0131\u0005\u0012",
    "\n\u0002\u0130\u012e\u0003\u0002\u0002\u0002\u0130\u0131\u0003\u0002",
    "\u0002\u0002\u0131\u0134\u0003\u0002\u0002\u0002\u0132\u0133\u0007\"",
    "\u0002\u0002\u0133\u0135\u0005\u0012\n\u0002\u0134\u0132\u0003\u0002",
    "\u0002\u0002\u0134\u0135\u0003\u0002\u0002\u0002\u0135\u0138\u0003\u0002",
    "\u0002\u0002\u0136\u0137\u0007>\u0002\u0002\u0137\u0139\u0005$\u0013",
    "\u0002\u0138\u0136\u0003\u0002\u0002\u0002\u0138\u0139\u0003\u0002\u0002",
    "\u0002\u0139\u013c\u0003\u0002\u0002\u0002\u013a\u013b\u0007!\u0002",
    "\u0002\u013b\u013d\u0005\u0012\n\u0002\u013c\u013a\u0003\u0002\u0002",
    "\u0002\u013c\u013d\u0003\u0002\u0002\u0002\u013d\u0141\u0003\u0002\u0002",
    "\u0002\u013e\u013f\u0007#\u0002\u0002\u013f\u0140\u0007\u001d\u0002",
    "\u0002\u0140\u0142\u0005\u0012\n\u0002\u0141\u013e\u0003\u0002\u0002",
    "\u0002\u0141\u0142\u0003\u0002\u0002\u0002\u0142\u0145\u0003\u0002\u0002",
    "\u0002\u0143\u0144\u0007\u001c\u0002\u0002\u0144\u0146\u0005\u0012\n",
    "\u0002\u0145\u0143\u0003\u0002\u0002\u0002\u0145\u0146\u0003\u0002\u0002",
    "\u0002\u0146\u0154\u0003\u0002\u0002\u0002\u0147\u014e\u0007\'\u0002",
    "\u0002\u0148\u0149\u0007B\u0002\u0002\u0149\u014b\u0007-\u0002\u0002",
    "\u014a\u014c\u0005 \u0011\u0002\u014b\u014a\u0003\u0002\u0002\u0002",
    "\u014b\u014c\u0003\u0002\u0002\u0002\u014c\u014f\u0003\u0002\u0002\u0002",
    "\u014d\u014f\u0005 \u0011\u0002\u014e\u0148\u0003\u0002\u0002\u0002",
    "\u014e\u014d\u0003\u0002\u0002\u0002\u014f\u0152\u0003\u0002\u0002\u0002",
    "\u0150\u0151\u0007D\u0002\u0002\u0151\u0153\u0007<\u0002\u0002\u0152",
    "\u0150\u0003\u0002\u0002\u0002\u0152\u0153\u0003\u0002\u0002\u0002\u0153",
    "\u0155\u0003\u0002\u0002\u0002\u0154\u0147\u0003\u0002\u0002\u0002\u0154",
    "\u0155\u0003\u0002\u0002\u0002\u0155\u001f\u0003\u0002\u0002\u0002\u0156",
    "\u0163\u0005\u0012\n\u0002\u0157\u0158\u0007\u0006\u0002\u0002\u0158",
    "\u015d\u0005\u0012\n\u0002\u0159\u015a\u0007\u0019\u0002\u0002\u015a",
    "\u015c\u0005\u0012\n\u0002\u015b\u0159\u0003\u0002\u0002\u0002\u015c",
    "\u015f\u0003\u0002\u0002\u0002\u015d\u015b\u0003\u0002\u0002\u0002\u015d",
    "\u015e\u0003\u0002\u0002\u0002\u015e\u0160\u0003\u0002\u0002\u0002\u015f",
    "\u015d\u0003\u0002\u0002\u0002\u0160\u0161\u0007\u0007\u0002\u0002\u0161",
    "\u0163\u0003\u0002\u0002\u0002\u0162\u0156\u0003\u0002\u0002\u0002\u0162",
    "\u0157\u0003\u0002\u0002\u0002\u0163!\u0003\u0002\u0002\u0002\u0164",
    "\u0167\u0005$\u0013\u0002\u0165\u0167\u0005.\u0018\u0002\u0166\u0164",
    "\u0003\u0002\u0002\u0002\u0166\u0165\u0003\u0002\u0002\u0002\u0167#",
    "\u0003\u0002\u0002\u0002\u0168\u0169\t\u0007\u0002\u0002\u0169%\u0003",
    "\u0002\u0002\u0002\u016a\u0170\u0005$\u0013\u0002\u016b\u0170\u0007",
    "H\u0002\u0002\u016c\u016d\u0007A\u0002\u0002\u016d\u016e\u0007\u000e",
    "\u0002\u0002\u016e\u0170\u0005&\u0014\u0002\u016f\u016a\u0003\u0002",
    "\u0002\u0002\u016f\u016b\u0003\u0002\u0002\u0002\u016f\u016c\u0003\u0002",
    "\u0002\u0002\u0170\'\u0003\u0002\u0002\u0002\u0171\u0175\u0005.\u0018",
    "\u0002\u0172\u0175\u0007F\u0002\u0002\u0173\u0175\u0005,\u0017\u0002",
    "\u0174\u0171\u0003\u0002\u0002\u0002\u0174\u0172\u0003\u0002\u0002\u0002",
    "\u0174\u0173\u0003\u0002\u0002\u0002\u0175)\u0003\u0002\u0002\u0002",
    "\u0176\u0177\u0005$\u0013\u0002\u0177\u0178\u0007\u000f\u0002\u0002",
    "\u0178\u0179\u0005$\u0013\u0002\u0179+\u0003\u0002\u0002\u0002\u017a",
    "\u017b\t\b\u0002\u0002\u017b-\u0003\u0002\u0002\u0002\u017c\u017d\t",
    "\t\u0002\u0002\u017d/\u0003\u0002\u0002\u0002935=KOQXZegkmo~\u0085\u009e",
    "\u00a4\u00b1\u00c5\u00cc\u00ce\u00d7\u00da\u00e7\u00ed\u00f0\u00f4\u00f8",
    "\u00fd\u0101\u0105\u0109\u0111\u0115\u0119\u011d\u0120\u0124\u0128\u012c",
    "\u0130\u0134\u0138\u013c\u0141\u0145\u014b\u014e\u0152\u0154\u015d\u0162",
    "\u0166\u016f\u0174"].join("");


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
                      "FILTER", "FALSE", "ENTITY", "ELSE", "DIMENSIONS", 
                      "DICTIONARY", "DEBIT", "CUBE", "CREDIT", "CONSTANT", 
                      "CONCEPT", "BY", "ASSERT", "AS", "AND", "NUMBER", 
                      "INTEGER", "ACCESSOR", "IDENTIFIER", "NAME", "WS", 
                      "UNRECOGNIZED_TOKEN", "ASSERT_UNSATISFIED", "ASSERT_SATISFIED", 
                      "ASSERT_RULE_NAME", "ASSERT_WS" ];

var ruleNames =  [ "xuleFile", "topLevelDeclaration", "namespaceDeclaration", 
                   "output", "assertion", "constantDeclaration", "functionDeclaration", 
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
XULEParser.DIMENSIONS = 57;
XULEParser.DICTIONARY = 58;
XULEParser.DEBIT = 59;
XULEParser.CUBE = 60;
XULEParser.CREDIT = 61;
XULEParser.CONSTANT = 62;
XULEParser.CONCEPT = 63;
XULEParser.BY = 64;
XULEParser.ASSERT = 65;
XULEParser.AS = 66;
XULEParser.AND = 67;
XULEParser.NUMBER = 68;
XULEParser.INTEGER = 69;
XULEParser.ACCESSOR = 70;
XULEParser.IDENTIFIER = 71;
XULEParser.NAME = 72;
XULEParser.WS = 73;
XULEParser.UNRECOGNIZED_TOKEN = 74;
XULEParser.ASSERT_UNSATISFIED = 75;
XULEParser.ASSERT_SATISFIED = 76;
XULEParser.ASSERT_RULE_NAME = 77;
XULEParser.ASSERT_WS = 78;

XULEParser.RULE_xuleFile = 0;
XULEParser.RULE_topLevelDeclaration = 1;
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

XuleFileContext.prototype.topLevelDeclaration = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(TopLevelDeclarationContext);
    } else {
        return this.getTypedRuleContext(TopLevelDeclarationContext,i);
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
                this.topLevelDeclaration();
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


function TopLevelDeclarationContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_topLevelDeclaration;
    return this;
}

TopLevelDeclarationContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
TopLevelDeclarationContext.prototype.constructor = TopLevelDeclarationContext;

TopLevelDeclarationContext.prototype.namespaceDeclaration = function() {
    return this.getTypedRuleContext(NamespaceDeclarationContext,0);
};

TopLevelDeclarationContext.prototype.constantDeclaration = function() {
    return this.getTypedRuleContext(ConstantDeclarationContext,0);
};

TopLevelDeclarationContext.prototype.functionDeclaration = function() {
    return this.getTypedRuleContext(FunctionDeclarationContext,0);
};

TopLevelDeclarationContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.enterTopLevelDeclaration(this);
	}
};

TopLevelDeclarationContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEParserListener ) {
        listener.exitTopLevelDeclaration(this);
	}
};




XULEParser.TopLevelDeclarationContext = TopLevelDeclarationContext;

XULEParser.prototype.topLevelDeclaration = function() {

    var localctx = new TopLevelDeclarationContext(this, this._ctx, this.state);
    this.enterRule(localctx, 2, XULEParser.RULE_topLevelDeclaration);
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

OutputContext.prototype.SEMI = function() {
    return this.getToken(XULEParser.SEMI, 0);
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
        this.state = 88;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.MESSAGE) {
            this.state = 83;
            this.match(XULEParser.MESSAGE);
            this.state = 84;
            this.expression(0);
            this.state = 86;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            if(_la===XULEParser.SEMI) {
                this.state = 85;
                this.match(XULEParser.SEMI);
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

AssertionContext.prototype.MESSAGE = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.MESSAGE);
    } else {
        return this.getToken(XULEParser.MESSAGE, i);
    }
};


AssertionContext.prototype.SEVERITY = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.SEVERITY);
    } else {
        return this.getToken(XULEParser.SEVERITY, i);
    }
};


AssertionContext.prototype.SEMI = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(XULEParser.SEMI);
    } else {
        return this.getToken(XULEParser.SEMI, i);
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
    this.enterRule(localctx, 8, XULEParser.RULE_assertion);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 90;
        this.match(XULEParser.ASSERT);
        this.state = 91;
        this.match(XULEParser.ASSERT_RULE_NAME);
        this.state = 92;
        _la = this._input.LA(1);
        if(!(_la===XULEParser.ASSERT_UNSATISFIED || _la===XULEParser.ASSERT_SATISFIED)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
        this.state = 107; 
        this._errHandler.sync(this);
        var _alt = 1;
        do {
        	switch (_alt) {
        	case 1:
        		this.state = 107;
        		this._errHandler.sync(this);
        		var la_ = this._interp.adaptivePredict(this._input,11,this._ctx);
        		switch(la_) {
        		case 1:
        		    this.state = 93;
        		    this.constantDeclaration();
        		    break;

        		case 2:
        		    this.state = 94;
        		    this.assignment();
        		    break;

        		case 3:
        		    this.state = 95;
        		    this.expression(0);
        		    this.state = 101;
        		    this._errHandler.sync(this);
        		    _la = this._input.LA(1);
        		    if(_la===XULEParser.MESSAGE) {
        		        this.state = 96;
        		        this.match(XULEParser.MESSAGE);
        		        this.state = 97;
        		        this.expression(0);
        		        this.state = 99;
        		        this._errHandler.sync(this);
        		        _la = this._input.LA(1);
        		        if(_la===XULEParser.SEMI) {
        		            this.state = 98;
        		            this.match(XULEParser.SEMI);
        		        }

        		    }

        		    this.state = 105;
        		    this._errHandler.sync(this);
        		    _la = this._input.LA(1);
        		    if(_la===XULEParser.SEVERITY) {
        		        this.state = 103;
        		        this.match(XULEParser.SEVERITY);
        		        this.state = 104;
        		        this.expression(0);
        		    }

        		    break;

        		}
        		break;
        	default:
        		throw new antlr4.error.NoViableAltException(this);
        	}
        	this.state = 109; 
        	this._errHandler.sync(this);
        	_alt = this._interp.adaptivePredict(this._input,12, this._ctx);
        } while ( _alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER );
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
        this.state = 111;
        this.match(XULEParser.CONSTANT);
        this.state = 112;
        this.identifier();
        this.state = 113;
        this.match(XULEParser.ASSIGN);
        this.state = 114;
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
        this.state = 116;
        this.match(XULEParser.FUNCTION);
        this.state = 117;
        this.identifier();
        this.state = 118;
        this.match(XULEParser.OPEN_PAREN);
        this.state = 119;
        this.identifier();
        this.state = 124;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while(_la===XULEParser.COMMA) {
            this.state = 120;
            this.match(XULEParser.COMMA);
            this.state = 121;
            this.identifier();
            this.state = 126;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
        }
        this.state = 127;
        this.match(XULEParser.CLOSE_PAREN);
        this.state = 131;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,14,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                this.state = 128;
                this.assignment(); 
            }
            this.state = 133;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,14,this._ctx);
        }

        this.state = 134;
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
        this.state = 136;
        this.identifier();
        this.state = 137;
        this.match(XULEParser.ASSIGN);
        this.state = 138;
        this.expression(0);
        this.state = 139;
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

ExpressionContext.prototype.PLUS = function() {
    return this.getToken(XULEParser.PLUS, 0);
};

ExpressionContext.prototype.MINUS = function() {
    return this.getToken(XULEParser.MINUS, 0);
};

ExpressionContext.prototype.NOT = function() {
    return this.getToken(XULEParser.NOT, 0);
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

ExpressionContext.prototype.navigation = function() {
    return this.getTypedRuleContext(NavigationContext,0);
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
        this.state = 162;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.OPEN_PAREN:
            this.state = 142;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 143;
            this.expression(0);
            this.state = 144;
            this.match(XULEParser.CLOSE_PAREN);
            break;
        case XULEParser.IF:
            this.state = 146;
            this.match(XULEParser.IF);
            this.state = 147;
            this.expression(0);
            this.state = 148;
            this.expression(0);
            this.state = 149;
            this.match(XULEParser.ELSE);
            this.state = 150;
            this.expression(16);
            break;
        case XULEParser.PLUS:
        case XULEParser.MINUS:
        case XULEParser.NOT:
            this.state = 152;
            _la = this._input.LA(1);
            if(!(((((_la - 18)) & ~0x1f) == 0 && ((1 << (_la - 18)) & ((1 << (XULEParser.PLUS - 18)) | (1 << (XULEParser.MINUS - 18)) | (1 << (XULEParser.NOT - 18)))) !== 0))) {
            this._errHandler.recoverInline(this);
            }
            else {
            	this._errHandler.reportMatch(this);
                this.consume();
            }
            this.state = 153;
            this.expression(8);
            break;
        case XULEParser.TAXONOMY:
        case XULEParser.PERIOD:
        case XULEParser.CONCEPT:
        case XULEParser.ACCESSOR:
        case XULEParser.IDENTIFIER:
            this.state = 154;
            this.access();
            this.state = 156;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,15,this._ctx);
            if(la_===1) {
                this.state = 155;
                this.parametersList();

            }
            break;
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
        case XULEParser.TRUE:
        case XULEParser.FALSE:
        case XULEParser.NUMBER:
            this.state = 158;
            this.literal();
            break;
        case XULEParser.OPEN_BRACKET:
        case XULEParser.OPEN_CURLY:
        case XULEParser.AT:
            this.state = 159;
            this.factset();
            break;
        case XULEParser.FILTER:
            this.state = 160;
            this.filter();
            break;
        case XULEParser.NAVIGATE:
            this.state = 161;
            this.navigation();
            break;
        default:
            throw new antlr4.error.NoViableAltException(this);
        }
        this._ctx.stop = this._input.LT(-1);
        this.state = 204;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,20,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                if(this._parseListeners!==null) {
                    this.triggerExitRuleEvent();
                }
                _prevctx = localctx;
                this.state = 202;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,19,this._ctx);
                switch(la_) {
                case 1:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 164;
                    if (!( this.precpred(this._ctx, 15))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 15)");
                    }
                    this.state = 165;
                    this.match(XULEParser.AND);
                    this.state = 166;
                    this.expression(16);
                    break;

                case 2:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 167;
                    if (!( this.precpred(this._ctx, 14))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 14)");
                    }
                    this.state = 168;
                    this.match(XULEParser.OR);
                    this.state = 169;
                    this.expression(15);
                    break;

                case 3:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 170;
                    if (!( this.precpred(this._ctx, 13))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 13)");
                    }
                    this.state = 171;
                    _la = this._input.LA(1);
                    if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.NOT_EQUALS) | (1 << XULEParser.EQUALS) | (1 << XULEParser.GREATER_THAN) | (1 << XULEParser.LESS_THAN))) !== 0))) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 172;
                    this.expression(14);
                    break;

                case 4:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 173;
                    if (!( this.precpred(this._ctx, 12))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 12)");
                    }
                    this.state = 175;
                    this._errHandler.sync(this);
                    _la = this._input.LA(1);
                    if(_la===XULEParser.NOT) {
                        this.state = 174;
                        this.match(XULEParser.NOT);
                    }

                    this.state = 177;
                    this.match(XULEParser.IN);
                    this.state = 178;
                    this.expression(13);
                    break;

                case 5:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 179;
                    if (!( this.precpred(this._ctx, 11))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 11)");
                    }
                    this.state = 180;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.PLUS || _la===XULEParser.MINUS)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 181;
                    this.expression(12);
                    break;

                case 6:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 182;
                    if (!( this.precpred(this._ctx, 10))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 10)");
                    }
                    this.state = 183;
                    _la = this._input.LA(1);
                    if(!(_la===XULEParser.TIMES || _la===XULEParser.DIV)) {
                    this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 184;
                    this.expression(11);
                    break;

                case 7:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 185;
                    if (!( this.precpred(this._ctx, 9))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 9)");
                    }
                    this.state = 186;
                    this.match(XULEParser.EXP);
                    this.state = 187;
                    this.expression(10);
                    break;

                case 8:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 188;
                    if (!( this.precpred(this._ctx, 17))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 17)");
                    }
                    this.state = 189;
                    this.match(XULEParser.SHARP);
                    this.state = 190;
                    this.identifier();
                    break;

                case 9:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 191;
                    if (!( this.precpred(this._ctx, 7))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 7)");
                    }
                    this.state = 192;
                    this.match(XULEParser.DOT);
                    this.state = 193;
                    this.access();
                    this.state = 195;
                    this._errHandler.sync(this);
                    var la_ = this._interp.adaptivePredict(this._input,18,this._ctx);
                    if(la_===1) {
                        this.state = 194;
                        this.parametersList();

                    }
                    break;

                case 10:
                    localctx = new ExpressionContext(this, _parentctx, _parentState);
                    this.pushNewRecursionContext(localctx, _startState, XULEParser.RULE_expression);
                    this.state = 197;
                    if (!( this.precpred(this._ctx, 5))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 5)");
                    }
                    this.state = 198;
                    this.match(XULEParser.OPEN_BRACKET);
                    this.state = 199;
                    this.stringLiteral();
                    this.state = 200;
                    this.match(XULEParser.CLOSE_BRACKET);
                    break;

                } 
            }
            this.state = 206;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,20,this._ctx);
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
        this.state = 207;
        this.match(XULEParser.OPEN_PAREN);
        this.state = 216;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.OPEN_BRACKET) | (1 << XULEParser.OPEN_PAREN) | (1 << XULEParser.OPEN_CURLY) | (1 << XULEParser.AT) | (1 << XULEParser.PLUS) | (1 << XULEParser.MINUS) | (1 << XULEParser.DOUBLE_QUOTED_STRING) | (1 << XULEParser.SINGLE_QUOTED_STRING) | (1 << XULEParser.TRUE))) !== 0) || ((((_la - 32)) & ~0x1f) == 0 && ((1 << (_la - 32)) & ((1 << (XULEParser.TAXONOMY - 32)) | (1 << (XULEParser.PERIOD - 32)) | (1 << (XULEParser.NOT - 32)) | (1 << (XULEParser.NAVIGATE - 32)) | (1 << (XULEParser.IF - 32)) | (1 << (XULEParser.FILTER - 32)) | (1 << (XULEParser.FALSE - 32)) | (1 << (XULEParser.CONCEPT - 32)))) !== 0) || ((((_la - 68)) & ~0x1f) == 0 && ((1 << (_la - 68)) & ((1 << (XULEParser.NUMBER - 68)) | (1 << (XULEParser.ACCESSOR - 68)) | (1 << (XULEParser.IDENTIFIER - 68)))) !== 0)) {
            this.state = 208;
            this.expression(0);
            this.state = 213;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.COMMA) {
                this.state = 209;
                this.match(XULEParser.COMMA);
                this.state = 210;
                this.expression(0);
                this.state = 215;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }
        }

        this.state = 218;
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

FactsetContext.prototype.AT = function() {
    return this.getToken(XULEParser.AT, 0);
};

FactsetContext.prototype.OPEN_CURLY = function() {
    return this.getToken(XULEParser.OPEN_CURLY, 0);
};

FactsetContext.prototype.factsetBody = function() {
    return this.getTypedRuleContext(FactsetBodyContext,0);
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
        this.state = 229;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.AT:
            this.enterOuterAlt(localctx, 1);
            this.state = 220;
            this.match(XULEParser.AT);
            break;
        case XULEParser.OPEN_CURLY:
            this.enterOuterAlt(localctx, 2);
            this.state = 221;
            this.match(XULEParser.OPEN_CURLY);
            this.state = 222;
            this.factsetBody();
            this.state = 223;
            this.match(XULEParser.CLOSE_CURLY);
            break;
        case XULEParser.OPEN_BRACKET:
            this.enterOuterAlt(localctx, 3);
            this.state = 225;
            this.match(XULEParser.OPEN_BRACKET);
            this.state = 226;
            this.factsetBody();
            this.state = 227;
            this.match(XULEParser.CLOSE_BRACKET);
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
    var _la = 0; // Token type
    try {
        this.state = 238;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,25,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 231;
            this.match(XULEParser.AT);
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 235;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.AT) {
                this.state = 232;
                this.aspectFilter();
                this.state = 237;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
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

AspectFilterContext.prototype.expression = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExpressionContext);
    } else {
        return this.getTypedRuleContext(ExpressionContext,i);
    }
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

AspectFilterContext.prototype.WHERE = function() {
    return this.getToken(XULEParser.WHERE, 0);
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
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 240;
        this.match(XULEParser.AT);
        this.state = 242;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,26,this._ctx);
        if(la_===1) {
            this.state = 241;
            this.match(XULEParser.AT);

        }
        this.state = 251;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,28,this._ctx);
        switch(la_) {
        case 1:
            this.state = 246;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,27,this._ctx);
            if(la_===1) {
                this.state = 244;
                this.match(XULEParser.CONCEPT);
                this.state = 245;
                this.match(XULEParser.ASSIGN);

            }
            break;

        case 2:
            this.state = 248;
            this.access();
            this.state = 249;
            this.match(XULEParser.ASSIGN);
            break;

        }
        this.state = 255;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.OPEN_BRACKET:
        case XULEParser.OPEN_PAREN:
        case XULEParser.OPEN_CURLY:
        case XULEParser.AT:
        case XULEParser.PLUS:
        case XULEParser.MINUS:
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
        case XULEParser.TRUE:
        case XULEParser.TAXONOMY:
        case XULEParser.PERIOD:
        case XULEParser.NOT:
        case XULEParser.NAVIGATE:
        case XULEParser.IF:
        case XULEParser.FILTER:
        case XULEParser.FALSE:
        case XULEParser.CONCEPT:
        case XULEParser.NUMBER:
        case XULEParser.ACCESSOR:
        case XULEParser.IDENTIFIER:
            this.state = 253;
            this.expression(0);
            break;
        case XULEParser.TIMES:
            this.state = 254;
            this.match(XULEParser.TIMES);
            break;
        default:
            throw new antlr4.error.NoViableAltException(this);
        }
        this.state = 259;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.AS) {
            this.state = 257;
            this.match(XULEParser.AS);
            this.state = 258;
            this.identifier();
        }

        this.state = 263;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.WHERE) {
            this.state = 261;
            this.match(XULEParser.WHERE);
            this.state = 262;
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
        this.state = 265;
        this.match(XULEParser.FILTER);
        this.state = 266;
        this.expression(0);
        this.state = 275;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,33,this._ctx);
        if(la_===1) {
            this.state = 267;
            this.match(XULEParser.WHERE);
            this.state = 271;
            this._errHandler.sync(this);
            var _alt = this._interp.adaptivePredict(this._input,32,this._ctx)
            while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
                if(_alt===1) {
                    this.state = 268;
                    this.assignment(); 
                }
                this.state = 273;
                this._errHandler.sync(this);
                _alt = this._interp.adaptivePredict(this._input,32,this._ctx);
            }

            this.state = 274;
            this.expression(0);

        }
        this.state = 279;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,34,this._ctx);
        if(la_===1) {
            this.state = 277;
            this.match(XULEParser.RETURNS);
            this.state = 278;
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

NavigationContext.prototype.TAXONOMY = function() {
    return this.getToken(XULEParser.TAXONOMY, 0);
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
        this.state = 281;
        this.match(XULEParser.NAVIGATE);
        this.state = 283;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(_la===XULEParser.DIMENSIONS) {
            this.state = 282;
            this.match(XULEParser.DIMENSIONS);
        }

        this.state = 286;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,36,this._ctx);
        if(la_===1) {
            this.state = 285;
            localctx.arcrole = this.role();

        }
        this.state = 288;
        localctx.direction = this.identifier();
        this.state = 290;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,37,this._ctx);
        if(la_===1) {
            this.state = 289;
            localctx.levels = this.match(XULEParser.INTEGER);

        }
        this.state = 294;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,38,this._ctx);
        if(la_===1) {
            this.state = 292;
            this.match(XULEParser.INCLUDE);
            this.state = 293;
            this.match(XULEParser.START);

        }
        this.state = 298;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,39,this._ctx);
        if(la_===1) {
            this.state = 296;
            this.match(XULEParser.ROLE);
            this.state = 297;
            this.role();

        }
        this.state = 302;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,40,this._ctx);
        if(la_===1) {
            this.state = 300;
            this.match(XULEParser.FROM);
            this.state = 301;
            this.expression(0);

        }
        this.state = 306;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,41,this._ctx);
        if(la_===1) {
            this.state = 304;
            this.match(XULEParser.TAXONOMY);
            this.state = 305;
            this.expression(0);

        }
        this.state = 310;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,42,this._ctx);
        if(la_===1) {
            this.state = 308;
            this.match(XULEParser.CUBE);
            this.state = 309;
            this.identifier();

        }
        this.state = 314;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,43,this._ctx);
        if(la_===1) {
            this.state = 312;
            this.match(XULEParser.TO);
            this.state = 313;
            this.expression(0);

        }
        this.state = 319;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,44,this._ctx);
        if(la_===1) {
            this.state = 316;
            this.match(XULEParser.STOP);
            this.state = 317;
            this.match(XULEParser.WHEN);
            this.state = 318;
            this.expression(0);

        }
        this.state = 323;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,45,this._ctx);
        if(la_===1) {
            this.state = 321;
            this.match(XULEParser.WHERE);
            this.state = 322;
            this.expression(0);

        }
        this.state = 338;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,49,this._ctx);
        if(la_===1) {
            this.state = 325;
            this.match(XULEParser.RETURNS);
            this.state = 332;
            this._errHandler.sync(this);
            switch(this._input.LA(1)) {
            case XULEParser.BY:
                this.state = 326;
                this.match(XULEParser.BY);
                this.state = 327;
                this.match(XULEParser.NETWORK);
                this.state = 329;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,46,this._ctx);
                if(la_===1) {
                    this.state = 328;
                    this.returnExpression();

                }
                break;
            case XULEParser.OPEN_BRACKET:
            case XULEParser.OPEN_PAREN:
            case XULEParser.OPEN_CURLY:
            case XULEParser.AT:
            case XULEParser.PLUS:
            case XULEParser.MINUS:
            case XULEParser.DOUBLE_QUOTED_STRING:
            case XULEParser.SINGLE_QUOTED_STRING:
            case XULEParser.TRUE:
            case XULEParser.TAXONOMY:
            case XULEParser.PERIOD:
            case XULEParser.NOT:
            case XULEParser.NAVIGATE:
            case XULEParser.IF:
            case XULEParser.FILTER:
            case XULEParser.FALSE:
            case XULEParser.CONCEPT:
            case XULEParser.NUMBER:
            case XULEParser.ACCESSOR:
            case XULEParser.IDENTIFIER:
                this.state = 331;
                this.returnExpression();
                break;
            default:
                throw new antlr4.error.NoViableAltException(this);
            }
            this.state = 336;
            this._errHandler.sync(this);
            var la_ = this._interp.adaptivePredict(this._input,48,this._ctx);
            if(la_===1) {
                this.state = 334;
                this.match(XULEParser.AS);
                this.state = 335;
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
        this.state = 352;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,51,this._ctx);
        switch(la_) {
        case 1:
            this.state = 340;
            this.expression(0);
            break;

        case 2:
            this.state = 341;
            this.match(XULEParser.OPEN_PAREN);
            this.state = 342;
            this.expression(0);
            this.state = 347;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.COMMA) {
                this.state = 343;
                this.match(XULEParser.COMMA);
                this.state = 344;
                this.expression(0);
                this.state = 349;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }
            this.state = 350;
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
        this.state = 356;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.TAXONOMY:
        case XULEParser.PERIOD:
        case XULEParser.CONCEPT:
        case XULEParser.IDENTIFIER:
            this.enterOuterAlt(localctx, 1);
            this.state = 354;
            this.identifier();
            break;
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
            this.enterOuterAlt(localctx, 2);
            this.state = 355;
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
        this.state = 358;
        _la = this._input.LA(1);
        if(!(((((_la - 32)) & ~0x1f) == 0 && ((1 << (_la - 32)) & ((1 << (XULEParser.TAXONOMY - 32)) | (1 << (XULEParser.PERIOD - 32)) | (1 << (XULEParser.CONCEPT - 32)))) !== 0) || _la===XULEParser.IDENTIFIER)) {
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
        this.state = 365;
        this._errHandler.sync(this);
        var la_ = this._interp.adaptivePredict(this._input,53,this._ctx);
        switch(la_) {
        case 1:
            this.enterOuterAlt(localctx, 1);
            this.state = 360;
            this.identifier();
            break;

        case 2:
            this.enterOuterAlt(localctx, 2);
            this.state = 361;
            this.match(XULEParser.ACCESSOR);
            break;

        case 3:
            this.enterOuterAlt(localctx, 3);
            this.state = 362;
            this.match(XULEParser.CONCEPT);
            this.state = 363;
            this.match(XULEParser.DOT);
            this.state = 364;
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
        this.state = 370;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.DOUBLE_QUOTED_STRING:
        case XULEParser.SINGLE_QUOTED_STRING:
            this.enterOuterAlt(localctx, 1);
            this.state = 367;
            this.stringLiteral();
            break;
        case XULEParser.NUMBER:
            this.enterOuterAlt(localctx, 2);
            this.state = 368;
            this.match(XULEParser.NUMBER);
            break;
        case XULEParser.TRUE:
        case XULEParser.FALSE:
            this.enterOuterAlt(localctx, 3);
            this.state = 369;
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
        this.state = 372;
        this.identifier();
        this.state = 373;
        this.match(XULEParser.COLON);
        this.state = 374;
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
        this.state = 376;
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
        this.state = 378;
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
			return this.precpred(this._ctx, 15);
		case 1:
			return this.precpred(this._ctx, 14);
		case 2:
			return this.precpred(this._ctx, 13);
		case 3:
			return this.precpred(this._ctx, 12);
		case 4:
			return this.precpred(this._ctx, 11);
		case 5:
			return this.precpred(this._ctx, 10);
		case 6:
			return this.precpred(this._ctx, 9);
		case 7:
			return this.precpred(this._ctx, 17);
		case 8:
			return this.precpred(this._ctx, 7);
		case 9:
			return this.precpred(this._ctx, 5);
		default:
			throw "No predicate with index:" + predIndex;
	}
};


exports.XULEParser = XULEParser;
