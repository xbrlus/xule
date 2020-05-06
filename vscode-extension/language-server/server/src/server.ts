/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

import {
	CompletionItem,
	CompletionItemKind,
	createConnection,
	Diagnostic,
	DiagnosticSeverity,
	DidChangeConfigurationNotification,
	InitializeParams,
	InitializeResult,
	ProposedFeatures,
	TextDocumentPositionParams,
	TextDocuments,
	TextDocumentSyncKind
} from 'vscode-languageserver';

import {TextDocument} from 'vscode-languageserver-textdocument';
import {CandidatesCollection, CodeCompletionCore} from 'antlr4-c3';
import {
	ANTLRErrorListener,
	CharStreams,
	CommonToken,
	CommonTokenStream,
	ParserRuleContext,
	RecognitionException,
	Recognizer,
	Token
} from 'antlr4ts';
import {
	ExpressionContext,
	IdentifierContext,
	PropertyAccessContext,
	XULEParser
} from './parser/XULEParser';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';
import {IdentifierInfo, IdentifierType, SymbolTable, SymbolTableVisitor} from './symbols';
import {Interval} from 'antlr4ts/misc/Interval';
import {ErrorNode} from "antlr4ts/tree";
import {SemanticCheckVisitor, wellKnownFunctions, wellKnownProperties} from "./semanticCheckVisitor";
import {SafeXULELexer} from "./safeXULELexer";

// Create a connection for the server. The connection uses Node's IPC as a transport.
// Also include all preview / proposed LSP features.
let connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager. The text document manager
// supports full document sync only
let documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

let hasConfigurationCapability: boolean = false;
let hasWorkspaceFolderCapability: boolean = false;
let hasDiagnosticRelatedInformationCapability: boolean = false;

const LINES_REGEXP = /[^\n\r]*(\r\n|\n|\r)|[^\n\r]+$/g;

connection.onInitialize((params: InitializeParams) => {
	let capabilities = params.capabilities;

	// Does the client support the `workspace/configuration` request?
	// If not, we will fall back using global settings
	hasConfigurationCapability = !!(
		capabilities.workspace && !!capabilities.workspace.configuration
	);
	hasWorkspaceFolderCapability = !!(
		capabilities.workspace && !!capabilities.workspace.workspaceFolders
	);
	hasDiagnosticRelatedInformationCapability = !!(
		capabilities.textDocument &&
		capabilities.textDocument.publishDiagnostics &&
		capabilities.textDocument.publishDiagnostics.relatedInformation
	);

	const result: InitializeResult = {
		capabilities: {
			textDocumentSync: TextDocumentSyncKind.Full,
			// Tell the client that the server supports code completion
			completionProvider: {
				resolveProvider: true
			}
		}
	};
	if (hasWorkspaceFolderCapability) {
		result.capabilities.workspace = {
			workspaceFolders: {
				supported: true
			}
		};
	}
	return result;
});

connection.onInitialized(() => {
	if (hasConfigurationCapability) {
		// Register for all configuration changes.
		connection.client.register(DidChangeConfigurationNotification.type, undefined);
	}
	if (hasWorkspaceFolderCapability) {
		connection.workspace.onDidChangeWorkspaceFolders(_event => {
			connection.console.log('Workspace folder change event received.');
		});
	}
});

enum DebugLevel { 'off', 'verbose' };
interface XULELanguageSettings {
	
	server: { debug: DebugLevel; };
	checks: {
		functions: boolean,
		properties: boolean,
		variables: boolean
	}
}

// The global settings, used when the `workspace/configuration` request is not supported by the client.
// Please note that this is not the case when using this server with the client provided in this example
// but could happen with other clients.
const defaultSettings: XULELanguageSettings = {
	server: { debug: DebugLevel.off },
	checks: { functions: true, properties: true, variables: true }
};
let globalSettings: XULELanguageSettings = defaultSettings;

// Cache the settings of all open documents
let documentSettings: Map<string, Thenable<XULELanguageSettings>> = new Map();

connection.onDidChangeConfiguration(change => {
	if (hasConfigurationCapability) {
		// Reset all cached document settings
		documentSettings.clear();
	} else {
		globalSettings = <XULELanguageSettings>((change.settings.xuleLanguage || defaultSettings));
	}

	// Revalidate all open text documents
	documents.all().forEach(validateTextDocument);
});

