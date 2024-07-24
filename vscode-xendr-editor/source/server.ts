import { DidChangeTextDocumentParams, DidOpenTextDocumentParams, InitializeParams, InitializeResult, TextDocumentSyncKind, createConnection } from "vscode-languageserver/node";
import { generateXuleCode } from "./generator";
import { parse } from "./parser";

let connection = createConnection();
connection.onInitialize(onInitialize);
connection.onDidOpenTextDocument(onDidOpenTextDocument);
connection.onDidChangeTextDocument(onDidChangeTextDocument);
connection.listen();

function onInitialize(event: InitializeParams): InitializeResult
{
	return { capabilities:
	{
		textDocumentSync: TextDocumentSyncKind.Full,
		completionProvider: {}
	}};
}

function onDidOpenTextDocument(event: DidOpenTextDocumentParams)
{
	process(event.textDocument.uri, event.textDocument.text);
}

function onDidChangeTextDocument(event: DidChangeTextDocumentParams)
{
	for (let change of event.contentChanges)
	{
		process(event.textDocument.uri, change.text);
	}
}

function process(htmlUri: string, htmlCode: string)
{
	let xendrReport = parse(htmlCode);

	if (xendrReport.isValid())
	{
		let xuleUri = htmlUri + ".xule";
		let xuleCode = generateXuleCode(xendrReport);

		writeFile(xuleUri, xuleCode);
	}
}

function writeFile(uri: string, content: string)
{
	connection.workspace.applyEdit({edit: {documentChanges:
	[
		{kind: "create", uri: uri, options: {overwrite: true}},
		{textDocument: {uri: uri, version: null}, edits: [{range: {start: {line: 0, character: 0}, end: {line: 0, character: 0}}, newText: content}]}
	]}});
}