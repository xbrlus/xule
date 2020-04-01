// Generated from XULE.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');
var XULEListener = require('./XULEListener').XULEListener;
var grammarFileName = "XULE.g4";


var serializedATN = ["\u0003\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964",
    "\u0003%R\u0004\u0002\t\u0002\u0004\u0003\t\u0003\u0004\u0004\t\u0004",
    "\u0004\u0005\t\u0005\u0004\u0006\t\u0006\u0004\u0007\t\u0007\u0004\b",
    "\t\b\u0003\u0002\u0003\u0002\u0003\u0002\u0007\u0002\u0014\n\u0002\f",
    "\u0002\u000e\u0002\u0017\u000b\u0002\u0003\u0002\u0003\u0002\u0003\u0002",
    "\u0007\u0002\u001c\n\u0002\f\u0002\u000e\u0002\u001f\u000b\u0002\u0003",
    "\u0002\u0005\u0002\"\n\u0002\u0003\u0003\u0003\u0003\u0005\u0003&\n",
    "\u0003\u0003\u0004\u0003\u0004\u0005\u0004*\n\u0004\u0003\u0004\u0003",
    "\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003",
    "\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003",
    "\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0005\u0004>",
    "\n\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004\u0003\u0004",
    "\u0003\u0004\u0005\u0004F\n\u0004\u0003\u0005\u0003\u0005\u0003\u0006",
    "\u0003\u0006\u0003\u0007\u0003\u0007\u0003\u0007\u0003\u0007\u0003\b",
    "\u0003\b\u0003\b\u0002\u0002\t\u0002\u0004\u0006\b\n\f\u000e\u0002\u0007",
    "\u0003\u0002\u001d\u001e\u0004\u0002\t\t\u001f!\u0003\u0002\u0014\u0015",
    "\u0003\u0002\u0011\u0013\u0003\u0002\"#\u0002X\u0002!\u0003\u0002\u0002",
    "\u0002\u0004#\u0003\u0002\u0002\u0002\u0006E\u0003\u0002\u0002\u0002",
    "\bG\u0003\u0002\u0002\u0002\nI\u0003\u0002\u0002\u0002\fK\u0003\u0002",
    "\u0002\u0002\u000eO\u0003\u0002\u0002\u0002\u0010\"\u0007\u0003\u0002",
    "\u0002\u0011\u0015\u0007\u0004\u0002\u0002\u0012\u0014\u0005\u0004\u0003",
    "\u0002\u0013\u0012\u0003\u0002\u0002\u0002\u0014\u0017\u0003\u0002\u0002",
    "\u0002\u0015\u0013\u0003\u0002\u0002\u0002\u0015\u0016\u0003\u0002\u0002",
    "\u0002\u0016\u0018\u0003\u0002\u0002\u0002\u0017\u0015\u0003\u0002\u0002",
    "\u0002\u0018\"\u0007\u0005\u0002\u0002\u0019\u001d\u0007\u0006\u0002",
    "\u0002\u001a\u001c\u0005\u0004\u0003\u0002\u001b\u001a\u0003\u0002\u0002",
    "\u0002\u001c\u001f\u0003\u0002\u0002\u0002\u001d\u001b\u0003\u0002\u0002",
    "\u0002\u001d\u001e\u0003\u0002\u0002\u0002\u001e \u0003\u0002\u0002",
    "\u0002\u001f\u001d\u0003\u0002\u0002\u0002 \"\u0007\u0007\u0002\u0002",
    "!\u0010\u0003\u0002\u0002\u0002!\u0011\u0003\u0002\u0002\u0002!\u0019",
    "\u0003\u0002\u0002\u0002\"\u0003\u0003\u0002\u0002\u0002#%\u0007\u0003",
    "\u0002\u0002$&\u0005\u0006\u0004\u0002%$\u0003\u0002\u0002\u0002%&\u0003",
    "\u0002\u0002\u0002&\u0005\u0003\u0002\u0002\u0002\'(\u0007\u0018\u0002",
    "\u0002(*\u0007\b\u0002\u0002)\'\u0003\u0002\u0002\u0002)*\u0003\u0002",
    "\u0002\u0002*+\u0003\u0002\u0002\u0002+F\u0005\b\u0005\u0002,-\u0007",
    "\u0010\u0002\u0002-.\u0007\b\u0002\u0002.F\u0007\u000e\u0002\u0002/",
    "0\u0007\u000f\u0002\u000201\u0007\b\u0002\u00021F\t\u0002\u0002\u0002",
    "23\u0007\u0016\u0002\u000234\u0007\b\u0002\u00024F\t\u0003\u0002\u0002",
    "56\u0007\u0017\u0002\u000267\u0007\n\u0002\u000278\u0007$\u0002\u0002",
    "89\u0007\u000b\u0002\u00029=\u0007\b\u0002\u0002:>\u0005\n\u0006\u0002",
    ";>\u0007!\u0002\u0002<>\u0007\t\u0002\u0002=:\u0003\u0002\u0002\u0002",
    "=;\u0003\u0002\u0002\u0002=<\u0003\u0002\u0002\u0002>F\u0003\u0002\u0002",
    "\u0002?@\t\u0004\u0002\u0002@A\u0007\b\u0002\u0002AF\u0005\f\u0007\u0002",
    "BC\t\u0005\u0002\u0002CD\u0007\b\u0002\u0002DF\u0005\u000e\b\u0002E",
    ")\u0003\u0002\u0002\u0002E,\u0003\u0002\u0002\u0002E/\u0003\u0002\u0002",
    "\u0002E2\u0003\u0002\u0002\u0002E5\u0003\u0002\u0002\u0002E?\u0003\u0002",
    "\u0002\u0002EB\u0003\u0002\u0002\u0002F\u0007\u0003\u0002\u0002\u0002",
    "GH\u0007$\u0002\u0002H\t\u0003\u0002\u0002\u0002IJ\u0003\u0002\u0002",
    "\u0002J\u000b\u0003\u0002\u0002\u0002KL\u0005\b\u0005\u0002LM\u0007",
    "\f\u0002\u0002MN\u0005\b\u0005\u0002N\r\u0003\u0002\u0002\u0002OP\t",
    "\u0006\u0002\u0002P\u000f\u0003\u0002\u0002\u0002\t\u0015\u001d!%)=",
    "E"].join("");


