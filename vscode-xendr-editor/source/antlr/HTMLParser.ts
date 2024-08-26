// Generated from source\antlr\HTMLParser.g4 by ANTLR 4.9.0-SNAPSHOT


import { ATN } from "antlr4ts/atn/ATN";
import { ATNDeserializer } from "antlr4ts/atn/ATNDeserializer";
import { FailedPredicateException } from "antlr4ts/FailedPredicateException";
import { NotNull } from "antlr4ts/Decorators";
import { NoViableAltException } from "antlr4ts/NoViableAltException";
import { Override } from "antlr4ts/Decorators";
import { Parser } from "antlr4ts/Parser";
import { ParserRuleContext } from "antlr4ts/ParserRuleContext";
import { ParserATNSimulator } from "antlr4ts/atn/ParserATNSimulator";
import { ParseTreeListener } from "antlr4ts/tree/ParseTreeListener";
import { ParseTreeVisitor } from "antlr4ts/tree/ParseTreeVisitor";
import { RecognitionException } from "antlr4ts/RecognitionException";
import { RuleContext } from "antlr4ts/RuleContext";
//import { RuleVersion } from "antlr4ts/RuleVersion";
import { TerminalNode } from "antlr4ts/tree/TerminalNode";
import { Token } from "antlr4ts/Token";
import { TokenStream } from "antlr4ts/TokenStream";
import { Vocabulary } from "antlr4ts/Vocabulary";
import { VocabularyImpl } from "antlr4ts/VocabularyImpl";

import * as Utils from "antlr4ts/misc/Utils";


export class HTMLParser extends Parser {
	public static readonly HTML_COMMENT = 1;
	public static readonly HTML_CONDITIONAL_COMMENT = 2;
	public static readonly XML = 3;
	public static readonly CDATA = 4;
	public static readonly DTD = 5;
	public static readonly SCRIPTLET = 6;
	public static readonly SEA_WS = 7;
	public static readonly SCRIPT_OPEN = 8;
	public static readonly STYLE_OPEN = 9;
	public static readonly TAG_OPEN = 10;
	public static readonly HTML_TEXT = 11;
	public static readonly TAG_CLOSE = 12;
	public static readonly TAG_SLASH_CLOSE = 13;
	public static readonly TAG_SLASH = 14;
	public static readonly TAG_EQUALS = 15;
	public static readonly TAG_NAME = 16;
	public static readonly TAG_WHITESPACE = 17;
	public static readonly SCRIPT_BODY = 18;
	public static readonly SCRIPT_SHORT_BODY = 19;
	public static readonly STYLE_BODY = 20;
	public static readonly STYLE_SHORT_BODY = 21;
	public static readonly ATTVALUE_VALUE = 22;
	public static readonly ATTRIBUTE = 23;
	public static readonly RULE_htmlDocument = 0;
	public static readonly RULE_scriptletOrSeaWs = 1;
	public static readonly RULE_htmlElements = 2;
	public static readonly RULE_htmlElement = 3;
	public static readonly RULE_htmlContent = 4;
	public static readonly RULE_htmlAttribute = 5;
	public static readonly RULE_htmlChardata = 6;
	public static readonly RULE_htmlMisc = 7;
	public static readonly RULE_htmlComment = 8;
	public static readonly RULE_script = 9;
	public static readonly RULE_style = 10;
	// tslint:disable:no-trailing-whitespace
	public static readonly ruleNames: string[] = [
		"htmlDocument", "scriptletOrSeaWs", "htmlElements", "htmlElement", "htmlContent", 
		"htmlAttribute", "htmlChardata", "htmlMisc", "htmlComment", "script", 
		"style",
	];