function getDocumentSettings(resource: string): Thenable<XULELanguageSettings> {
	if (!hasConfigurationCapability) {
		return Promise.resolve(globalSettings);
	}
	let result = documentSettings.get(resource);
	if (!result) {
		result = connection.workspace.getConfiguration({
			scopeUri: resource,
			section: 'xuleLanguage'
		});
		documentSettings.set(resource, result);
	}
	return result;
}

// Only keep settings for open documents
documents.onDidClose(e => {
	documentSettings.delete(e.document.uri);
});

// The content of a text document has changed. This event is emitted
// when the text document first opened or when its content has changed.
documents.onDidChangeContent(change => {
	validateTextDocument(change.document);
});

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
	let diagnostics: Diagnostic[] = [];
	let text = textDocument.getText();
	let input = CharStreams.fromString(text);
	let lexer = new SafeXULELexer(input);

	class ReportingLexerErrorListener implements ANTLRErrorListener<number> {
		syntaxError? = <T extends number>(recognizer: Recognizer<T, any>, offendingSymbol: T | undefined, line: number, charPositionInLine: number, msg: string, e: RecognitionException | undefined) => {
			let range = null;
			if(e) {
				let token = e.getOffendingToken();
				if(token) {
					range = {
						start: textDocument.positionAt(token.startIndex),
						end: textDocument.positionAt(token.stopIndex + 1)
					}
				}
			}
			let diagnostic: Diagnostic = {
				severity: DiagnosticSeverity.Error,
				range: range,
				message: msg,
				source: 'XULE syntax checker'
			};
			diagnostics.push(diagnostic);
		};
	}
	lexer.addErrorListener(new ReportingLexerErrorListener());

	class ReportingParserErrorListener implements ANTLRErrorListener<Token> {
		syntaxError? = <T extends Token>(recognizer: Recognizer<T, any>, offendingSymbol: T | undefined, line: number, charPositionInLine: number, msg: string, e: RecognitionException | undefined) => {
			let range = null;
			if(e) {
				let token = e.getOffendingToken();
				if(token) {
					range = {
						start: textDocument.positionAt(token.startIndex),
						end: textDocument.positionAt(token.stopIndex + 1)
					}
				}
			} else if(offendingSymbol) {
				range = {
					start: textDocument.positionAt(offendingSymbol.startIndex),
					end: textDocument.positionAt(offendingSymbol.stopIndex + 1)
				}
			}
			let diagnostic: Diagnostic = {
				severity: DiagnosticSeverity.Error,
				range: range,
				message: msg,
				source: 'XULE syntax checker'
			};
			diagnostics.push(diagnostic);
		};
	}
	let parser = new XULEParser(new CommonTokenStream(lexer));
	parser.addErrorListener(new ReportingParserErrorListener());

	let parseTree = parser.xuleFile();
	let symbolTable = new SymbolTableVisitor().visit(parseTree);
	textDocument['parseTree'] = parseTree;
	textDocument['parser'] = parser;
	textDocument['symbolTable'] = symbolTable;

	let semanticCheckVisitor = new SemanticCheckVisitor(diagnostics, symbolTable, textDocument);
	let settings = await getDocumentSettings(textDocument.uri);
	semanticCheckVisitor.checkFunctions = settings.checks.functions;
	semanticCheckVisitor.checkProperties = settings.checks.properties;
	semanticCheckVisitor.checkVariables = settings.checks.variables;
	semanticCheckVisitor.visit(parseTree);
	connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
}

type NodeInfo = { node: ParseTree, offset: number, tokenIndex: number };

function reconstructText(parserRule: ParserRuleContext): string {
	return parserRule.start.inputStream.getText(textInterval(parserRule))
}

function textInterval(parserRule: ParserRuleContext) {
	return new Interval(parserRule.start.startIndex, parserRule.stop.stopIndex);
}