var atn = new antlr4.atn.ATNDeserializer().deserialize(serializedATN);

var decisionsToDFA = atn.decisionToState.map( function(ds, index) { return new antlr4.dfa.DFA(ds, index); });

var sharedContextCache = new antlr4.PredictionContextCache();

var literalNames = [ null, "'@'", "'{'", "'}'", "'['", "']'", "'='", "'*'", 
                     "'('", "')'", "':'", null, null, null, null, null, 
                     null, null, null, null, null, null, "'concept'", "'period'", 
                     "'unit'", "'entity'", "'cube'", "'instant'", "'duration'", 
                     "'debit'", "'credit'", "'none'", "'true'", "'false'" ];

var symbolicNames = [ null, null, null, null, null, null, null, null, null, 
                      null, null, "DOUBLE_QUOTED_STRING", "SINGLE_QUOTED_STRING", 
                      "CONCEPT_PERIOD_TYPE", "CONCEPT_LOCAL_NAME", "CONCEPT_IS_NUMERIC", 
                      "CONCEPT_IS_MONETARY", "CONCEPT_HAS_ENUMERATIONS", 
                      "CONCEPT_DATA_TYPE", "CONCEPT_BASE_TYPE", "CONCEPT_BALANCE", 
                      "CONCEPT_ATTRIBUTE", "CONCEPT", "PERIOD_FILTER", "UNIT_FILTER", 
                      "ENTITY_FILTER", "CUBE_FILTER", "INSTANT", "DURATION", 
                      "DEBIT", "CREDIT", "NONE", "TRUE", "FALSE", "IDENTIFIER", 
                      "WS" ];

