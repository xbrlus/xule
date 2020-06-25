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
	TextDocumentSyncKind,
	WorkspaceFolder
} from 'vscode-languageserver';

import {TextDocument} from 'vscode-languageserver-textdocument';
import {CandidatesCollection, CodeCompletionCore} from 'antlr4-c3';
import {
	ANTLRErrorListener,
	CharStreams,
	CommonTokenStream,
	ParserRuleContext,
	RecognitionException,
	Recognizer,
	Token
} from 'antlr4ts';
import {IdentifierContext, PropertyAccessContext, XuleFileContext, XULEParser} from './parser/XULEParser';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';
import {
	bindingInfo,
	CompilationUnit,
	IdentifierInfo,
	IdentifierType,
	Namespace,
	SymbolTable,
	SymbolTableVisitor
} from './symbols';
import {Interval} from 'antlr4ts/misc/Interval';
import {ErrorNode} from "antlr4ts/tree";
import {
	SemanticCheckVisitor,
	wellKnownFunctions,
	wellKnownOutputAttributes,
	wellKnownProperties
} from "./semanticCheckVisitor";
import {EnhancedXULELexer} from "./enhancedXULELexer";
import * as fuzzysort from 'fuzzysort';
import {builtInNamespaces} from "./builtInNamespaces";
import * as fs from "fs";
import {getRange, LINES_REGEXP} from "./utils";

// Create a connection for the server. The connection uses Node's IPC as a transport.
// Also include all preview / proposed LSP features.
let connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager. The text document manager
// supports full document sync only
let documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

let hasConfigurationCapability: boolean = false;
let hasWorkspaceFolderCapability: boolean = false;
let hasDiagnosticRelatedInformationCapability: boolean = false;

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
			},
			// Tell the client that the server supports Go to definition
			definitionProvider: true
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

enum DebugLevel { 'off', 'verbose' }
interface XULELanguageSettings {
	
	server: { debug: DebugLevel; };
	checks: {
		functions: boolean,
		properties: boolean,
		variables: boolean
	},
	namespaces: { definitions: string[] },
	autoImports: string[]
}

// The global settings, used when the `workspace/configuration` request is not supported by the client.
// Please note that this is not the case when using this server with the client provided in this example
// but could happen with other clients.
const defaultSettings: XULELanguageSettings = {
	server: { debug: DebugLevel.off },
	checks: { functions: true, properties: true, variables: true },
	namespaces: { definitions: [] },
	autoImports: []
};
let globalSettings: XULELanguageSettings = defaultSettings;

// Cache the settings of all open documents
let documentSettings: Map<string, Thenable<XULELanguageSettings>> = new Map();

connection.onDidChangeConfiguration(change => {
	if (hasConfigurationCapability) {
		// Reset all cached document settings
		documentSettings.clear();
	} else {
		globalSettings = <XULELanguageSettings>((change.settings.xule || defaultSettings));
	}

	// Revalidate all open text documents
	documents.all().forEach(validateTextDocument);
});

const COMPILATION_UNIT = 'compilationUnit';
const PARSE_TREE = 'parseTree';
const SYMBOL_TABLE = 'symbolTable';

connection.onDefinition(params => {
	let document = documents.get(params.textDocument.uri);
	if(!document || !document[PARSE_TREE]) {
		return null;
	}
	let treeInfo = parseTreeAtPosition(document[PARSE_TREE], params.position.line + 1, params.position.character);
	if(!treeInfo) {
		return null;
	}
	let tree = treeInfo.node;
	if(tree instanceof IdentifierContext || (tree instanceof TerminalNode && tree.symbol.type == XULEParser.IDENTIFIER)) {
		let cu = document[COMPILATION_UNIT] as CompilationUnit;
		let symbolTable = document[SYMBOL_TABLE] as SymbolTable;
		let binding = symbolTable.lookup(tree.text, tree);
		let info = bindingInfo(binding, IdentifierType.CONSTANT);
		if(info && info.definedAt) {
			return definitionLocation(info, cu);
		}
		info = bindingInfo(binding, IdentifierType.FUNCTION);
		if(info && info.definedAt) {
			return definitionLocation(info, cu);
		}
		info = bindingInfo(binding, IdentifierType.VARIABLE);
		if(info && info.definedAt) {
			return definitionLocation(info, cu);
		}
	}
	return null;
});