function terminalNodeAtPosition(terminal: TerminalNode, line: number, column: number) {
	let token = terminal.symbol;
	let startLine = token.line;
	const lines = token.text.match(LINES_REGEXP);
	let endLine = startLine + lines.length - 1;
	// Does the terminal node actually contain the position? If not we don't need to look further.
	if (startLine > line || endLine < line) {
		return undefined;
	}

	if (startLine != endLine && line < endLine) {
		//The token spans multiple lines and we're inside it, but not inside its last line
		let offset = column;
		for (let i = 0; i < line - startLine; i++) {
			offset += lines[i].length;
		}
		return {node: terminal, offset: offset, tokenIndex: terminal.symbol.tokenIndex};
	}

	let tokenStartInLine = line == startLine ? token.charPositionInLine : 0;
	let tokenStopInLine = 0;
	if (line == startLine) {
		if (startLine != endLine) {
			tokenStopInLine = column;
		} else {
			tokenStopInLine = token.charPositionInLine + (token.stopIndex - token.startIndex + 1);
		}
	} else if (line == endLine) {
		if(startLine == endLine) {
			throw "You've found a bug: startLine == endLine. This was not supposed to happen.";
		}
		tokenStopInLine =
			token.stopIndex - token.startIndex -
			Math.max(token.text.lastIndexOf('\n'), token.text.lastIndexOf('\r'));
	} else {
		tokenStopInLine = column;
	}
	if (tokenStartInLine <= column && tokenStopInLine >= column) {
		let offset = column - tokenStartInLine;
		for (let i = 0; i < line - startLine; i++) {
			offset += lines[i].length;
		}
		if(terminal.symbol.type == XULEParser.OPEN_BRACKET || terminal.symbol.type == XULEParser.CLOSE_BRACKET ||
		   terminal.symbol.type == XULEParser.OPEN_CURLY || terminal.symbol.type == XULEParser.CLOSE_CURLY ||
		   terminal.symbol.type == XULEParser.OPEN_PAREN || terminal.symbol.type == XULEParser.CLOSE_PAREN ||
		   terminal.symbol.type == XULEParser.COMMA) {
			if(offset == 0) {
				//Return the (virtual) token before this one
				return {node: new TerminalNode(new CommonToken(0, "")), offset: 0, tokenIndex: terminal.symbol.tokenIndex - 1};
			} else if(offset == terminal.text.length) {
				//Return the (virtual) token after this one
				return {node: new TerminalNode(new CommonToken(0, "")), offset: 0, tokenIndex: terminal.symbol.tokenIndex + 1};
			}
		}

		return {node: terminal, offset: offset, tokenIndex: terminal.symbol.tokenIndex};
	}
	return undefined;
}

function ruleContextAtPosition(context: ParserRuleContext, line: number, column: number) {
	//Parse tree is entirely before or after the given line
	if (context.start.line > line || context.stop.line < line) {
		return undefined;
	}
	//Parse tree starts after the given line and column
	if (line == context.start.line && column < context.start.charPositionInLine) {
		return undefined;
	}
	if (line == context.stop.line) {
		const lines = reconstructText(context).match(LINES_REGEXP);
		let endColumn = lines[lines.length - 1].length;
		if (line == context.start.line) {
			endColumn += context.start.charPositionInLine;
		}
		//Parse tree stops before the given line and column
		if (column > endColumn) {
			return undefined;
		}
	}
	if (context.childCount > 0) {
		for (let i = 0; i < context.childCount; i++) {
			let result = parseTreeAtPosition(context.getChild(i), line, column);
			if (result) {
				return result;
			}
		}
		return closestSubtree(context, line, column);
	}
	return undefined;
}

/**
 * Returns the token at the given position in the stream.
 * Returns undefined if none is found.
 */
function parseTreeAtPosition(tree: ParseTree, line: number, column: number): NodeInfo {
    if (tree instanceof TerminalNode) {
		return terminalNodeAtPosition(tree, line, column);
	} else {
		return ruleContextAtPosition(tree as ParserRuleContext, line, column);
	}
}