var ruleNames =  [ "factset", "aspect_filter", "concept_filter", "identifier", 
                   "value", "dataType", "booleanValue" ];

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
XULEParser.T__0 = 1;
XULEParser.T__1 = 2;
XULEParser.T__2 = 3;
XULEParser.T__3 = 4;
XULEParser.T__4 = 5;
XULEParser.T__5 = 6;
XULEParser.T__6 = 7;
XULEParser.T__7 = 8;
XULEParser.T__8 = 9;
XULEParser.T__9 = 10;
XULEParser.DOUBLE_QUOTED_STRING = 11;
XULEParser.SINGLE_QUOTED_STRING = 12;
XULEParser.CONCEPT_PERIOD_TYPE = 13;
XULEParser.CONCEPT_LOCAL_NAME = 14;
XULEParser.CONCEPT_IS_NUMERIC = 15;
XULEParser.CONCEPT_IS_MONETARY = 16;
XULEParser.CONCEPT_HAS_ENUMERATIONS = 17;
XULEParser.CONCEPT_DATA_TYPE = 18;
XULEParser.CONCEPT_BASE_TYPE = 19;
XULEParser.CONCEPT_BALANCE = 20;
XULEParser.CONCEPT_ATTRIBUTE = 21;
XULEParser.CONCEPT = 22;
XULEParser.PERIOD_FILTER = 23;
XULEParser.UNIT_FILTER = 24;
XULEParser.ENTITY_FILTER = 25;
XULEParser.CUBE_FILTER = 26;
XULEParser.INSTANT = 27;
XULEParser.DURATION = 28;
XULEParser.DEBIT = 29;
XULEParser.CREDIT = 30;
XULEParser.NONE = 31;
XULEParser.TRUE = 32;
XULEParser.FALSE = 33;
XULEParser.IDENTIFIER = 34;
XULEParser.WS = 35;

XULEParser.RULE_factset = 0;
XULEParser.RULE_aspect_filter = 1;
XULEParser.RULE_concept_filter = 2;
XULEParser.RULE_identifier = 3;
XULEParser.RULE_value = 4;
XULEParser.RULE_dataType = 5;
XULEParser.RULE_booleanValue = 6;


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

FactsetContext.prototype.aspect_filter = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(Aspect_filterContext);
    } else {
        return this.getTypedRuleContext(Aspect_filterContext,i);
    }
};

FactsetContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterFactset(this);
	}
};

FactsetContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitFactset(this);
	}
};




XULEParser.FactsetContext = FactsetContext;

XULEParser.prototype.factset = function() {

    var localctx = new FactsetContext(this, this._ctx, this.state);
    this.enterRule(localctx, 0, XULEParser.RULE_factset);
    var _la = 0; // Token type
    try {
        this.state = 31;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.T__0:
            this.enterOuterAlt(localctx, 1);
            this.state = 14;
            this.match(XULEParser.T__0);
            break;
        case XULEParser.T__1:
            this.enterOuterAlt(localctx, 2);
            this.state = 15;
            this.match(XULEParser.T__1);
            this.state = 19;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.T__0) {
                this.state = 16;
                this.aspect_filter();
                this.state = 21;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }
            this.state = 22;
            this.match(XULEParser.T__2);
            break;
        case XULEParser.T__3:
            this.enterOuterAlt(localctx, 3);
            this.state = 23;
            this.match(XULEParser.T__3);
            this.state = 27;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            while(_la===XULEParser.T__0) {
                this.state = 24;
                this.aspect_filter();
                this.state = 29;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
            }
            this.state = 30;
            this.match(XULEParser.T__4);
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


function Aspect_filterContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_aspect_filter;
    return this;
}

Aspect_filterContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
Aspect_filterContext.prototype.constructor = Aspect_filterContext;

Aspect_filterContext.prototype.concept_filter = function() {
    return this.getTypedRuleContext(Concept_filterContext,0);
};

Aspect_filterContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterAspect_filter(this);
	}
};

Aspect_filterContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitAspect_filter(this);
	}
};




XULEParser.Aspect_filterContext = Aspect_filterContext;