	private static readonly _LITERAL_NAMES: Array<string | undefined> = [
		undefined, undefined, undefined, undefined, undefined, undefined, undefined, 
		undefined, undefined, undefined, "'<'", undefined, "'>'", "'/>'", "'/'", 
		"'='",
	];
	private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
		undefined, "HTML_COMMENT", "HTML_CONDITIONAL_COMMENT", "XML", "CDATA", 
		"DTD", "SCRIPTLET", "SEA_WS", "SCRIPT_OPEN", "STYLE_OPEN", "TAG_OPEN", 
		"HTML_TEXT", "TAG_CLOSE", "TAG_SLASH_CLOSE", "TAG_SLASH", "TAG_EQUALS", 
		"TAG_NAME", "TAG_WHITESPACE", "SCRIPT_BODY", "SCRIPT_SHORT_BODY", "STYLE_BODY", 
		"STYLE_SHORT_BODY", "ATTVALUE_VALUE", "ATTRIBUTE",
	];
	public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(HTMLParser._LITERAL_NAMES, HTMLParser._SYMBOLIC_NAMES, []);

	// @Override
	// @NotNull
	public get vocabulary(): Vocabulary {
		return HTMLParser.VOCABULARY;
	}
	// tslint:enable:no-trailing-whitespace

	// @Override
	public get grammarFileName(): string { return "HTMLParser.g4"; }

	// @Override
	public get ruleNames(): string[] { return HTMLParser.ruleNames; }

	// @Override
	public get serializedATN(): string { return HTMLParser._serializedATN; }

	protected createFailedPredicateException(predicate?: string, message?: string): FailedPredicateException {
		return new FailedPredicateException(this, predicate, message);
	}

	constructor(input: TokenStream) {
		super(input);
		this._interp = new ParserATNSimulator(HTMLParser._ATN, this);
	}
	// @RuleVersion(0)
	public htmlDocument(): HtmlDocumentContext {
		let _localctx: HtmlDocumentContext = new HtmlDocumentContext(this._ctx, this.state);
		this.enterRule(_localctx, 0, HTMLParser.RULE_htmlDocument);
		let _la: number;
		try {
			let _alt: number;
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 25;
			this._errHandler.sync(this);
			_alt = this.interpreter.adaptivePredict(this._input, 0, this._ctx);
			while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
				if (_alt === 1) {
					{
					{
					this.state = 22;
					this.scriptletOrSeaWs();
					}
					}
				}
				this.state = 27;
				this._errHandler.sync(this);
				_alt = this.interpreter.adaptivePredict(this._input, 0, this._ctx);
			}
			this.state = 29;
			this._errHandler.sync(this);
			_la = this._input.LA(1);
			if (_la === HTMLParser.XML) {
				{
				this.state = 28;
				this.match(HTMLParser.XML);
				}
			}

			this.state = 34;
			this._errHandler.sync(this);
			_alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
			while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
				if (_alt === 1) {
					{
					{
					this.state = 31;
					this.scriptletOrSeaWs();
					}
					}
				}
				this.state = 36;
				this._errHandler.sync(this);
				_alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
			}
			this.state = 38;
			this._errHandler.sync(this);
			_la = this._input.LA(1);
			if (_la === HTMLParser.DTD) {
				{
				this.state = 37;
				this.match(HTMLParser.DTD);
				}
			}

			this.state = 43;
			this._errHandler.sync(this);
			_alt = this.interpreter.adaptivePredict(this._input, 4, this._ctx);
			while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
				if (_alt === 1) {
					{
					{
					this.state = 40;
					this.scriptletOrSeaWs();
					}
					}
				}
				this.state = 45;
				this._errHandler.sync(this);
				_alt = this.interpreter.adaptivePredict(this._input, 4, this._ctx);
			}
			this.state = 49;
			this._errHandler.sync(this);
			_la = this._input.LA(1);
			while ((((_la) & ~0x1F) === 0 && ((1 << _la) & ((1 << HTMLParser.HTML_COMMENT) | (1 << HTMLParser.HTML_CONDITIONAL_COMMENT) | (1 << HTMLParser.SCRIPTLET) | (1 << HTMLParser.SEA_WS) | (1 << HTMLParser.SCRIPT_OPEN) | (1 << HTMLParser.STYLE_OPEN) | (1 << HTMLParser.TAG_OPEN))) !== 0)) {
				{
				{
				this.state = 46;
				_localctx._htmlElements = this.htmlElements();
				_localctx._elements.push(_localctx._htmlElements);
				}
				}
				this.state = 51;
				this._errHandler.sync(this);
				_la = this._input.LA(1);
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public scriptletOrSeaWs(): ScriptletOrSeaWsContext {
		let _localctx: ScriptletOrSeaWsContext = new ScriptletOrSeaWsContext(this._ctx, this.state);
		this.enterRule(_localctx, 2, HTMLParser.RULE_scriptletOrSeaWs);
		let _la: number;
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 52;
			_la = this._input.LA(1);
			if (!(_la === HTMLParser.SCRIPTLET || _la === HTMLParser.SEA_WS)) {
			this._errHandler.recoverInline(this);
			} else {
				if (this._input.LA(1) === Token.EOF) {
					this.matchedEOF = true;
				}

				this._errHandler.reportMatch(this);
				this.consume();
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlElements(): HtmlElementsContext {
		let _localctx: HtmlElementsContext = new HtmlElementsContext(this._ctx, this.state);
		this.enterRule(_localctx, 4, HTMLParser.RULE_htmlElements);
		let _la: number;
		try {
			let _alt: number;
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 57;
			this._errHandler.sync(this);
			_la = this._input.LA(1);
			while ((((_la) & ~0x1F) === 0 && ((1 << _la) & ((1 << HTMLParser.HTML_COMMENT) | (1 << HTMLParser.HTML_CONDITIONAL_COMMENT) | (1 << HTMLParser.SEA_WS))) !== 0)) {
				{
				{
				this.state = 54;
				this.htmlMisc();
				}
				}
				this.state = 59;
				this._errHandler.sync(this);
				_la = this._input.LA(1);
			}
			this.state = 60;
			_localctx._element = this.htmlElement();
			this.state = 64;
			this._errHandler.sync(this);
			_alt = this.interpreter.adaptivePredict(this._input, 7, this._ctx);
			while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
				if (_alt === 1) {
					{
					{
					this.state = 61;
					this.htmlMisc();
					}
					}
				}
				this.state = 66;
				this._errHandler.sync(this);
				_alt = this.interpreter.adaptivePredict(this._input, 7, this._ctx);
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlElement(): HtmlElementContext {
		let _localctx: HtmlElementContext = new HtmlElementContext(this._ctx, this.state);
		this.enterRule(_localctx, 6, HTMLParser.RULE_htmlElement);
		let _la: number;
		try {
			this.state = 90;
			this._errHandler.sync(this);
			switch (this._input.LA(1)) {
			case HTMLParser.TAG_OPEN:
				this.enterOuterAlt(_localctx, 1);
				{
				this.state = 67;
				this.match(HTMLParser.TAG_OPEN);
				this.state = 68;
				_localctx._name = this.match(HTMLParser.TAG_NAME);
				this.state = 72;
				this._errHandler.sync(this);
				_la = this._input.LA(1);
				while (_la === HTMLParser.TAG_NAME) {
					{
					{
					this.state = 69;
					_localctx._htmlAttribute = this.htmlAttribute();
					_localctx._attributes.push(_localctx._htmlAttribute);
					}
					}
					this.state = 74;
					this._errHandler.sync(this);
					_la = this._input.LA(1);
				}
				this.state = 85;
				this._errHandler.sync(this);
				switch (this._input.LA(1)) {
				case HTMLParser.TAG_CLOSE:
					{
					this.state = 75;
					this.match(HTMLParser.TAG_CLOSE);
					this.state = 82;
					this._errHandler.sync(this);
					switch ( this.interpreter.adaptivePredict(this._input, 9, this._ctx) ) {
					case 1:
						{
						this.state = 76;
						_localctx._content = this.htmlContent();
						this.state = 77;
						this.match(HTMLParser.TAG_OPEN);
						this.state = 78;
						this.match(HTMLParser.TAG_SLASH);
						this.state = 79;
						this.match(HTMLParser.TAG_NAME);
						this.state = 80;
						this.match(HTMLParser.TAG_CLOSE);
						}
						break;
					}
					}
					break;
				case HTMLParser.TAG_SLASH_CLOSE:
					{
					this.state = 84;
					this.match(HTMLParser.TAG_SLASH_CLOSE);
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				break;
			case HTMLParser.SCRIPTLET:
				this.enterOuterAlt(_localctx, 2);
				{
				this.state = 87;
				this.match(HTMLParser.SCRIPTLET);
				}
				break;
			case HTMLParser.SCRIPT_OPEN:
				this.enterOuterAlt(_localctx, 3);
				{
				this.state = 88;
				this.script();
				}
				break;
			case HTMLParser.STYLE_OPEN:
				this.enterOuterAlt(_localctx, 4);
				{
				this.state = 89;
				this.style();
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlContent(): HtmlContentContext {
		let _localctx: HtmlContentContext = new HtmlContentContext(this._ctx, this.state);
		this.enterRule(_localctx, 8, HTMLParser.RULE_htmlContent);
		let _la: number;
		try {
			let _alt: number;
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 93;
			this._errHandler.sync(this);
			_la = this._input.LA(1);
			if (_la === HTMLParser.SEA_WS || _la === HTMLParser.HTML_TEXT) {
				{
				this.state = 92;
				_localctx._htmlChardata = this.htmlChardata();
				_localctx._texts.push(_localctx._htmlChardata);
				}
			}

			this.state = 105;
			this._errHandler.sync(this);
			_alt = this.interpreter.adaptivePredict(this._input, 15, this._ctx);
			while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
				if (_alt === 1) {
					{
					{
					this.state = 98;
					this._errHandler.sync(this);
					switch (this._input.LA(1)) {
					case HTMLParser.SCRIPTLET:
					case HTMLParser.SCRIPT_OPEN:
					case HTMLParser.STYLE_OPEN:
					case HTMLParser.TAG_OPEN:
						{
						this.state = 95;
						_localctx._htmlElement = this.htmlElement();
						_localctx._subelements.push(_localctx._htmlElement);
						}
						break;
					case HTMLParser.CDATA:
						{
						this.state = 96;
						_localctx._cdata = this.match(HTMLParser.CDATA);
						}
						break;
					case HTMLParser.HTML_COMMENT:
					case HTMLParser.HTML_CONDITIONAL_COMMENT:
						{
						this.state = 97;
						this.htmlComment();
						}
						break;
					default:
						throw new NoViableAltException(this);
					}
					this.state = 101;
					this._errHandler.sync(this);
					_la = this._input.LA(1);
					if (_la === HTMLParser.SEA_WS || _la === HTMLParser.HTML_TEXT) {
						{
						this.state = 100;
						_localctx._htmlChardata = this.htmlChardata();
						_localctx._texts.push(_localctx._htmlChardata);
						}
					}

					}
					}
				}
				this.state = 107;
				this._errHandler.sync(this);
				_alt = this.interpreter.adaptivePredict(this._input, 15, this._ctx);
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlAttribute(): HtmlAttributeContext {
		let _localctx: HtmlAttributeContext = new HtmlAttributeContext(this._ctx, this.state);
		this.enterRule(_localctx, 10, HTMLParser.RULE_htmlAttribute);
		let _la: number;
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 108;
			_localctx._name = this.match(HTMLParser.TAG_NAME);
			this.state = 111;
			this._errHandler.sync(this);
			_la = this._input.LA(1);
			if (_la === HTMLParser.TAG_EQUALS) {
				{
				this.state = 109;
				this.match(HTMLParser.TAG_EQUALS);
				this.state = 110;
				_localctx._value = this.match(HTMLParser.ATTVALUE_VALUE);
				}
			}

			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlChardata(): HtmlChardataContext {
		let _localctx: HtmlChardataContext = new HtmlChardataContext(this._ctx, this.state);
		this.enterRule(_localctx, 12, HTMLParser.RULE_htmlChardata);
		let _la: number;
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 113;
			_la = this._input.LA(1);
			if (!(_la === HTMLParser.SEA_WS || _la === HTMLParser.HTML_TEXT)) {
			this._errHandler.recoverInline(this);
			} else {
				if (this._input.LA(1) === Token.EOF) {
					this.matchedEOF = true;
				}

				this._errHandler.reportMatch(this);
				this.consume();
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlMisc(): HtmlMiscContext {
		let _localctx: HtmlMiscContext = new HtmlMiscContext(this._ctx, this.state);
		this.enterRule(_localctx, 14, HTMLParser.RULE_htmlMisc);
		try {
			this.state = 117;
			this._errHandler.sync(this);
			switch (this._input.LA(1)) {
			case HTMLParser.HTML_COMMENT:
			case HTMLParser.HTML_CONDITIONAL_COMMENT:
				this.enterOuterAlt(_localctx, 1);
				{
				this.state = 115;
				this.htmlComment();
				}
				break;
			case HTMLParser.SEA_WS:
				this.enterOuterAlt(_localctx, 2);
				{
				this.state = 116;
				this.match(HTMLParser.SEA_WS);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public htmlComment(): HtmlCommentContext {
		let _localctx: HtmlCommentContext = new HtmlCommentContext(this._ctx, this.state);
		this.enterRule(_localctx, 16, HTMLParser.RULE_htmlComment);
		let _la: number;
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 119;
			_la = this._input.LA(1);
			if (!(_la === HTMLParser.HTML_COMMENT || _la === HTMLParser.HTML_CONDITIONAL_COMMENT)) {
			this._errHandler.recoverInline(this);
			} else {
				if (this._input.LA(1) === Token.EOF) {
					this.matchedEOF = true;
				}

				this._errHandler.reportMatch(this);
				this.consume();
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public script(): ScriptContext {
		let _localctx: ScriptContext = new ScriptContext(this._ctx, this.state);
		this.enterRule(_localctx, 18, HTMLParser.RULE_script);
		let _la: number;
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 121;
			this.match(HTMLParser.SCRIPT_OPEN);
			this.state = 122;
			_la = this._input.LA(1);
			if (!(_la === HTMLParser.SCRIPT_BODY || _la === HTMLParser.SCRIPT_SHORT_BODY)) {
			this._errHandler.recoverInline(this);
			} else {
				if (this._input.LA(1) === Token.EOF) {
					this.matchedEOF = true;
				}

				this._errHandler.reportMatch(this);
				this.consume();
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public style(): StyleContext {
		let _localctx: StyleContext = new StyleContext(this._ctx, this.state);
		this.enterRule(_localctx, 20, HTMLParser.RULE_style);
		let _la: number;
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 124;
			this.match(HTMLParser.STYLE_OPEN);
			this.state = 125;
			_la = this._input.LA(1);
			if (!(_la === HTMLParser.STYLE_BODY || _la === HTMLParser.STYLE_SHORT_BODY)) {
			this._errHandler.recoverInline(this);
			} else {
				if (this._input.LA(1) === Token.EOF) {
					this.matchedEOF = true;
				}

				this._errHandler.reportMatch(this);
				this.consume();
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}

	public static readonly _serializedATN: string =
		"\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x19\x82\x04\x02" +
		"\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07" +
		"\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x03\x02\x07\x02" +
		"\x1A\n\x02\f\x02\x0E\x02\x1D\v\x02\x03\x02\x05\x02 \n\x02\x03\x02\x07" +
		"\x02#\n\x02\f\x02\x0E\x02&\v\x02\x03\x02\x05\x02)\n\x02\x03\x02\x07\x02" +
		",\n\x02\f\x02\x0E\x02/\v\x02\x03\x02\x07\x022\n\x02\f\x02\x0E\x025\v\x02" +
		"\x03\x03\x03\x03\x03\x04\x07\x04:\n\x04\f\x04\x0E\x04=\v\x04\x03\x04\x03" +
		"\x04\x07\x04A\n\x04\f\x04\x0E\x04D\v\x04\x03\x05\x03\x05\x03\x05\x07\x05" +
		"I\n\x05\f\x05\x0E\x05L\v\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03" +
		"\x05\x03\x05\x05\x05U\n\x05\x03\x05\x05\x05X\n\x05\x03\x05\x03\x05\x03" +
		"\x05\x05\x05]\n\x05\x03\x06\x05\x06`\n\x06\x03\x06\x03\x06\x03\x06\x05" +
		"\x06e\n\x06\x03\x06\x05\x06h\n\x06\x07\x06j\n\x06\f\x06\x0E\x06m\v\x06" +
		"\x03\x07\x03\x07\x03\x07\x05\x07r\n\x07\x03\b\x03\b\x03\t\x03\t\x05\t" +
		"x\n\t\x03\n\x03\n\x03\v\x03\v\x03\v\x03\f\x03\f\x03\f\x03\f\x02\x02\x02" +
		"\r\x02\x02\x04\x02\x06\x02\b\x02\n\x02\f\x02\x0E\x02\x10\x02\x12\x02\x14" +
		"\x02\x16\x02\x02\x07\x03\x02\b\t\x04\x02\t\t\r\r\x03\x02\x03\x04\x03\x02" +
		"\x14\x15\x03\x02\x16\x17\x02\x8B\x02\x1B\x03\x02\x02\x02\x046\x03\x02" +
		"\x02\x02\x06;\x03\x02\x02\x02\b\\\x03\x02\x02\x02\n_\x03\x02\x02\x02\f" +
		"n\x03\x02\x02\x02\x0Es\x03\x02\x02\x02\x10w\x03\x02\x02\x02\x12y\x03\x02" +
		"\x02\x02\x14{\x03\x02\x02\x02\x16~\x03\x02\x02\x02\x18\x1A\x05\x04\x03" +
		"\x02\x19\x18\x03\x02\x02\x02\x1A\x1D\x03\x02\x02\x02\x1B\x19\x03\x02\x02" +
		"\x02\x1B\x1C\x03\x02\x02\x02\x1C\x1F\x03\x02\x02\x02\x1D\x1B\x03\x02\x02" +
		"\x02\x1E \x07\x05\x02\x02\x1F\x1E\x03\x02\x02\x02\x1F \x03\x02\x02\x02" +
		" $\x03\x02\x02\x02!#\x05\x04\x03\x02\"!\x03\x02\x02\x02#&\x03\x02\x02" +
		"\x02$\"\x03\x02\x02\x02$%\x03\x02\x02\x02%(\x03\x02\x02\x02&$\x03\x02" +
		"\x02\x02\')\x07\x07\x02\x02(\'\x03\x02\x02\x02()\x03\x02\x02\x02)-\x03" +
		"\x02\x02\x02*,\x05\x04\x03\x02+*\x03\x02\x02\x02,/\x03\x02\x02\x02-+\x03" +
		"\x02\x02\x02-.\x03\x02\x02\x02.3\x03\x02\x02\x02/-\x03\x02\x02\x0202\x05" +
		"\x06\x04\x0210\x03\x02\x02\x0225\x03\x02\x02\x0231\x03\x02\x02\x0234\x03" +
		"\x02\x02\x024\x03\x03\x02\x02\x0253\x03\x02\x02\x0267\t\x02\x02\x027\x05" +
		"\x03\x02\x02\x028:\x05\x10\t\x0298\x03\x02\x02\x02:=\x03\x02\x02\x02;" +
		"9\x03\x02\x02\x02;<\x03\x02\x02\x02<>\x03\x02\x02\x02=;\x03\x02\x02\x02" +
		">B\x05\b\x05\x02?A\x05\x10\t\x02@?\x03\x02\x02\x02AD\x03\x02\x02\x02B" +
		"@\x03\x02\x02\x02BC\x03\x02\x02\x02C\x07\x03\x02\x02\x02DB\x03\x02\x02" +
		"\x02EF\x07\f\x02\x02FJ\x07\x12\x02\x02GI\x05\f\x07\x02HG\x03\x02\x02\x02" +
		"IL\x03\x02\x02\x02JH\x03\x02\x02\x02JK\x03\x02\x02\x02KW\x03\x02\x02\x02" +
		"LJ\x03\x02\x02\x02MT\x07\x0E\x02\x02NO\x05\n\x06\x02OP\x07\f\x02\x02P" +
		"Q\x07\x10\x02\x02QR\x07\x12\x02\x02RS\x07\x0E\x02\x02SU\x03\x02\x02\x02" +
		"TN\x03\x02\x02\x02TU\x03\x02\x02\x02UX\x03\x02\x02\x02VX\x07\x0F\x02\x02" +
		"WM\x03\x02\x02\x02WV\x03\x02\x02\x02X]\x03\x02\x02\x02Y]\x07\b\x02\x02" +
		"Z]\x05\x14\v\x02[]\x05\x16\f\x02\\E\x03\x02\x02\x02\\Y\x03\x02\x02\x02" +
		"\\Z\x03\x02\x02\x02\\[\x03\x02\x02\x02]\t\x03\x02\x02\x02^`\x05\x0E\b" +
		"\x02_^\x03\x02\x02\x02_`\x03\x02\x02\x02`k\x03\x02\x02\x02ae\x05\b\x05" +
		"\x02be\x07\x06\x02\x02ce\x05\x12\n\x02da\x03\x02\x02\x02db\x03\x02\x02" +
		"\x02dc\x03\x02\x02\x02eg\x03\x02\x02\x02fh\x05\x0E\b\x02gf\x03\x02\x02" +
		"\x02gh\x03\x02\x02\x02hj\x03\x02\x02\x02id\x03\x02\x02\x02jm\x03\x02\x02" +
		"\x02ki\x03\x02\x02\x02kl\x03\x02\x02\x02l\v\x03\x02\x02\x02mk\x03\x02" +
		"\x02\x02nq\x07\x12\x02\x02op\x07\x11\x02\x02pr\x07\x18\x02\x02qo\x03\x02" +
		"\x02\x02qr\x03\x02\x02\x02r\r\x03\x02\x02\x02st\t\x03\x02\x02t\x0F\x03" +
		"\x02\x02\x02ux\x05\x12\n\x02vx\x07\t\x02\x02wu\x03\x02\x02\x02wv\x03\x02" +
		"\x02\x02x\x11\x03\x02\x02\x02yz\t\x04\x02\x02z\x13\x03\x02\x02\x02{|\x07" +
		"\n\x02\x02|}\t\x05\x02\x02}\x15\x03\x02\x02\x02~\x7F\x07\v\x02\x02\x7F" +
		"\x80\t\x06\x02\x02\x80\x17\x03\x02\x02\x02\x14\x1B\x1F$(-3;BJTW\\_dgk" +
		"qw";
	public static __ATN: ATN;
	public static get _ATN(): ATN {
		if (!HTMLParser.__ATN) {
			HTMLParser.__ATN = new ATNDeserializer().deserialize(Utils.toCharArray(HTMLParser._serializedATN));
		}

		return HTMLParser.__ATN;
	}

}

export class HtmlDocumentContext extends ParserRuleContext {
	public _htmlElements!: HtmlElementsContext;
	public _elements: HtmlElementsContext[] = [];
	public scriptletOrSeaWs(): ScriptletOrSeaWsContext[];
	public scriptletOrSeaWs(i: number): ScriptletOrSeaWsContext;
	public scriptletOrSeaWs(i?: number): ScriptletOrSeaWsContext | ScriptletOrSeaWsContext[] {
		if (i === undefined) {
			return this.getRuleContexts(ScriptletOrSeaWsContext);
		} else {
			return this.getRuleContext(i, ScriptletOrSeaWsContext);
		}
	}
	public XML(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.XML, 0); }
	public DTD(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.DTD, 0); }
	public htmlElements(): HtmlElementsContext[];
	public htmlElements(i: number): HtmlElementsContext;
	public htmlElements(i?: number): HtmlElementsContext | HtmlElementsContext[] {
		if (i === undefined) {
			return this.getRuleContexts(HtmlElementsContext);
		} else {
			return this.getRuleContext(i, HtmlElementsContext);
		}
	}
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlDocument; }
}


export class ScriptletOrSeaWsContext extends ParserRuleContext {
	public SCRIPTLET(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SCRIPTLET, 0); }
	public SEA_WS(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SEA_WS, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_scriptletOrSeaWs; }
}


export class HtmlElementsContext extends ParserRuleContext {
	public _element!: HtmlElementContext;
	public htmlElement(): HtmlElementContext {
		return this.getRuleContext(0, HtmlElementContext);
	}
	public htmlMisc(): HtmlMiscContext[];
	public htmlMisc(i: number): HtmlMiscContext;
	public htmlMisc(i?: number): HtmlMiscContext | HtmlMiscContext[] {
		if (i === undefined) {
			return this.getRuleContexts(HtmlMiscContext);
		} else {
			return this.getRuleContext(i, HtmlMiscContext);
		}
	}
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlElements; }
}


export class HtmlElementContext extends ParserRuleContext {
	public _name!: Token;
	public _htmlAttribute!: HtmlAttributeContext;
	public _attributes: HtmlAttributeContext[] = [];
	public _content!: HtmlContentContext;
	public TAG_OPEN(): TerminalNode[];
	public TAG_OPEN(i: number): TerminalNode;
	public TAG_OPEN(i?: number): TerminalNode | TerminalNode[] {
		if (i === undefined) {
			return this.getTokens(HTMLParser.TAG_OPEN);
		} else {
			return this.getToken(HTMLParser.TAG_OPEN, i);
		}
	}
	public TAG_NAME(): TerminalNode[];
	public TAG_NAME(i: number): TerminalNode;
	public TAG_NAME(i?: number): TerminalNode | TerminalNode[] {
		if (i === undefined) {
			return this.getTokens(HTMLParser.TAG_NAME);
		} else {
			return this.getToken(HTMLParser.TAG_NAME, i);
		}
	}
	public TAG_CLOSE(): TerminalNode[];
	public TAG_CLOSE(i: number): TerminalNode;
	public TAG_CLOSE(i?: number): TerminalNode | TerminalNode[] {
		if (i === undefined) {
			return this.getTokens(HTMLParser.TAG_CLOSE);
		} else {
			return this.getToken(HTMLParser.TAG_CLOSE, i);
		}
	}
	public TAG_SLASH_CLOSE(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.TAG_SLASH_CLOSE, 0); }
	public htmlAttribute(): HtmlAttributeContext[];
	public htmlAttribute(i: number): HtmlAttributeContext;
	public htmlAttribute(i?: number): HtmlAttributeContext | HtmlAttributeContext[] {
		if (i === undefined) {
			return this.getRuleContexts(HtmlAttributeContext);
		} else {
			return this.getRuleContext(i, HtmlAttributeContext);
		}
	}
	public TAG_SLASH(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.TAG_SLASH, 0); }
	public htmlContent(): HtmlContentContext | undefined {
		return this.tryGetRuleContext(0, HtmlContentContext);
	}
	public SCRIPTLET(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SCRIPTLET, 0); }
	public script(): ScriptContext | undefined {
		return this.tryGetRuleContext(0, ScriptContext);
	}
	public style(): StyleContext | undefined {
		return this.tryGetRuleContext(0, StyleContext);
	}
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlElement; }
}


export class HtmlContentContext extends ParserRuleContext {
	public _htmlChardata!: HtmlChardataContext;
	public _texts: HtmlChardataContext[] = [];
	public _htmlElement!: HtmlElementContext;
	public _subelements: HtmlElementContext[] = [];
	public _cdata!: Token;
	public htmlChardata(): HtmlChardataContext[];
	public htmlChardata(i: number): HtmlChardataContext;
	public htmlChardata(i?: number): HtmlChardataContext | HtmlChardataContext[] {
		if (i === undefined) {
			return this.getRuleContexts(HtmlChardataContext);
		} else {
			return this.getRuleContext(i, HtmlChardataContext);
		}
	}
	public htmlComment(): HtmlCommentContext[];
	public htmlComment(i: number): HtmlCommentContext;
	public htmlComment(i?: number): HtmlCommentContext | HtmlCommentContext[] {
		if (i === undefined) {
			return this.getRuleContexts(HtmlCommentContext);
		} else {
			return this.getRuleContext(i, HtmlCommentContext);
		}
	}
	public htmlElement(): HtmlElementContext[];
	public htmlElement(i: number): HtmlElementContext;
	public htmlElement(i?: number): HtmlElementContext | HtmlElementContext[] {
		if (i === undefined) {
			return this.getRuleContexts(HtmlElementContext);
		} else {
			return this.getRuleContext(i, HtmlElementContext);
		}
	}
	public CDATA(): TerminalNode[];
	public CDATA(i: number): TerminalNode;
	public CDATA(i?: number): TerminalNode | TerminalNode[] {
		if (i === undefined) {
			return this.getTokens(HTMLParser.CDATA);
		} else {
			return this.getToken(HTMLParser.CDATA, i);
		}
	}
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlContent; }
}


export class HtmlAttributeContext extends ParserRuleContext {
	public _name!: Token;
	public _value!: Token;
	public TAG_NAME(): TerminalNode { return this.getToken(HTMLParser.TAG_NAME, 0); }
	public TAG_EQUALS(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.TAG_EQUALS, 0); }
	public ATTVALUE_VALUE(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.ATTVALUE_VALUE, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlAttribute; }
}


export class HtmlChardataContext extends ParserRuleContext {
	public HTML_TEXT(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.HTML_TEXT, 0); }
	public SEA_WS(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SEA_WS, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlChardata; }
}


export class HtmlMiscContext extends ParserRuleContext {
	public htmlComment(): HtmlCommentContext | undefined {
		return this.tryGetRuleContext(0, HtmlCommentContext);
	}
	public SEA_WS(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SEA_WS, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlMisc; }
}


export class HtmlCommentContext extends ParserRuleContext {
	public HTML_COMMENT(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.HTML_COMMENT, 0); }
	public HTML_CONDITIONAL_COMMENT(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.HTML_CONDITIONAL_COMMENT, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_htmlComment; }
}


export class ScriptContext extends ParserRuleContext {
	public SCRIPT_OPEN(): TerminalNode { return this.getToken(HTMLParser.SCRIPT_OPEN, 0); }
	public SCRIPT_BODY(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SCRIPT_BODY, 0); }
	public SCRIPT_SHORT_BODY(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.SCRIPT_SHORT_BODY, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_script; }
}


export class StyleContext extends ParserRuleContext {
	public STYLE_OPEN(): TerminalNode { return this.getToken(HTMLParser.STYLE_OPEN, 0); }
	public STYLE_BODY(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.STYLE_BODY, 0); }
	public STYLE_SHORT_BODY(): TerminalNode | undefined { return this.tryGetToken(HTMLParser.STYLE_SHORT_BODY, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return HTMLParser.RULE_style; }
}