function closestSubtree(context: ParseTree, line, column) {
	function closestTerminal(tree: ParseTree): TerminalNode {
		if(tree instanceof TerminalNode) {
			return tree;
		} else {
			return closestSubtree(tree, line, column).node;
		}
	}
	//Since we invoke this only after not having found a token at the exact position, and we search depth-first,
	//we can be sure all child nodes are terminals
	let result = closestTerminal(context.getChild(0));
	for (let i = 1; i < context.childCount; i++) {
		const candidate = closestTerminal(context.getChild(i));
		let startLine = candidate.symbol.line;
		const lines = candidate.text.match(LINES_REGEXP);
		let endLine = startLine + lines.length - 1;
		if(endLine <= line && candidate.symbol.stopIndex > result.symbol.stopIndex) {
			if(endLine < line) {
				result = candidate;
			} else {
				let pos;
				if(startLine == endLine) {
					pos = candidate.symbol.charPositionInLine + candidate.text.length;
				} else {
					pos = lines[lines.length - 1].length;
				}
				if(pos < column) {
					result = candidate;
				}
			}
		}
	}
	return { node: result, offset: result.text.length, tokenIndex: result.symbol.tokenIndex };
}

function setupCompletionCore(parser: XULEParser, settings: XULELanguageSettings) {
	let core = new CodeCompletionCore(parser);
	core.ignoredTokens = new Set([
		XULEParser.ADD_L, XULEParser.ADD_LR, XULEParser.ADD_R,
		XULEParser.AND_OP, XULEParser.ASSIGN, XULEParser.ASSERT_RULE_NAME, XULEParser.AT,
		XULEParser.CLOSE_BRACKET, XULEParser.CLOSE_CURLY, XULEParser.CLOSE_PAREN,
		XULEParser.COMMA, XULEParser.DIV,
		XULEParser.DOT, XULEParser.DOUBLE_QUOTE, XULEParser.EOF, XULEParser.EQUALS,
		XULEParser.GT, XULEParser.GTE, XULEParser.LT, XULEParser.LTE, XULEParser.MINUS,
		XULEParser.NOT_EQUALS,
		XULEParser.OPEN_BRACKET, XULEParser.OPEN_CURLY, XULEParser.OPEN_PAREN,
		XULEParser.PLUS,
		XULEParser.SEMI, XULEParser.SHARP, XULEParser.SIMM_DIFF, XULEParser.SINGLE_QUOTE, XULEParser.STRING_CONTENTS,
		XULEParser.SUB_L, XULEParser.SUB_LR, XULEParser.SUB_R,
		XULEParser.TIMES
	]);
	core.preferredRules = new Set([
		XULEParser.RULE_assignedVariable, XULEParser.RULE_booleanLiteral,
		XULEParser.RULE_identifier, XULEParser.RULE_propertyAccess, XULEParser.RULE_direction,
		XULEParser.RULE_navigationReturnOption, XULEParser.RULE_outputAttributeName,
		XULEParser.RULE_variableRead
	]);
	if(settings.server.debug == DebugLevel.verbose) {
		core.showDebugOutput = true;
    	core.showResult = true;
    	core.showRuleStack = true;
	}
	return core;
}

function suggestIdentifier(
	node: ParseTree, declarationType: IdentifierType, completionKind: CompletionItemKind,
	symbolTable: SymbolTable, completions: any[]) {
	function filter(n) {
		return function(b) {
			return b.name.toLowerCase().startsWith(n) &&
				   b.meaning.find(m => m instanceof IdentifierInfo && m.type == declarationType) !== undefined;
		}
	}

	let match = node.text.toLowerCase();
	let known = symbolTable.lookupAll(filter(match), node);
	known.forEach(c => {
		if (!completions.find(co => co.label == c.name)) {
			let label: string = c.name;
			let item: CompletionItem = { label: label, kind: completionKind };
			if(label.startsWith('$') && match.length > 0) {
				item.insertText = label.substring(1); //VSCode messes up with $
			}
			completions.push(item);
		}
	});
}

function findPropertyAccessContext(node: ParseTree) {
	while (!(node instanceof PropertyAccessContext)) {
		if (node.parent) {
			node = node.parent;
		} else {
			return null;
		}
	}
	return node;
}

function indexOfNode(parent: ParseTree, node: ParseTree) {
	for(let i = 0; i < parent.childCount; i++) {
		if(parent.getChild(i) == node) {
			return i;
		}
	}
	return -1;
}

