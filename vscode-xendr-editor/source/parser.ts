import { CharStreams, CommonTokenStream } from "antlr4ts";
import { HTMLLexer } from "./antlr/HTMLLexer";
import { HTMLParser, HtmlElementContext } from "./antlr/HTMLParser";
import { BlockKind, XendrReport, XuleBlock } from "./report";

let report: XendrReport;
let prefixStack: string[][];
let renameStack: Map<string, string>[];

export function parse(htmlCode: string): XendrReport
{
	resetState();

	let rootNode = antlrParse(htmlCode);

	if (rootNode)
	{
		walk(rootNode);
	}

	return report;
}

function resetState()
{
	report = new XendrReport();
	prefixStack = [];
	renameStack = [];
}

function antlrParse(htmlCode: string): HtmlElementContext | undefined
{
	let characters = CharStreams.fromString(htmlCode);
	let lexer = new HTMLLexer(characters);
	let tokens = new CommonTokenStream(lexer);
	let parser = new HTMLParser(tokens);
	let tree = parser.htmlDocument();
	let root = tree?.htmlElements()?.[0]?._element;
	return root;
}

function walk(element: HtmlElementContext)
{
	let prefixes = parseNamespacePrefixes(element);
	prefixStack.push(prefixes);

	let {name, part, renames} = parseAttributes(element);
	renameStack.push(renames);

	extractXuleCode(element, name, part);

	for (let subelement of element._content?._subelements || [])
	{
		walk(subelement);
	}

	renameStack.pop();
	prefixStack.pop();
}

function parseNamespacePrefixes(element: HtmlElementContext): string[]
{
	let prefixes: string[] = [];

	for (let attribute of element._attributes)
	{
		let name = attribute._name.text;
		let value = attribute._value.text;
		if (!name || !value) continue;

		if (name.match(/xmlns(:\w)?/))
		{
			let prefix = name.split(":")[1];

			report.addNamespace(prefix, value.replace(/"/g, ""));

			if (value === `"http://xbrl.us/xendr/2.0/template"`)
			{
				prefixes.push(prefix ? prefix + ":" : "");
			}
		}
	}
	return prefixes;
}

function parseAttributes(element: HtmlElementContext): {name: string|undefined, part: string|undefined, renames: Map<string, string>}
{
	let renames = new Map<string, string>();

	let repeat: string|undefined;
	let repeatWithin: string|undefined;
	let finalName: string|undefined;
	let part: string|undefined;

	for (let attribute of element._attributes)
	{
		let name = attribute._name.text;
		let value = attribute._value.text?.replace(/"/g, "");
		if (!name || !value) continue;

		for (let entry of prefixStack) for (let prefix of entry)
		{
			switch (name)
			{
				case `${prefix}repeat`:
				{
					repeat = value;
				}
				break; case `${prefix}repeatWithin`:
				{
					repeatWithin = value;
				}
				break; case `name`:
				{
					finalName = value;
				}
				break; case `part`:
				{
					part = value;
				}
				break;
			}
		}
	}

	if (repeat && repeatWithin)
	{
		renames.set(repeat, repeatWithin);
	}

	if (finalName)
	{
		for (let i = renameStack.length - 1; i >= 0; i--)
		{
			finalName = renameStack[i].get(finalName) || finalName;
		}
	}

	return {name: finalName, part, renames};
}

function extractXuleCode(element: HtmlElementContext, name: string|undefined, part: string|undefined)
{
	for (let entry of prefixStack) for (let prefix of entry)
	{
		switch (element._name.text)
		{
			case (`${prefix}expression`):
			{
				let block = report.getBlockWithName(name) || report.addBlock(new XuleBlock(BlockKind.SingleExpression, name));

				block.addElement(element);

				if (part)
				{
					block.kind = BlockKind.Parts;
				}
			}
			break; case (`${prefix}global`):
			{
				let block = report.addBlock(new XuleBlock(BlockKind.SingleStatement));
				block.addElement(element);
			}
			break; case (`${prefix}showIf`):
			{
				let block = report.addBlock(new XuleBlock(BlockKind.SingleExpression));
				block.addElement(element);
			}
			break; case (`${prefix}footnoteFacts`):
			{
				report.setFootnotesPresent();
			}
			break; case `${prefix}html`:
			case `${prefix}class`:
			case `${prefix}sign`:
			case `${prefix}format`:
			case `${prefix}scale`:
			case `${prefix}fact`:
			case `${prefix}attribute`:
			case `${prefix}footnote`:
			case `${prefix}startNumber`:
			{
				let block = report.getMostRecentBlock();
				if (block)
				{
					block.addElement(element);

					if (block.kind !== BlockKind.Parts)
					{
						block.kind = BlockKind.ExpressionList;
					}
				}
			}
		}
	}
}