function definitionLocation(info: any, cu: CompilationUnit) {
	let xuleFile = info.definedAt as ParseTree;
	while(xuleFile && !(xuleFile instanceof XuleFileContext)) {
		xuleFile = xuleFile.parent;
	}
	if(xuleFile) {
		let uri = cu.childUris[cu.children.indexOf(xuleFile)];
		let range = getRange(info.definedAt);
		return { uri: uri, range: range	}
	}
}

function getDocumentSettings(resource: string): Thenable<XULELanguageSettings> {
	if (!hasConfigurationCapability) {
		return Promise.resolve(globalSettings);
	}
	let result = documentSettings.get(resource);
	if (!result) {
		result = connection.workspace.getConfiguration({
			scopeUri: resource,
			section: 'xule'
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

function ensurePath(path: string) {
	let prefix = "file:";
	if (path.startsWith(prefix)) {
		path = path.substring(prefix.length);
	}
	while (path.startsWith("/")) {
		path = path.substring(1);
	}
	path = "/" + path;
	return path;
}

function canonicalizedPathToURI(path: string) {
	return "file://" + path;
}

//This could be cached if loading them every time is too slow
function loadNamespaces(path: string, namespaces: Namespace[]) {
	path = ensurePath(path);
	try {
		if (fs.existsSync(path)) {
				let data = fs.readFileSync(path);
				let definition = JSON.parse(data.toString());
				for (let uri in definition) {
					namespaces.push(new Namespace(uri, definition[uri]));
				}
		} else {
			let msg = "Namespace definitions file not found: " + path;
			connection.console.error(msg);
		}
	} catch (e) {
		connection.console.error(`Could not load namespaces from ${path}: ${e}`);
	}
}

function setupParser(textDocument: TextDocument, diagnostics: Diagnostic[]) {
	let text = textDocument.getText();
	let input = CharStreams.fromString(text);
	let lexer = new EnhancedXULELexer(input);

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
	return parser;
}

function workspacePathToAbsolutePath(f: WorkspaceFolder, path: string) {
	let uri = f.uri;
	if (!uri.endsWith("/")) {
		uri += "/";
	}
	return uri + path;
}

async function loadAdditionalNamespaces(settings: XULELanguageSettings) {
	let namespaces = [];
	for (let n in settings.namespaces.definitions) {
		let path = settings.namespaces.definitions[n].trim();
		if (path.startsWith("/") || path.startsWith("file://")) {
			loadNamespaces(path, namespaces);
		} else {
			let folders = await connection.workspace.getWorkspaceFolders();
			folders.forEach(f => loadNamespaces(workspacePathToAbsolutePath(f, path), namespaces));
		}
	}
	return namespaces;
}

function loadXuleFile(path: string, cu: CompilationUnit) {
	path = ensurePath(path);
	try {
		if (fs.existsSync(path)) {
			let data = fs.readFileSync(path);
			let input = CharStreams.fromString(data.toString());
			let lexer = new EnhancedXULELexer(input);
			let parser = new XULEParser(new CommonTokenStream(lexer));
			cu.add(parser.xuleFile(), canonicalizedPathToURI(path));
		} else {
			connection.console.error("AutoImport file not found: " + path);
		}
	} catch (e) {
		connection.console.error(`Could not load ${path}: ${e}`);
	}
}

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
	let diagnostics: Diagnostic[] = [];
	let parser = setupParser(textDocument, diagnostics);
	let parseTree = parser.xuleFile();
	let settings = await getDocumentSettings(textDocument.uri);
	let namespaces = await loadAdditionalNamespaces(settings);

	let docPath = ensurePath(textDocument.uri);
	let cu = new CompilationUnit();
	for(let i in settings.autoImports) {
		let path = settings.autoImports[i].trim();
		if (path.startsWith("/") || path.startsWith("file://")) {
			if(ensurePath(path) != docPath) {
				loadXuleFile(path, cu);
			}
		} else {
			let folders = await connection.workspace.getWorkspaceFolders();
			let folder = folders.find(f => textDocument.uri.startsWith(f.uri));
			if(!folder && folders.length > 0) {
				folder = folders[0];
			}
			if(folder) {
				let actualPath = ensurePath(workspacePathToAbsolutePath(folder, path));
				if(actualPath != docPath) {
					loadXuleFile(actualPath, cu);
				}
			}
		}
	}
	cu.add(parseTree, textDocument.uri);

	let symbolTableVisitor = new SymbolTableVisitor().withNamespaces(...builtInNamespaces, ...namespaces);
	let symbolTable = symbolTableVisitor.visit(cu);
	//Save these for code completions
	textDocument[COMPILATION_UNIT] = cu;
	textDocument[PARSE_TREE] = parseTree;
	textDocument['parser'] = parser;
	textDocument[SYMBOL_TABLE] = symbolTable;

	let semanticCheckVisitor = new SemanticCheckVisitor(diagnostics, symbolTable, textDocument);
	semanticCheckVisitor.checkFunctions  = settings.checks.functions;
	semanticCheckVisitor.checkProperties = settings.checks.properties;
	semanticCheckVisitor.checkVariables  = settings.checks.variables;
	semanticCheckVisitor.visit(parseTree);

	connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
}

class NodeInfo {
	constructor(public node: ParseTree, public offset: number, public tokenIndex: number) {}

	get textToMatch() {
		if(this.node instanceof ErrorNode) {
			return "";
		} else if(this.node instanceof TerminalNode) {
			if(this.node.symbol.type == XULEParser.IDENTIFIER) {
				let text = this.node.text.toLowerCase();
				if (this.offset < text.length - 1) {
					//The caret is inside an identifier or keyword. Let's match the existing string.
					text = text.substring(0, this.offset);
				}
				return text;
			} else {
				return ""; //Don't match tokens that are not keywords/identifiers
			}
		} else {
			return this.node.text;
		}
	}
}

function reconstructText(parserRule: ParserRuleContext): string {
	return parserRule.start.inputStream.getText(textInterval(parserRule))
}

function textInterval(parserRule: ParserRuleContext) {
	return new Interval(parserRule.start.startIndex, parserRule.stop.stopIndex);
}

function terminalNodeAtPosition(terminal: TerminalNode, line: number, column: number) {
	let token = terminal.symbol;
	let startLine = token.line;
	if(token.text.length == 0) {
		//Handle zero-length tokens, including the virtual tokens we insert for better code completion
		if(line == startLine && column == token.charPositionInLine) {
			return new NodeInfo(terminal, 0, terminal.symbol.tokenIndex);
		} else {
			return undefined;
		}
	}
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
		return new NodeInfo(terminal, offset, terminal.symbol.tokenIndex);
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
		return new NodeInfo(terminal, offset, terminal.symbol.tokenIndex);
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
			let subtree = closestSubtree(tree, line, column);
			return subtree ? <TerminalNode>subtree.node : null;
		}
	}
	if(context.childCount == 0) {
		//This can happen in case of error nodes
		return null;
	}
	//Since we invoke this only after not having found a token at the exact position, and we search depth-first,
	//we can be sure all child nodes are terminals
	let result = closestTerminal(context.getChild(0));
	for (let i = 1; i < context.childCount; i++) {
		const candidate = closestTerminal(context.getChild(i));
		if(candidate && !result) {
			result = candidate;
			continue;
		}
		if(!candidate) {
			continue;
		}
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
	return result ? new NodeInfo(result, result.text.length, result.symbol.tokenIndex) : null;
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
		XULEParser.RULE_assignedVariable, XULEParser.RULE_atIdentifier, XULEParser.RULE_booleanLiteral,
		XULEParser.RULE_identifier, XULEParser.RULE_propertyRef, XULEParser.RULE_direction,
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

function fuzzySearch(text: string, candidates: string[]) {
	if(text.length == 0) {
		return candidates.map(c => {
			return { target: c, score: 0, indexes: [] }
		});
	} else {
		return fuzzysort.go(text, candidates);
	}
}

function suggestIdentifiers(
	nodeInfo: NodeInfo, declarationType: IdentifierType, completionKind: CompletionItemKind,
	symbolTable: SymbolTable, completions: any[], global?: boolean) {
	function filter(n) {
		return function(b) {
			let results = fuzzySearch(n, [b.name.toLowerCase()]);
			return results.length > 0 &&
				   b.meaning.find(m => m instanceof IdentifierInfo && m.type == declarationType) !== undefined;
		}
	}

	let match = nodeInfo.textToMatch;
	let known = [];
	if(global) {
		let allMatching = symbolTable.symbols.map(s => s.environment.findAll(filter(match)));
		allMatching.forEach(list => known.push(list.filter(x => x)));
	} else {
		known = symbolTable.lookupAll(filter(match), nodeInfo.node);
	}
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

function suggestProperties(
	nodeInfo: NodeInfo, completionKind: CompletionItemKind, symbolTable: SymbolTable, completions: CompletionItem[]) {
	let textToMatch = nodeInfo.textToMatch;
	let candidates = [];
	for(let name in wellKnownProperties) {
		candidates.push(name);
	}
	maybeSuggest(candidates, textToMatch, completionKind, completions);
}

function maybeSuggest(candidates: string[], text: string, kind: CompletionItemKind, completions: CompletionItem[]) {
	let results = fuzzySearch(text, candidates);
	results.forEach(r => {
		completions.push({
			label: r.target,
			kind: kind
		});
	});
	return results.length > 0;
}

// This handler provides the initial list of the completion items.
connection.onCompletion(
	(_textDocumentPosition: TextDocumentPositionParams): Promise<CompletionItem[]> => {
		return computeCodeSuggestions(_textDocumentPosition);
	}
);

const returnOptions = [
	"arc-name", "arcrole", "arcrole-cycles-allowed", "arcrole-description", "arcrole-uri", "cycle",
	"dimension-sub-type", "dimension-type", "drs-role", "link-name", "navigation-depth", "navigation-order", "network",
	"order", "preferred-label", "preferred-label-role", "relationship", "result-order", "role", "role-description",
	"role-uri", "source", "source-name", "target", "target-name", "weight"];

function suggestFunctions(nodeInfo: NodeInfo, symbolTable: SymbolTable, completions: any[]) {
	let textToMatch = nodeInfo.textToMatch;
	//Well-known functions
	let candidates = [];
	for(let name in wellKnownFunctions) {
		candidates.push(name);
	}
	maybeSuggest(candidates, textToMatch, CompletionItemKind.Function, completions);
	//Declared functions
	suggestIdentifiers(nodeInfo, IdentifierType.FUNCTION, CompletionItemKind.Function, symbolTable, completions);
}

function suggestQNames(nodeInfo: NodeInfo, kind: CompletionItemKind, symbolTable: SymbolTable, completions: any[]) {
	let textToMatch = nodeInfo.textToMatch;
	let namespace = "";
	if(textToMatch.indexOf(':') >= 0) {
		let parts = textToMatch.split(':');
		namespace = parts[0];
		textToMatch = parts.slice(1).join(":");
	} else {
		let namespaces = [];
		for(let n in symbolTable.namespaces) {
			if(n) {
				namespaces.push(n + ":")}
		}
		maybeSuggest(namespaces, textToMatch, CompletionItemKind.Enum, completions);
	}
	let ns = symbolTable.lookupNamespace(namespace);
	if(ns && ns.namespace.names) {
		maybeSuggest(ns.namespace.names.map(n => n.localName), textToMatch, kind, completions);
	}
}

function suggestReturnOptions(text: string, completions: any[]) {
	maybeSuggest(returnOptions, text, CompletionItemKind.Keyword, completions);
}

function suggestOutputAttributes(symbolTable: SymbolTable, nodeInfo: NodeInfo, completions: any[]) {
	maybeSuggest(wellKnownOutputAttributes, nodeInfo.textToMatch, CompletionItemKind.Keyword, completions);
	suggestIdentifiers(nodeInfo, IdentifierType.OUTPUT_ATTRIBUTE, CompletionItemKind.Variable, symbolTable, completions);
}

/**
 * Suggests an identifier. Returns true iff a keyword can be suggested instead of an identifier
 * @param symbolTable 
 * @param nodeInfo 
 * @param candidates 
 * @param completions 
 */
function suggestAllIdentifiers(symbolTable: SymbolTable, nodeInfo: NodeInfo, candidates: CandidatesCollection, completions: any[]) {
	if(!nodeInfo) {
		return true;
	}
	let keywords = true;
	const text = nodeInfo.textToMatch;
	if (candidates.rules.has(XULEParser.RULE_propertyRef)) {
		suggestProperties(nodeInfo, CompletionItemKind.Property, symbolTable, completions);
		return false;
	}
	if (candidates.rules.has(XULEParser.RULE_booleanLiteral)) {
		maybeSuggest(["true", "false"], text, CompletionItemKind.Constant, completions);
	}
	if (candidates.rules.has(XULEParser.RULE_direction)) {
		maybeSuggest(["descendants"], text, CompletionItemKind.Keyword, completions);
		keywords = false;
	}
	if (candidates.rules.has(XULEParser.RULE_navigationReturnOption)) {
		suggestReturnOptions(text, completions);
		keywords = false;
	}
	if (candidates.rules.has(XULEParser.RULE_outputAttributeName)) {
		suggestOutputAttributes(symbolTable, nodeInfo, completions);
		keywords = false;
	}
	if(candidates.rules.has(XULEParser.RULE_assignedVariable)) {
		suggestIdentifiers(nodeInfo, IdentifierType.VARIABLE, CompletionItemKind.Variable, symbolTable, completions);
		keywords = false;
	}
	if(candidates.rules.has(XULEParser.RULE_atIdentifier)) {
		suggestQNames(nodeInfo, CompletionItemKind.EnumMember, symbolTable, completions);
		keywords = false;
	}
	if(candidates.rules.has(XULEParser.RULE_variableRead)) {
		suggestIdentifiers(nodeInfo, IdentifierType.CONSTANT, CompletionItemKind.Constant, symbolTable, completions);
		suggestIdentifiers(nodeInfo, IdentifierType.VARIABLE, CompletionItemKind.Variable, symbolTable, completions);
		suggestFunctions(nodeInfo, symbolTable, completions);
		if(!candidates.rules.has(XULEParser.RULE_atIdentifier)) {
			suggestQNames(nodeInfo, CompletionItemKind.EnumMember, symbolTable, completions);
		}
		maybeSuggest(["none"], text, CompletionItemKind.Keyword, completions);
		maybeSuggest(["skip"], text, CompletionItemKind.Keyword, completions); //TODO should we check that the context is appropriate? Can we?
	}
	return keywords
}

function suggestKeywords(parser: XULEParser, nodeInfo: NodeInfo, candidates: CandidatesCollection, completions: any[]) {
	let keywords = [];
	let text = nodeInfo ? nodeInfo.textToMatch : "";
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
		keywords.push(keyword);
	});
	maybeSuggest(keywords, text, CompletionItemKind.Keyword, completions);
}

async function computeCodeSuggestions(_textDocumentPosition: TextDocumentPositionParams): Promise<CompletionItem[]> {
	const documentURI = _textDocumentPosition.textDocument.uri;
	let document = documents.get(documentURI);
	if(document) {
		let settings = await getDocumentSettings(documentURI);
		const parser = document['parser'] as XULEParser;
		const symbolTable = document[SYMBOL_TABLE] as SymbolTable;
		if(parser) {
			const pos = _textDocumentPosition.position;
			const parseTree = document[PARSE_TREE] as ParseTree;
			const nodeInfo = parseTreeAtPosition(parseTree, pos.line + 1, pos.character);
			let tokenIndex = 0;
			if(nodeInfo) {
				tokenIndex = nodeInfo.tokenIndex;
				if(nodeInfo.node instanceof TerminalNode && nodeInfo.node.symbol.type != XULEParser.IDENTIFIER) {
					if(nodeInfo.offset == 0) {
						tokenIndex--;
					} else if(nodeInfo.offset >= nodeInfo.node.text.length) {
						tokenIndex++;
					}
				}
			}
			let core = setupCompletionCore(parser, settings);
			let candidates = core.collectCandidates(tokenIndex);
			let completions = [];

			let keywordsToo = suggestAllIdentifiers(symbolTable, nodeInfo, candidates, completions);
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

// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();
