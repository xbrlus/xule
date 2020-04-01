// Generated from XULE.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');

// This class defines a complete listener for a parse tree produced by XULEParser.
function XULEListener() {
	antlr4.tree.ParseTreeListener.call(this);
	return this;
}

XULEListener.prototype = Object.create(antlr4.tree.ParseTreeListener.prototype);
XULEListener.prototype.constructor = XULEListener;

// Enter a parse tree produced by XULEParser#factset.
XULEListener.prototype.enterFactset = function(ctx) {
};

// Exit a parse tree produced by XULEParser#factset.
XULEListener.prototype.exitFactset = function(ctx) {
};


// Enter a parse tree produced by XULEParser#aspect_filter.
XULEListener.prototype.enterAspect_filter = function(ctx) {
};

// Exit a parse tree produced by XULEParser#aspect_filter.
XULEListener.prototype.exitAspect_filter = function(ctx) {
};


// Enter a parse tree produced by XULEParser#concept_filter.
XULEListener.prototype.enterConcept_filter = function(ctx) {
};

// Exit a parse tree produced by XULEParser#concept_filter.
XULEListener.prototype.exitConcept_filter = function(ctx) {
};


// Enter a parse tree produced by XULEParser#identifier.
XULEListener.prototype.enterIdentifier = function(ctx) {
};

// Exit a parse tree produced by XULEParser#identifier.
XULEListener.prototype.exitIdentifier = function(ctx) {
};


// Enter a parse tree produced by XULEParser#value.
XULEListener.prototype.enterValue = function(ctx) {
};

// Exit a parse tree produced by XULEParser#value.
XULEListener.prototype.exitValue = function(ctx) {
};


// Enter a parse tree produced by XULEParser#dataType.
XULEListener.prototype.enterDataType = function(ctx) {
};

// Exit a parse tree produced by XULEParser#dataType.
XULEListener.prototype.exitDataType = function(ctx) {
};


// Enter a parse tree produced by XULEParser#booleanValue.
XULEListener.prototype.enterBooleanValue = function(ctx) {
};

// Exit a parse tree produced by XULEParser#booleanValue.
XULEListener.prototype.exitBooleanValue = function(ctx) {
};



exports.XULEListener = XULEListener;