function suggestProperty(
	node: ParseTree, completionKind: CompletionItemKind, symbolTable: SymbolTable, completions: any[]) {
	let inIdentifier = node instanceof IdentifierContext || (node instanceof TerminalNode && node.symbol.type == XULEParser.IDENTIFIER);
	let textToMatch = inIdentifier ? node.text : "";
	let addDot = !inIdentifier && !(node instanceof TerminalNode && node.symbol.type == XULEParser.DOT);
	for(let name in wellKnownProperties) {
		maybeSuggest(addDot ? '.' + name : name, textToMatch, completionKind, completions);
	}
}

function maybeSuggest(candidate: string, text: string, kind: CompletionItemKind, completions: any[]) {
	if (candidate.startsWith(text)) {
		completions.push({
			label: candidate,
			kind: kind
		});
		return true;
	}
	return false;
}

// This handler provides the initial list of the completion items.
connection.onCompletion(
	(_textDocumentPosition: TextDocumentPositionParams): Promise<CompletionItem[]> => {
		let result = [];
		return computeCodeSuggestions(_textDocumentPosition);
	}
);

const returnOptions = [
	"arc-name", "arcrole", "arcrole-cycles-allowed", "arcrole-description", "arcrole-uri", "cycle",
	"dimension-sub-type", "dimension-type", "drs-role", "link-name", "navigation-depth", "navigation-order", "network",
	"order", "preferred-label", "preferred-label-role", "relationship", "result-order", "role", "role-description",
	"role-uri", "source", "source-name", "target", "target-name", "weight"];

const outputAttributes = [
	"message", "rule-suffix", "rule-focus", "severity"
];

function suggestFunction(nodeInfo: NodeInfo, symbolTable: SymbolTable, completions: any[]) {
	let textToMatch = nodeInfo.node.text.toLowerCase();
	//Well-known functions
	for(let name in wellKnownFunctions) {
		maybeSuggest(name, textToMatch, CompletionItemKind.Function, completions);
	}
	//Declared functions
	suggestIdentifier(nodeInfo.node, IdentifierType.FUNCTION, CompletionItemKind.Function, symbolTable, completions);
}

function suggestReturnOption(text: string, completions: any[]) {
	for(let o in returnOptions) {
		maybeSuggest(returnOptions[o], text, CompletionItemKind.Keyword, completions);
	}
}

function suggestOutputAttribute(symbolTable: SymbolTable, nodeInfo: NodeInfo, completions: any[]) {
	for(let o in outputAttributes) {
		maybeSuggest(outputAttributes[o], nodeInfo.node.text, CompletionItemKind.Keyword, completions);
	}
	suggestIdentifier(nodeInfo.node, IdentifierType.OUTPUT_ATTRIBUTE, CompletionItemKind.Variable, symbolTable, completions);
}

/**
 * Suggests an identifier. Returns true iff a keyword can be suggested instead of an identifier
 * @param symbolTable 
 * @param nodeInfo 
 * @param candidates 
 * @param completions 
 */
function suggestIdentifiers(symbolTable: SymbolTable, nodeInfo: NodeInfo, candidates: CandidatesCollection, completions: any[]) {
	if(!nodeInfo) {
		return true;
	}
	let keywords = true;
	const text = nodeInfo.node instanceof ErrorNode ? "" : nodeInfo.node.text.toLowerCase();
	if (candidates.rules.has(XULEParser.RULE_booleanLiteral)) {
		maybeSuggest("true", text, CompletionItemKind.Constant, completions);
		maybeSuggest("false", text, CompletionItemKind.Constant, completions);
	}
	if (candidates.rules.has(XULEParser.RULE_propertyAccess)) {
		suggestProperty(nodeInfo.node, CompletionItemKind.Property, symbolTable, completions);
		keywords = false;
	}
	if (candidates.rules.has(XULEParser.RULE_direction)) {
		maybeSuggest("descendants", text, CompletionItemKind.Keyword, completions);
		keywords = false;
	}
	if (candidates.rules.has(XULEParser.RULE_navigationReturnOption)) {
		suggestReturnOption(text, completions);
		keywords = false;
	}
	if (candidates.rules.has(XULEParser.RULE_outputAttributeName)) {
		suggestOutputAttribute(symbolTable, nodeInfo, completions);
		keywords = false;
	}
	if(candidates.rules.has(XULEParser.RULE_assignedVariable)) {
		suggestIdentifier(nodeInfo.node, IdentifierType.VARIABLE, CompletionItemKind.Variable, symbolTable, completions);
		keywords = false;
	}
	if(candidates.rules.has(XULEParser.RULE_variableRead)) {
		suggestIdentifier(nodeInfo.node, IdentifierType.CONSTANT, CompletionItemKind.Constant, symbolTable, completions);
		suggestIdentifier(nodeInfo.node, IdentifierType.VARIABLE, CompletionItemKind.Variable, symbolTable, completions);
		suggestFunction(nodeInfo, symbolTable, completions);
		maybeSuggest("none", text, CompletionItemKind.Keyword, completions);
		maybeSuggest("skip", text, CompletionItemKind.Keyword, completions); //TODO should we check that the context is appropriate? Can we?
	}
	return keywords
}