XULEParser.prototype.aspect_filter = function() {

    var localctx = new Aspect_filterContext(this, this._ctx, this.state);
    this.enterRule(localctx, 2, XULEParser.RULE_aspect_filter);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 33;
        this.match(XULEParser.T__0);
        this.state = 35;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if(((((_la - 13)) & ~0x1f) == 0 && ((1 << (_la - 13)) & ((1 << (XULEParser.CONCEPT_PERIOD_TYPE - 13)) | (1 << (XULEParser.CONCEPT_LOCAL_NAME - 13)) | (1 << (XULEParser.CONCEPT_IS_NUMERIC - 13)) | (1 << (XULEParser.CONCEPT_IS_MONETARY - 13)) | (1 << (XULEParser.CONCEPT_HAS_ENUMERATIONS - 13)) | (1 << (XULEParser.CONCEPT_DATA_TYPE - 13)) | (1 << (XULEParser.CONCEPT_BASE_TYPE - 13)) | (1 << (XULEParser.CONCEPT_BALANCE - 13)) | (1 << (XULEParser.CONCEPT_ATTRIBUTE - 13)) | (1 << (XULEParser.CONCEPT - 13)) | (1 << (XULEParser.IDENTIFIER - 13)))) !== 0)) {
            this.state = 34;
            this.concept_filter();
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


function Concept_filterContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_concept_filter;
    this.localName = null; // Token
    this.periodType = null; // Token
    this.balance = null; // Token
    this.test = null; // Token
    return this;
}

Concept_filterContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
Concept_filterContext.prototype.constructor = Concept_filterContext;

Concept_filterContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

Concept_filterContext.prototype.CONCEPT = function() {
    return this.getToken(XULEParser.CONCEPT, 0);
};

Concept_filterContext.prototype.CONCEPT_LOCAL_NAME = function() {
    return this.getToken(XULEParser.CONCEPT_LOCAL_NAME, 0);
};

Concept_filterContext.prototype.SINGLE_QUOTED_STRING = function() {
    return this.getToken(XULEParser.SINGLE_QUOTED_STRING, 0);
};

Concept_filterContext.prototype.CONCEPT_PERIOD_TYPE = function() {
    return this.getToken(XULEParser.CONCEPT_PERIOD_TYPE, 0);
};

Concept_filterContext.prototype.INSTANT = function() {
    return this.getToken(XULEParser.INSTANT, 0);
};

Concept_filterContext.prototype.DURATION = function() {
    return this.getToken(XULEParser.DURATION, 0);
};

Concept_filterContext.prototype.CONCEPT_BALANCE = function() {
    return this.getToken(XULEParser.CONCEPT_BALANCE, 0);
};

Concept_filterContext.prototype.DEBIT = function() {
    return this.getToken(XULEParser.DEBIT, 0);
};

Concept_filterContext.prototype.CREDIT = function() {
    return this.getToken(XULEParser.CREDIT, 0);
};

Concept_filterContext.prototype.NONE = function() {
    return this.getToken(XULEParser.NONE, 0);
};

Concept_filterContext.prototype.CONCEPT_ATTRIBUTE = function() {
    return this.getToken(XULEParser.CONCEPT_ATTRIBUTE, 0);
};

Concept_filterContext.prototype.IDENTIFIER = function() {
    return this.getToken(XULEParser.IDENTIFIER, 0);
};

Concept_filterContext.prototype.value = function() {
    return this.getTypedRuleContext(ValueContext,0);
};

Concept_filterContext.prototype.dataType = function() {
    return this.getTypedRuleContext(DataTypeContext,0);
};

Concept_filterContext.prototype.CONCEPT_BASE_TYPE = function() {
    return this.getToken(XULEParser.CONCEPT_BASE_TYPE, 0);
};

Concept_filterContext.prototype.CONCEPT_DATA_TYPE = function() {
    return this.getToken(XULEParser.CONCEPT_DATA_TYPE, 0);
};

Concept_filterContext.prototype.booleanValue = function() {
    return this.getTypedRuleContext(BooleanValueContext,0);
};

Concept_filterContext.prototype.CONCEPT_HAS_ENUMERATIONS = function() {
    return this.getToken(XULEParser.CONCEPT_HAS_ENUMERATIONS, 0);
};

Concept_filterContext.prototype.CONCEPT_IS_MONETARY = function() {
    return this.getToken(XULEParser.CONCEPT_IS_MONETARY, 0);
};

Concept_filterContext.prototype.CONCEPT_IS_NUMERIC = function() {
    return this.getToken(XULEParser.CONCEPT_IS_NUMERIC, 0);
};

Concept_filterContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterConcept_filter(this);
	}
};

