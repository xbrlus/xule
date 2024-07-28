import { CompletionContext, CompletionItem, CompletionList, DiagnosticChangeEvent, DiagnosticCollection, ExtensionContext, Position, TextDocument, TextDocumentChangeEvent, Uri, commands, languages, workspace } from "vscode";
import { LanguageClient, LanguageClientOptions, ServerOptions, TransportKind } from "vscode-languageclient/node";

let diagnosticCollection: DiagnosticCollection;

export function activate(context: ExtensionContext)
{
	let module = Uri.joinPath(context.extensionUri, "distribution", "server.js").path;
	let transport = TransportKind.ipc;

	let serverOptions: ServerOptions =
	{
		run: { module, transport },
		debug: { module, transport, options: { execArgv: ["--nolazy", "--inspect"] } }
	};

	let clientOptions: LanguageClientOptions =
	{
		documentSelector: [{ scheme: "file", language: "html" }],
		middleware: { provideCompletionItem }
	};

	let client = new LanguageClient("xendr", "XENDR Language Server", serverOptions, clientOptions);

	client.start();

	diagnosticCollection = languages.createDiagnosticCollection("xendrDiagnostics");

	languages.onDidChangeDiagnostics(onDidChangeDiagnostics);

	workspace.onDidChangeTextDocument(onDidChangeDocument);

	context.subscriptions.push(client, diagnosticCollection);
}

async function provideCompletionItem(document: TextDocument, position: Position, context: CompletionContext): Promise<CompletionItem[]>
{
	let xuleUri = Uri.parse(document.uri.toString() + ".xule");

	await waitForModification(xuleUri);

	let completionList = await commands.executeCommand<CompletionList>("vscode.executeCompletionItemProvider", xuleUri, position, context.triggerCharacter);

	return completionList.items;
}

async function waitForModification(uri: Uri, timeout: number = 5000): Promise<void>
{
	return new Promise((resolve, reject) =>
	{
		let watcher = workspace.createFileSystemWatcher(uri.fsPath);
		let timer = setTimeout(onTimeout, timeout);

		watcher.onDidChange(() =>
		{
			watcher.dispose();
			clearTimeout(timer);
			resolve();
		});

		function onTimeout()
		{
			watcher.dispose();
			clearTimeout(timer);
			reject();
		}
	});
}

function onDidChangeDiagnostics(event: DiagnosticChangeEvent)
{
	for (let uri of event.uris)
	{
		let uriString = uri.toString();
		if (uriString.endsWith(".html.xule"))
		{
			let diagnostics = languages.getDiagnostics(uri);

			let htmlUri = Uri.parse(uriString.substring(0, uriString.lastIndexOf(".xule")));
			diagnosticCollection.set(htmlUri, diagnostics);
		}
	}
}

function onDidChangeDocument(event: TextDocumentChangeEvent)
{
	let document = event.document;

	if (document.uri.path.endsWith(".html.xule"))
	{
		document.save();
	}
}