function suggestKeywords(parser: XULEParser, nodeInfo: NodeInfo, candidates: CandidatesCollection, completions: any[]) {
	candidates.tokens.forEach((value, key, map) => {
		if (key == XULEParser.IDENTIFIER || key == XULEParser.TRUE || key == XULEParser.FALSE) {
			return; //It's handled above
		}
		let keyword = parser.vocabulary.getDisplayName(key).toLowerCase();
		if (key == XULEParser.ASSERT_SATISFIED) {
			keyword = 'satisfied'
		} else if (key == XULEParser.ASSERT_UNSATISFIED) {
			keyword = 'unsatisfied'
		} else if(key == XULEParser.OUTPUT_ATTRIBUTE) {
			keyword = 'output-attribute'
		} else if(key == XULEParser.RULE_NAME_PREFIX) {
			keyword = 'rule-name-prefix'
		}
		let text = "";
		if (nodeInfo && !(nodeInfo.node instanceof ErrorNode) && nodeInfo.node.text) {
			text = nodeInfo.node.text.toLowerCase();
			if (nodeInfo.offset < nodeInfo.node.text.length - 1) {
				//The caret is inside a keyword. Let's match the existing string.
				text = text.substring(0, nodeInfo.offset);
			}
		}
		maybeSuggest(keyword, text, CompletionItemKind.Keyword, completions);
	});
}

async function computeCodeSuggestions(_textDocumentPosition: TextDocumentPositionParams): Promise<CompletionItem[]> {
	const documentURI = _textDocumentPosition.textDocument.uri;
	let document = documents.get(documentURI);
	if(document) {
		let settings = await getDocumentSettings(documentURI);
		const parser = document['parser'] as XULEParser;
		const symbolTable = document['symbolTable'] as SymbolTable;
		if(parser) {
			const pos = _textDocumentPosition.position;
			const parseTree = document['parseTree'] as ParseTree;
			const nodeInfo = parseTreeAtPosition(parseTree, pos.line + 1, pos.character);
			let tokenIndex = nodeInfo ? nodeInfo.tokenIndex : 0;
			let core = setupCompletionCore(parser, settings);
			let candidates = core.collectCandidates(tokenIndex);
			let completions = [];

			let keywordsToo = suggestIdentifiers(symbolTable, nodeInfo, candidates, completions);
			if(keywordsToo) {
				suggestKeywords(parser, nodeInfo, candidates, completions);
			}
			return completions;
		}
	}
	return [];
}

// This handler resolves additional information for the item selected in
// the completion list.
connection.onCompletionResolve(
	(item: CompletionItem): CompletionItem => {
		return item;
	}
);

/*
connection.onDidOpenTextDocument((params) => {
	// A text document got opened in VSCode.
	// params.textDocument.uri uniquely identifies the document. For documents store on disk this is a file URI.
	// params.textDocument.text the initial full content of the document.
	connection.console.log(`${params.textDocument.uri} opened.`);
});
connection.onDidChangeTextDocument((params) => {
	// The content of a text document did change in VSCode.
	// params.textDocument.uri uniquely identifies the document.
	// params.contentChanges describe the content changes to the document.
	connection.console.log(`${params.textDocument.uri} changed: ${JSON.stringify(params.contentChanges)}`);
});
connection.onDidCloseTextDocument((params) => {
	// A text document got closed in VSCode.
	// params.textDocument.uri uniquely identifies the document.
	connection.console.log(`${params.textDocument.uri} closed.`);
});
*/

// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();