Concept_filterContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitConcept_filter(this);
	}
};




XULEParser.Concept_filterContext = Concept_filterContext;

XULEParser.prototype.concept_filter = function() {

    var localctx = new Concept_filterContext(this, this._ctx, this.state);
    this.enterRule(localctx, 4, XULEParser.RULE_concept_filter);
    var _la = 0; // Token type
    try {
        this.state = 67;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case XULEParser.CONCEPT:
        case XULEParser.IDENTIFIER:
            this.enterOuterAlt(localctx, 1);
            this.state = 39;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            if(_la===XULEParser.CONCEPT) {
                this.state = 37;
                this.match(XULEParser.CONCEPT);
                this.state = 38;
                this.match(XULEParser.T__5);
            }

            this.state = 41;
            this.identifier();
            break;
        case XULEParser.CONCEPT_LOCAL_NAME:
            this.enterOuterAlt(localctx, 2);
            this.state = 42;
            this.match(XULEParser.CONCEPT_LOCAL_NAME);
            this.state = 43;
            this.match(XULEParser.T__5);
            this.state = 44;
            localctx.localName = this.match(XULEParser.SINGLE_QUOTED_STRING);
            break;
        case XULEParser.CONCEPT_PERIOD_TYPE:
            this.enterOuterAlt(localctx, 3);
            this.state = 45;
            this.match(XULEParser.CONCEPT_PERIOD_TYPE);
            this.state = 46;
            this.match(XULEParser.T__5);
            this.state = 47;
            localctx.periodType = this._input.LT(1);
            _la = this._input.LA(1);
            if(!(_la===XULEParser.INSTANT || _la===XULEParser.DURATION)) {
                localctx.periodType = this._errHandler.recoverInline(this);
            }
            else {
            	this._errHandler.reportMatch(this);
                this.consume();
            }
            break;
        case XULEParser.CONCEPT_BALANCE:
            this.enterOuterAlt(localctx, 4);
            this.state = 48;
            this.match(XULEParser.CONCEPT_BALANCE);
            this.state = 49;
            this.match(XULEParser.T__5);
            this.state = 50;
            localctx.balance = this._input.LT(1);
            _la = this._input.LA(1);
            if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.T__6) | (1 << XULEParser.DEBIT) | (1 << XULEParser.CREDIT) | (1 << XULEParser.NONE))) !== 0))) {
                localctx.balance = this._errHandler.recoverInline(this);
            }
            else {
            	this._errHandler.reportMatch(this);
                this.consume();
            }
            break;
        case XULEParser.CONCEPT_ATTRIBUTE:
            this.enterOuterAlt(localctx, 5);
            this.state = 51;
            this.match(XULEParser.CONCEPT_ATTRIBUTE);
            this.state = 52;
            this.match(XULEParser.T__7);
            this.state = 53;
            this.match(XULEParser.IDENTIFIER);
            this.state = 54;
            this.match(XULEParser.T__8);
            this.state = 55;
            this.match(XULEParser.T__5);
            this.state = 59;
            this._errHandler.sync(this);
            switch(this._input.LA(1)) {
            case XULEParser.T__0:
            case XULEParser.T__2:
            case XULEParser.T__4:
                this.state = 56;
                this.value();
                break;
            case XULEParser.NONE:
                this.state = 57;
                this.match(XULEParser.NONE);
                break;
            case XULEParser.T__6:
                this.state = 58;
                this.match(XULEParser.T__6);
                break;
            default:
                throw new antlr4.error.NoViableAltException(this);
            }
            break;
        case XULEParser.CONCEPT_DATA_TYPE:
        case XULEParser.CONCEPT_BASE_TYPE:
            this.enterOuterAlt(localctx, 6);
            this.state = 61;
            _la = this._input.LA(1);
            if(!(_la===XULEParser.CONCEPT_DATA_TYPE || _la===XULEParser.CONCEPT_BASE_TYPE)) {
            this._errHandler.recoverInline(this);
            }
            else {
            	this._errHandler.reportMatch(this);
                this.consume();
            }
            this.state = 62;
            this.match(XULEParser.T__5);
            this.state = 63;
            this.dataType();
            break;
        case XULEParser.CONCEPT_IS_NUMERIC:
        case XULEParser.CONCEPT_IS_MONETARY:
        case XULEParser.CONCEPT_HAS_ENUMERATIONS:
            this.enterOuterAlt(localctx, 7);
            this.state = 64;
            localctx.test = this._input.LT(1);
            _la = this._input.LA(1);
            if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << XULEParser.CONCEPT_IS_NUMERIC) | (1 << XULEParser.CONCEPT_IS_MONETARY) | (1 << XULEParser.CONCEPT_HAS_ENUMERATIONS))) !== 0))) {
                localctx.test = this._errHandler.recoverInline(this);
            }
            else {
            	this._errHandler.reportMatch(this);
                this.consume();
            }
            this.state = 65;
            this.match(XULEParser.T__5);
            this.state = 66;
            this.booleanValue();
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

IdentifierContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterIdentifier(this);
	}
};

IdentifierContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitIdentifier(this);
	}
};




XULEParser.IdentifierContext = IdentifierContext;

XULEParser.prototype.identifier = function() {

    var localctx = new IdentifierContext(this, this._ctx, this.state);
    this.enterRule(localctx, 6, XULEParser.RULE_identifier);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 69;
        this.match(XULEParser.IDENTIFIER);
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


function ValueContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_value;
    return this;
}

ValueContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ValueContext.prototype.constructor = ValueContext;


ValueContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterValue(this);
	}
};

ValueContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitValue(this);
	}
};




XULEParser.ValueContext = ValueContext;

XULEParser.prototype.value = function() {

    var localctx = new ValueContext(this, this._ctx, this.state);
    this.enterRule(localctx, 8, XULEParser.RULE_value);
    try {
        this.enterOuterAlt(localctx, 1);

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

DataTypeContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterDataType(this);
	}
};

DataTypeContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitDataType(this);
	}
};




XULEParser.DataTypeContext = DataTypeContext;

XULEParser.prototype.dataType = function() {

    var localctx = new DataTypeContext(this, this._ctx, this.state);
    this.enterRule(localctx, 10, XULEParser.RULE_dataType);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 73;
        this.identifier();
        this.state = 74;
        this.match(XULEParser.T__9);
        this.state = 75;
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


function BooleanValueContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = XULEParser.RULE_booleanValue;
    return this;
}

BooleanValueContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
BooleanValueContext.prototype.constructor = BooleanValueContext;

BooleanValueContext.prototype.TRUE = function() {
    return this.getToken(XULEParser.TRUE, 0);
};

BooleanValueContext.prototype.FALSE = function() {
    return this.getToken(XULEParser.FALSE, 0);
};

BooleanValueContext.prototype.enterRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.enterBooleanValue(this);
	}
};

BooleanValueContext.prototype.exitRule = function(listener) {
    if(listener instanceof XULEListener ) {
        listener.exitBooleanValue(this);
	}
};




XULEParser.BooleanValueContext = BooleanValueContext;

XULEParser.prototype.booleanValue = function() {

    var localctx = new BooleanValueContext(this, this._ctx, this.state);
    this.enterRule(localctx, 12, XULEParser.RULE_booleanValue);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 77;
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


exports.XULEParser = XULEParser;
