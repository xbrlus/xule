/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

import {
	createConnection,
	TextDocuments,
	Diagnostic,
	DiagnosticSeverity,
	ProposedFeatures,
	InitializeParams,
	DidChangeConfigurationNotification,
	CompletionItem,
	CompletionItemKind,
	TextDocumentPositionParams,
	TextDocumentSyncKind,
	InitializeResult
} from 'vscode-languageserver';

import {
	TextDocument
} from 'vscode-languageserver-textdocument';
import { CodeCompletionCore } from 'antlr4-c3';
import { XULELexer } from './parser/XULELexer';
import { CharStreams, ANTLRErrorListener, RecognitionException, Recognizer, CommonTokenStream, Token, ParserRuleContext } from 'antlr4ts';
import { XULEParser } from './parser/XULEParser';
import { ParseTree } from 'antlr4ts/tree/ParseTree';
import { TerminalNode } from 'antlr4ts/tree/TerminalNode';

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

// The example settings
interface ExampleSettings {
	maxNumberOfProblems: number;
}

// The global settings, used when the `workspace/configuration` request is not supported by the client.
// Please note that this is not the case when using this server with the client provided in this example
// but could happen with other clients.
const defaultSettings: ExampleSettings = { maxNumberOfProblems: 1000 };
let globalSettings: ExampleSettings = defaultSettings;

// Cache the settings of all open documents
let documentSettings: Map<string, Thenable<ExampleSettings>> = new Map();

connection.onDidChangeConfiguration(change => {
	if (hasConfigurationCapability) {
		// Reset all cached document settings
		documentSettings.clear();
	} else {
		globalSettings = <ExampleSettings>(
			(change.settings.languageServerExample || defaultSettings)
		);
	}

	// Revalidate all open text documents
	documents.all().forEach(validateTextDocument);
});

function getDocumentSettings(resource: string): Thenable<ExampleSettings> {
	if (!hasConfigurationCapability) {
		return Promise.resolve(globalSettings);
	}
	let result = documentSettings.get(resource);
	if (!result) {
		result = connection.workspace.getConfiguration({
			scopeUri: resource,
			section: 'languageServerExample'
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
	// In this simple example we get the settings for every validate run.
	let settings = await getDocumentSettings(textDocument.uri);

	let diagnostics: Diagnostic[] = [];
	let text = textDocument.getText();
	let input = CharStreams.fromString(textDocument.getText());
	let lexer = new XULELexer(input);

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
				source: 'ex'
			};
			diagnostics.push(diagnostic);
		};
	}
	let reportingErrorListener = new ReportingLexerErrorListener();
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
				source: 'ex'
			};
			diagnostics.push(diagnostic);
		};
	}
	let parser = new XULEParser(new CommonTokenStream(lexer));
	parser.addErrorListener(new ReportingParserErrorListener());
	

	let parseTree = parser.xuleFile();
	textDocument['parseTree'] = parseTree;
	textDocument['parser'] = parser;
	connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
}

connection.onDidChangeWatchedFiles(_change => {
	// Monitored files have change in VSCode
	connection.console.log('We received an file change event');
});

/**
 * Returns the narrowest parse tree which covers the given position.
 * Returns undefined if none is found.
 * Note that currently this doesn't handle multiline tokens.
 */
function parseTreeFromPosition(tree: ParseTree, line: number, column: number): ParseTree | undefined {
    // Does the root node actually contain the position? If not we don't need to look further.
    if (tree instanceof TerminalNode) {
        let terminal = (tree as TerminalNode);
        let token = terminal.symbol;
        if (token.line != line) {
			return undefined; //TODO what if the token spans multiple lines?
		}

        let tokenStop = token.charPositionInLine + (token.stopIndex - token.startIndex + 1);
        if (token.charPositionInLine <= column && tokenStop >= column) {
            return terminal;
        }
        return undefined;
    } else {
        let context = (tree as ParserRuleContext);
        if (!context.start || !context.stop) { // Invalid tree?
            return undefined;
        }

        if (context.start.line > line || (context.start.line == line && column < context.start.charPositionInLine)) {
            return undefined;
        }

        let tokenStop = context.stop.charPositionInLine + (context.stop.stopIndex - context.stop.startIndex + 1);
        if (context.stop.line < line || (context.stop.line == line && tokenStop < column)) {
            return undefined;
        }

		if (context.childCount > 0) {
            for (let i = 0; i < context.childCount; i++) {
                let result = parseTreeFromPosition(context.getChild(i), line, column);
                if (result) {
                    return result;
                }
            }
        }
        return context;

    }
}

// This handler provides the initial list of the completion items.
connection.onCompletion(
	(_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
		// The pass parameter contains the position of the text document in
		// which code complete got requested. For the example we ignore this
		// info and always provide the same completion items.
		let document = documents.get(_textDocumentPosition.textDocument.uri);
		if(document) {
			let parser = document['parser'] as XULEParser;
			if(parser) {
				const pos = _textDocumentPosition.position;
				const context = parseTreeFromPosition(document['parseTree'] as ParseTree, pos.line, pos.character);
				let tokenIndex: number = -1;
				if(context instanceof TerminalNode) {
					tokenIndex = context.symbol.startIndex;
				} else if(context instanceof ParserRuleContext) {
					tokenIndex = context.start.tokenIndex;
				}
				let core = new CodeCompletionCore(parser);
				let candidates = core.collectCandidates(tokenIndex);
				let completions = [];
				candidates.tokens.forEach((value, key, map) => {
					completions.push({
						label: parser.vocabulary.getDisplayName(key),
						kind: CompletionItemKind.Text
					});
				});
				return completions;
			}
		}
		return [];
	}
);

// This handler resolves additional information for the item selected in
// the completion list.
connection.onCompletionResolve(
	(item: CompletionItem): CompletionItem => {
		if (item.data === 1) {
			item.detail = 'TypeScript details';
			item.documentation = 'TypeScript documentation';
		} else if (item.data === 2) {
			item.detail = 'JavaScript details';
			item.documentation = 'JavaScript documentation';
		}
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
